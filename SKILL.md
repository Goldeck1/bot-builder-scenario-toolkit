---
name: bot-builder-scenario-generation
description: Генерация валидных JSON-сценариев для совместимой платформы Bot Builder. Использовать, когда нужно создать или изменить сценарий бота для импорта в продукт.
---

# SKILL — Генерация сценариев Bot Builder

> Машинный вход. Это сжатый, авторитетный свод правил для безошибочной генерации
> JSON-сценариев. Все поля **выверены по коду движка** (не только по промпт-спеке).
> Источник истины при конфликте — [`canonical/platform-spec.md`](canonical/platform-spec.md).
> **Перед выдачей любого сценария прогоняй [`validators/validate_scenario.py`](validators/validate_scenario.py) — 0 ERROR обязательно.**

## Что генерируем

Сценарий чат-бота как **машина состояний**, импортируемый в Bot Builder (Telegram, WhatsApp,
VK, Max, Web). Вывод — **только валидный JSON**, без markdown-обёртки и пояснений, если
пользователь не попросил иначе.

## Скелет (всегда такой)

```json
{
  "name": "string",
  "description": "string",
  "config": {
    "id": "kebab-machine-id",
    "initial": "start",
    "context": { "var1": "", "var2": "" },
    "states": { "start": { "...": "" }, "end": { "type": "end" } }
  }
}
```

- `config.states` — словарь: **ключ = id узла**, значение = узел.
- Узел: `{ "type": <тип>, "data": {...}, "transitions": [...] }`.
- Позиции узлов (x/y) НЕ нужны — раскладка авто. Цикличность НЕ в JSON (это настройка бота).

## 9 типов узлов (только эти)

| type | Назначение | Ключевые `data` | transitions |
|---|---|---|---|
| `start` | вход | — | да, обычно 1 шт `unconditional` |
| `message` | текст/вопрос/меню | `message, media?, keyboard?, saveVariable?, trackResponseInStats?, enableErrorHandling, invalidInputMessage, maxInvalidAttempts, invalidAttemptsTargetNodeId` | да (regex-ветвление) |
| `condition` | ветвление по JS | `condition, trueTarget, falseTarget` | **НЕТ** |
| `action` | записать переменные | `variables: [{name, value}]` | да, `unconditional` |
| `http` | внешний запрос | `url, method, headers?, queryParams?, body?, timeout?, auth?, variableMappings:[{field,variable}]` | да, `unconditional` |
| `notify_user` | сообщение в ЛС | `recipientId, message` | да, `unconditional` |
| `schedule_message` | отложенное сообщение | `delayValue, delayUnit(minutes\|hours\|days), message, media?, keyboard?` | да, `unconditional` |
| `clear_scheduled_messages` | очистить очередь отложенных | — | да, `unconditional` |
| `end` | конец ветки | — | нет |

Полные поля и примеры — [`reference/02-node-types.md`](reference/02-node-types.md).

## Переход (transition)

```json
{ "id": "uuid", "regex": "/Да/i", "priority": 1, "description": "Подпись", "targetNodeId": "node_id", "unconditional": false }
```
- Проверяются по возрастанию `priority` (меньше = выше). Берётся первый совпавший regex.
- Конкретные переходы: `priority` 1–10. Fallback `".*"`: `priority >= 100`.
- `unconditional: true` → выполняется сразу, без ожидания ввода (служебные узлы и цепочки сообщений).

## ЖЁСТКИЕ ПРАВИЛА (нарушение = поломка)

1. Обязательны узлы `start` и `end`. `config.initial` = id стартового узла (`"start"`).
2. Все ссылки на узлы существуют в `states`: `targetNodeId`, `trueTarget`, `falseTarget`,
   `invalidAttemptsTargetNodeId`.
3. `condition` **без `transitions`** — только `trueTarget`/`falseTarget` в `data`.
4. `regex` — JavaScript RegExp: `"/паттерн/i"` или `".*"`. **Запрещены инлайн-флаги `(?i)`**.
5. В `condition` — только `context.var` (JS). **`{var}` в condition запрещён.**
6. Подстановка `{var}` работает в: `message.message`, `schedule_message.message`,
   `http.url`, `http.body`, `notify_user.recipientId`, `notify_user.message`.
