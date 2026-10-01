#!/usr/bin/env python3
"""
validate_scenario.py — пред-полётный валидатор сценариев Bot Builder.

Назначение: проверить сгенерированный JSON-сценарий ПЕРЕД импортом в продукт,
чтобы он гарантированно не сломался. Кодирует жёсткие правила движка
(см. reference/06-hard-rules.md), выверенные по реальному коду приложения.

Использование:
    python3 validate_scenario.py scenario.json
    cat scenario.json | python3 validate_scenario.py -
    python3 validate_scenario.py a.json b.json     # несколько файлов

Коды возврата: 0 — ошибок нет; 1 — есть ERROR; 2 — не удалось прочитать/распарсить.
Предупреждения (WARN) не влияют на код возврата, но их стоит просмотреть.
"""
import json
import re
import sys

ALLOWED_TYPES = {
    "start", "message", "condition", "action", "http",
    "notify_user", "schedule_message", "clear_scheduled_messages", "end",
}
# Узлы, которые НЕ ждут ввод и должны вести дальше безусловным переходом.
SERVICE_TYPES = {"action", "http", "notify_user", "schedule_message", "clear_scheduled_messages"}
BUILTIN_VARS = {"userId", "username", "userHandle", "firstName", "lastName",
                "user_name", "messengerType", "recipient", "lastUserInput"}
DELAY_UNITS = {"minutes", "hours", "days"}
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


class Report:
    def __init__(self):
        self.errors = []
        self.warns = []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warns.append(msg)


def collect_declared_vars(cfg):
    declared = set(BUILTIN_VARS)
    ctx = cfg.get("context", {})
    if isinstance(ctx, dict):
        for k, v in ctx.items():
            if k == "variables" and isinstance(v, dict):
                declared.update(v.keys())          # context.variables.X
            else:
                declared.add(k)                     # context.X (flat)
    states = cfg.get("states", {})
    if isinstance(states, dict):
        for node in states.values():
            if not isinstance(node, dict):
                continue
            data = node.get("data") or {}
            if not isinstance(data, dict):
                continue
            if isinstance(data.get("saveVariable"), str) and data["saveVariable"].strip():
                declared.add(data["saveVariable"].strip())
            if node.get("type") == "action":
                for it in data.get("variables", []) or []:
                    if isinstance(it, dict) and isinstance(it.get("name"), str) and it["name"].strip():
                        declared.add(it["name"].strip())
            if node.get("type") == "http":
                for mp in data.get("variableMappings", []) or []:
                    if isinstance(mp, dict) and isinstance(mp.get("variable"), str) and mp["variable"].strip():
                        declared.add(mp["variable"].strip())
    return declared


PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][\w.]*)\}")
CTX_RE = re.compile(r"context\.(?:variables\.)?([a-zA-Z_]\w*)")


def used_placeholders(text):
    return set(m.group(1).split(".")[0] for m in PLACEHOLDER_RE.finditer(text or ""))


