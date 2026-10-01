# reference/06 — Жёсткие правила (то, что проверяет валидатор)

Эти правила закодированы в [`../validators/validate_scenario.py`](../validators/validate_scenario.py).
ERROR = сценарий сломается при импорте/исполнении. WARN = почти наверняка логическая ошибка.

## ERRORS (блокеры)

| # | Правило |
|---|---|
| E1 | Корень — объект с непустым `name` и объектом `config`. |
| E2 | `config.states` — непустой объект. |
| E3 | `config.initial` присутствует и ссылается на существующий узел. |
| E4 | Есть ≥1 узел `start` и ≥1 узел `end`. |
| E5 | `type` каждого узла ∈ {start, message, condition, action, http, notify_user, schedule_message, clear_scheduled_messages, end}. |
| E6 | `condition` НЕ имеет `transitions`; имеет `condition`, `trueTarget`, `falseTarget`. |
| E7 | В `condition.condition` нет `{var}` (только `context.*`). |
| E8 | Все ссылки на узлы существуют: `targetNodeId`, `trueTarget`, `falseTarget`, `invalidAttemptsTargetNodeId`. |
| E9 | Неконечные/неусловные узлы имеют непустой массив `transitions`. |
| E10 | В каждом переходе `regex` — строка; нет инлайн-флагов `(?i)`/`(?m)`/`(?s)`. |
| E11 | В каждом переходе `priority` — число. |
| E12 | `http.variableMappings[*]` — объекты `{field, variable}`. |

## WARNINGS (проверь логику)

| # | Правило |
|---|---|
| W1 | `config.initial` указывает на узел не типа `start`. |
| W2 | Служебный узел (http/notify_user/action/schedule_message/clear_scheduled_messages) не имеет `unconditional`-перехода → риск зависания. |
| W3 | Узел `message` с переходами без `enableErrorHandling: true`. |
| W4 | Универсальный `.*`/пустой regex с `priority < 100` рядом с конкретными переходами → перехватит их. |
| W5 | Повтор `priority` в нескольких переходах одного узла → неоднозначный порядок. |
| W6 | Использована `{var}` или `context.var`, которая нигде не объявлена/не сохраняется (исключая встроенные). |
| W7 | `http` без `url` / необычный `method`; `schedule_message.delayUnit` не из {minutes,hours,days}; `action` без массива `variables`; пустой `notify_user.recipientId`. |

## Запуск

```bash
python3 validators/validate_scenario.py scenario.json     # файл
cat scenario.json | python3 validators/validate_scenario.py -   # из stdin
```
Коды возврата: `0` — нет ERROR; `1` — есть ERROR; `2` — не прочитан/невалидный JSON.

**Контракт генерации: сценарий выдаётся только при 0 ERROR.** WARNINGS — просмотреть и
осознанно оставить или поправить.