7. Все используемые переменные объявлены в `config.context` (или приходят из `saveVariable`/
   `action`/`http.variableMappings`/встроенных).
8. После служебных узлов (`http`, `notify_user`, `action`, `schedule_message`,
   `clear_scheduled_messages`) — переход с `"unconditional": true`.
9. На узлах `message`, которые ждут ответ: `enableErrorHandling: true` + `invalidInputMessage`
   (+ `maxInvalidAttempts` + `invalidAttemptsTargetNodeId` для увода в fallback).
   ⚠️ **Проверено вживую:** `invalidInputMessage` срабатывает ТОЛЬКО если ни один regex не
   совпал. Если у узла есть catch-all переход `".*"` (priority ≥ 100) — он перехватит любой
   ввод раньше, и `invalidInputMessage` не покажется. Выбирай ОДНУ стратегию на узел:
   либо fallback `.*`→повтор/меню, либо `invalidInputMessage` без `.*`-перехода.

## КНОПКИ — критичный нюанс роутинга

`keyboard` — поле внутри `message`/`schedule_message`, не отдельный узел.
- **`reply`** (кнопки под полем ввода): при нажатии отправляется **текст** кнопки →
  `regex` перехода должен матчить **текст** (`{ "text": "Да" }`).
- **`inline`** (кнопки в сообщении): при нажатии отправляется **`callback_data`** →
  `regex` перехода должен матчить **callback_data**, НЕ текст (`{ "text": "Да", "callback_data": "yes" }`).
  Кнопка-ссылка: `{ "text": "Сайт", "url": "https://..." }` (не шлёт ввод, просто открывает).

Лимиты кнопок по каналам и подробности — [`reference/03-keyboards.md`](reference/03-keyboards.md).

## Переменные / context

- `{var}` — подстановка значения в текстах/URL.
- `context.var` — в условиях (flat-ключи `config.context` и `saveVariable` пишут сюда).
- `context.variables.var` — начальные переменные, заданные через объект `config.context.variables`.
- `context.lastUserInput` — текст последнего сообщения пользователя.
- Встроенные (без объявления): `{userId} {username} {user_name} {messengerType} {recipient} {lastUserInput}`.
  Для `notify_user.recipientId` менеджера используй переменную (напр. `{manager_id}` из context),
  для ответа текущему пользователю — `{userId}`/`{recipient}`.

Подробно — [`reference/04-variables.md`](reference/04-variables.md).

## Анти-паттерны (никогда так)

- ❌ `"regex": "(?i)да"` → ✅ `"/да/i"`
- ❌ `"condition": "{score} >= 9"` → ✅ `"parseInt(context.score) >= 9"`
- ❌ `condition` с массивом `transitions` → ✅ только `trueTarget`/`falseTarget`
- ❌ inline-кнопка с регексом по тексту → ✅ regex по `callback_data`
- ❌ fallback `".*"` с `priority: 1` рядом с конкретными → ✅ `priority >= 100`
- ❌ `http`/`notify_user` без `unconditional` перехода → бот зависнет в ожидании ввода
- ❌ узел типа, которого нет в списке 9 → импорт сломается
- ❌ ссылка `targetNodeId` на несуществующий id

## Рабочий процесс генерации

1. Спроектируй граф: start → … → end (с fallback-ветками и обработкой невалидного ввода).
2. Объяви все переменные в `config.context`.
3. Сгенерируй JSON по правилам выше.
4. **Прогони валидатор:** `python3 validators/validate_scenario.py scenario.json` → добейся 0 ERROR.
5. Отдай JSON. (Импорт в продукт: «Боты → Импорт» или «Редактор → JSON редактор → вставить → Сохранить».)

## Чек-лист перед выдачей

- [ ] `start` и `end` присутствуют, `config.initial` корректен
- [ ] все ссылки на узлы существуют
- [ ] `condition` без `transitions`, условие на `context.var`
- [ ] regex в форме `/.../i`, без `(?i)`; fallback `.*` имеет `priority >= 100`
- [ ] служебные узлы продолжаются `unconditional: true`
- [ ] inline-кнопки матчатся по `callback_data`, reply — по тексту
- [ ] все `{var}` и `context.var` объявлены
- [ ] message-вопросы имеют обработку невалидного ввода
- [ ] **валидатор: 0 ERROR**