def validate(scenario, rep: Report):
    if not isinstance(scenario, dict):
        rep.err("Корень должен быть JSON-объектом.")
        return
    if not isinstance(scenario.get("name"), str) or not scenario["name"].strip():
        rep.err("Отсутствует непустое строковое поле 'name'.")
    cfg = scenario.get("config")
    if not isinstance(cfg, dict):
        rep.err("Отсутствует объект 'config'.")
        return
    if "context" in cfg and not isinstance(cfg["context"], dict):
        rep.err("'config.context' должен быть объектом.")
    states = cfg.get("states")
    if not isinstance(states, dict) or not states:
        rep.err("'config.states' должен быть непустым объектом.")
        return

    initial = cfg.get("initial")
    if not isinstance(initial, str) or not initial:
        rep.err("Отсутствует строковое поле 'config.initial'.")
    elif initial not in states:
        rep.err(f"config.initial='{initial}' не существует в states.")
    elif (states[initial] or {}).get("type") != "start":
        rep.warn(f"Узел config.initial='{initial}' имеет тип "
                 f"'{(states[initial] or {}).get('type')}', ожидался 'start'.")

    # наличие start и end
    types_present = [(states[k] or {}).get("type") for k in states]
    if "start" not in types_present:
        rep.err("Нет ни одного узла типа 'start'.")
    if "end" not in types_present:
        rep.err("Нет ни одного узла типа 'end'.")

    declared = collect_declared_vars(cfg)

    def check_ref(target, where):
        if not isinstance(target, str) or not target.strip():
            rep.err(f"{where}: пустая/нестроковая ссылка на узел.")
        elif target not in states:
            rep.err(f"{where}: ссылка на несуществующий узел '{target}'.")

    for nid, node in states.items():
        w = f"Узел '{nid}'"
        if not isinstance(node, dict):
            rep.err(f"{w}: должен быть объектом.")
            continue
        ntype = node.get("type")
        if ntype not in ALLOWED_TYPES:
            rep.err(f"{w}: недопустимый тип '{ntype}'. Разрешены: {sorted(ALLOWED_TYPES)}.")
            continue
        data = node.get("data") or {}
        transitions = node.get("transitions")

        # --- condition ---
        if ntype == "condition":
            if "transitions" in node:
                rep.err(f"{w} (condition): не должен иметь 'transitions'. Используй trueTarget/falseTarget.")
            cond = data.get("condition")
            if not isinstance(cond, str) or not cond.strip():
                rep.err(f"{w} (condition): пустое поле data.condition.")
            else:
                if PLACEHOLDER_RE.search(cond):
                    rep.err(f"{w} (condition): в condition нельзя использовать {{var}}; пиши context.var.")
                for v in CTX_RE.findall(cond):
                    if v not in declared:
                        rep.warn(f"{w} (condition): переменная context.{v} нигде не объявлена/не сохраняется.")
            check_ref(data.get("trueTarget"), f"{w}.data.trueTarget")
            check_ref(data.get("falseTarget"), f"{w}.data.falseTarget")
            continue

        # --- end ---
        if ntype == "end":
            if node.get("transitions"):
                rep.warn(f"{w} (end): обычно не имеет переходов.")
            continue

        # --- остальные типы: проверка переходов ---
        if not isinstance(transitions, list) or not transitions:
            rep.err(f"{w} ({ntype}): отсутствует непустой массив 'transitions'.")
            transitions = []

        seen_prio = {}
        has_uncond = False
        for i, t in enumerate(transitions):
            tw = f"{w} переход[{i}]"
            if not isinstance(t, dict):
                rep.err(f"{tw}: должен быть объектом.")
                continue
            if not t.get("id"):
                rep.warn(f"{tw}: отсутствует 'id'.")
            rx = t.get("regex")
            if not isinstance(rx, str):
                rep.err(f"{tw}: 'regex' должен быть строкой.")
                rx = ""
            if "(?i)" in rx or "(?s)" in rx or "(?m)" in rx:
                rep.err(f"{tw}: инлайновые флаги вида (?i) ломают сценарий. Используй форму /паттерн/i.")
            prio = t.get("priority")
            if not isinstance(prio, (int, float)):
                rep.err(f"{tw}: 'priority' должен быть числом.")
            else:
                seen_prio.setdefault(prio, 0)
                seen_prio[prio] += 1
            if t.get("unconditional") is True:
                has_uncond = True
            # fallback с низким приоритетом
            if rx in (".*", "/.*/", "") and isinstance(prio, (int, float)) and prio < 100 \
                    and len(transitions) > 1 and not t.get("unconditional"):
                rep.warn(f"{tw}: универсальный regex '{rx}' с priority={prio} (<100) перехватит "
                         f"конкретные переходы. Для fallback ставь priority >= 100.")
            check_ref(t.get("targetNodeId"), f"{tw}.targetNodeId")

        for p, c in seen_prio.items():
            if c > 1:
                rep.warn(f"{w}: приоритет {p} повторяется в {c} переходах (неоднозначный порядок).")

        if ntype in SERVICE_TYPES and transitions and not has_uncond:
            rep.warn(f"{w} ({ntype}): служебный узел обычно продолжается безусловным переходом "
                     f"(\"unconditional\": true), иначе сценарий зависнет в ожидании ввода.")

        # --- проверки полей по типам ---
        if ntype == "http":
            if data.get("method") and data["method"] not in HTTP_METHODS:
                rep.warn(f"{w} (http): необычный метод '{data.get('method')}'.")
            if not data.get("url"):
                rep.warn(f"{w} (http): пустой data.url.")
            for mp in data.get("variableMappings", []) or []:
                if not isinstance(mp, dict) or "field" not in mp or "variable" not in mp:
                    rep.err(f"{w} (http): элемент variableMappings должен быть {{field, variable}}.")
        if ntype == "notify_user":
            if not data.get("recipientId"):
                rep.warn(f"{w} (notify_user): пустой data.recipientId.")
        if ntype == "schedule_message":
            if data.get("delayUnit") and data["delayUnit"] not in DELAY_UNITS:
                rep.warn(f"{w} (schedule_message): delayUnit='{data.get('delayUnit')}', "
                         f"ожидалось одно из {sorted(DELAY_UNITS)}.")
        if ntype == "action":
            if not isinstance(data.get("variables"), list):
                rep.warn(f"{w} (action): ожидается data.variables = массив {{name, value}}.")
        if ntype == "message":
            tgt = data.get("invalidAttemptsTargetNodeId")
            if isinstance(tgt, str) and tgt.strip():
                check_ref(tgt, f"{w}.data.invalidAttemptsTargetNodeId")
            waits_for_input = any(not t.get("unconditional") for t in transitions if isinstance(t, dict))
            if waits_for_input and not data.get("enableErrorHandling"):
                rep.warn(f"{w} (message): рекомендуется enableErrorHandling: true + обработка невалидного ввода.")

        # --- подстановки {var} в текстовых полях ---
        for field in ("message",):
            val = data.get(field)
            if isinstance(val, str):
                for v in used_placeholders(val):
                    if v not in declared:
                        rep.warn(f"{w}: в '{field}' используется {{{v}}}, но переменная нигде не объявлена.")
        if ntype == "notify_user":
            for field in ("recipientId", "message"):
                for v in used_placeholders(data.get(field, "")):
                    if v not in declared:
                        rep.warn(f"{w}: в notify_user.{field} используется {{{v}}}, переменная не объявлена.")
        if ntype == "http":
            for field in ("url", "body"):
                fv = data.get(field)
                if isinstance(fv, str):
                    for v in used_placeholders(fv):
                        if v not in declared:
                            rep.warn(f"{w}: в http.{field} используется {{{v}}}, переменная не объявлена.")


def run_one(path):
    rep = Report()
    try:
        raw = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    except OSError as e:
        print(f"[{path}] НЕ ПРОЧИТАН: {e}")
        return 2
    try:
        scenario = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[{path}] НЕВАЛИДНЫЙ JSON: {e}")
        return 2
    validate(scenario, rep)
    label = scenario.get("name", path) if isinstance(scenario, dict) else path
    print(f"\n=== {path}  ({label}) ===")
    if rep.errors:
        print(f"  ERRORS ({len(rep.errors)}):")
        for m in rep.errors:
            print("   ✗ " + m)
    if rep.warns:
        print(f"  WARNINGS ({len(rep.warns)}):")
        for m in rep.warns:
            print("   ! " + m)
    if not rep.errors and not rep.warns:
        print("  ✓ Идеально: ошибок и предупреждений нет.")
    elif not rep.errors:
        print("  ✓ Валиден (только предупреждения).")
    return 1 if rep.errors else 0


def main(argv):
    paths = argv[1:] or ["-"]
    rc = 0
    for p in paths:
        rc = max(rc, run_one(p))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
