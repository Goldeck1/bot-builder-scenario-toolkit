# reference/02 — Типы узлов (выверено по движку)

Поля `data` ниже извлечены из кода приложения (сборка/десериализация узлов), а не только из
промпт-спеки. UI-лейбл — название типа в выпадающем списке «Тип узла».

| `type` | UI-лейбл |
|---|---|
| start | Начало |
| message | Сообщение |
| condition | Условие |
| action | Действие |
| http | HTTP запрос |
| notify_user | Уведомление в ЛС |
| schedule_message | Отложенное сообщение |
| clear_scheduled_messages | Очистить очередь |
| end | Конец |

---

## start
Точка входа. Без `data`. Обычно один `unconditional`-переход.
```json
"start": { "type": "start",
  "transitions": [ { "id": "t0", "regex": ".*", "priority": 0, "unconditional": true, "description": "Старт", "targetNodeId": "welcome" } ] }
```

## message
`data`:
| Поле | Тип | Примечание |
|---|---|---|
| `message` | string | Текст. Поддерживает `{var}`. Может быть пустым, если есть `media`. |
| `media` | object/ref | Вложение (картинка/файл). Опционально. |
| `keyboard` | object | reply/inline — см. [03-keyboards](03-keyboards.md). |
| `saveVariable` | string | Имя переменной в `context`, куда писать ответ пользователя. |
| `trackResponseInStats` | bool | `true` = собирать ответы в Аналитику (тумблер «В статистике»). |
| `enableErrorHandling` | bool | Включает обработку невалидного ввода (ставь `true`). |
| `invalidInputMessage` | string | Текст при несовпадении со всеми regex. |
| `maxInvalidAttempts` | number | Попыток до увода в fallback. |
| `invalidAttemptsTargetNodeId` | string | Узел увода после лимита. |

`transitions` — regex-ветвление по ответу пользователя.

## condition
**Без `transitions`.** `data`:
| Поле | Тип | Примечание |
|---|---|---|
| `condition` | string | JS-выражение: `new Function('context','return '+condition)`. Только `context.*`. |
| `trueTarget` | string | Узел при `true`. |
| `falseTarget` | string | Узел при `false`. |
```json
"branch": { "type": "condition",
  "data": { "condition": "context.nps && parseInt(context.nps) >= 9", "trueTarget": "promoter", "falseTarget": "rest" } }
```

## action
Записывает переменные в `context`. `data`:
| Поле | Тип | Примечание |
|---|---|---|
| `variables` | array | Массив `{ "name": "...", "value": "..." }`. |
```json
"set": { "type": "action",
  "data": { "variables": [ { "name": "score", "value": "10" }, { "name": "stage", "value": "qualified" } ] },
  "transitions": [ { "id": "t", "regex": ".*", "priority": 0, "unconditional": true, "description": "Записали", "targetNodeId": "next" } ] }
```

## http
`data`:
| Поле | Тип | Примечание |
|---|---|---|
| `url` | string | Поддерживает `{var}`. |
| `method` | string | GET/POST/PUT/PATCH/DELETE (по умолчанию GET). |
| `headers` | object | Опц. |
| `queryParams` | object | Опц. |
| `body` | string | Опц., для POST/PUT. Поддерживает `{var}`. |
| `timeout` | number | мс, по умолчанию `30000`. |
| `auth` | object | `{ "type": "none"\|"basic"\|"bearer", "username","password","token" }`. |
| `variableMappings` | array | `[{ "field": "data.user.name", "variable": "user_name" }]` — путь в JSON-ответе → переменная. |
```json
"call": { "type": "http",
  "data": {
    "url": "https://api.example.com/u?id={userId}", "method": "GET",
    "headers": { "Content-Type": "application/json" },
    "timeout": 30000, "auth": { "type": "none" },
    "variableMappings": [ { "field": "data.plan", "variable": "plan_name" } ]
  },
  "transitions": [ { "id": "t", "regex": ".*", "priority": 0, "unconditional": true, "description": "После HTTP", "targetNodeId": "next" } ] }
```

## notify_user
Сообщение в ЛС по `recipientId` (в том же канале). `data`:
| Поле | Тип | Примечание |
|---|---|---|
| `recipientId` | string | ID получателя. Поддерживает `{var}` (напр. `{manager_id}`, `{userId}`). |
| `message` | string | Текст. Поддерживает `{var}`. |
```json
"notify": { "type": "notify_user",
  "data": { "recipientId": "{manager_id}", "message": "Заявка от {lead_name}, тел: {phone}" },
  "transitions": [ { "id": "t", "regex": ".*", "priority": 0, "unconditional": true, "description": "Дальше", "targetNodeId": "thanks" } ] }
```

## schedule_message
Отложенная отправка после попадания в узел. `data`:
| Поле | Тип | Примечание |
|---|---|---|
| `delayValue` | number | Величина задержки (по умолчанию 1). |
| `delayUnit` | string | `minutes` \| `hours` \| `days`. |
| `message` | string | Текст. Поддерживает `{var}`. |
| `media` | object/ref | Опц. |
| `keyboard` | object | Опц. (reply/inline). |
```json
"remind": { "type": "schedule_message",
  "data": { "delayValue": 2, "delayUnit": "hours", "message": "Напоминаем, {user_name}!",
            "keyboard": { "type": "inline", "buttons": [[{ "text": "Открыть", "url": "https://example.com" }]] } },
  "transitions": [ { "id": "t", "regex": ".*", "priority": 0, "unconditional": true, "description": "Дальше", "targetNodeId": "next" } ] }
```
> Сейчас отложка работает по задержке (delay), не по конкретной дате. Чтобы не копить дубли
> напоминаний — перед новым ставь `clear_scheduled_messages`.

## clear_scheduled_messages
Чистит очередь отложенных сообщений пользователя. Без `data`.
```json
"clean": { "type": "clear_scheduled_messages",
  "transitions": [ { "id": "t", "regex": ".*", "priority": 0, "unconditional": true, "description": "В конец", "targetNodeId": "end" } ] }
```

## end
Конец ветки. Без `data`, без `transitions`.
```json
"end": { "type": "end" }
```
Поведение после `end` зависит от настройки **Цикличности** бота (тумблер в списке «Боты»,
поле API `is_cyclic`) — НЕ часть JSON-сценария.
