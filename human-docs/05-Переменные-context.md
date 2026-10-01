# 05 — Переменные и context

## Где живут переменные

Все переменные диалога лежат в `context` — объекте состояния конкретной сессии пользователя.
Объявляй их заранее в `config.context` (пустыми значениями), включая служебные:

```json
"context": {
  "user_name": "",
  "lead_name": "",
  "user_choice": "",
  "manager_id": "123456789"
}
```

## Два синтаксиса — не путать

| Где | Синтаксис | Пример |
|---|---|---|
| В тексте/полях (подстановка значения) | `{varName}` | `"Привет, {user_name}!"` |
| В условиях `condition` (JS-выражение) | `context.varName` | `"parseInt(context.nps_score) >= 9"` |

> В правой панели редактора подсказано то же: начальные переменные доступны как `{varName}`
> в сообщениях и как `context.variables.varName` в условиях. На практике в спецификации
> генерации условия пишут короче — `context.varName`. Следуй примерам из
> [canonical/platform-spec.md](canonical/platform-spec.md).

### Подстановка `{varName}` работает в:
- `message.data.message`
- `http.data.url`
- `http.data.body`
- `notify_user.data.recipientId`
- `notify_user.data.message`
- (а также в `schedule_message.data.message`)

Если переменной нет/пустая — подставляется пустая строка.

## Как переменные заполняются

1. **`saveVariable`** в узле `message` — сохраняет ответ пользователя.
   ```json
   "collect_name": {
     "type": "message",
     "data": { "message": "Введите ваше имя", "saveVariable": "lead_name",
               "enableErrorHandling": true, "invalidInputMessage": "Введите имя.",
               "maxInvalidAttempts": 2, "invalidAttemptsTargetNodeId": "welcome" },
     "transitions": [ { "id": "next", "regex": ".*", "priority": 100,
                        "description": "Далее", "targetNodeId": "notify_manager" } ]
   }
   ```
2. **`action`** — записать значение в переменную программно (редко).
3. **`http` + `variableMappings`** — из JSON-ответа внешнего API:
   `[{ "field": "data.plan", "variable": "plan_name" }]`.
4. **Начальные** — заданы в `config.context` с самого старта.

## Встроенные переменные

В редакторе есть блок «Встроенные переменные» — служебные значения, доступные в любом
сценарии без объявления (например, имя пользователя из мессенджера). Если нужно имя
пользователя — используй встроенную переменную, не пытайся собирать её вручную.

## Условия (`condition`)

`condition` исполняется как `new Function('context', 'return ' + condition)`, поэтому это
полноценное JS-выражение над объектом `context`:

```js
context.timeline && context.timeline.includes('срочно')
parseInt(context.nps_score) >= 9
context.experience && (context.experience.includes('3') || context.experience.includes('5'))
```

Частые приёмы:
- строковое сравнение: `context.x && context.x.includes('...')`
- числовое: `parseInt(context.x) >= N` (значения из ответов — строки, приводи `parseInt`)
- защита от undefined: всегда проверяй `context.x &&` перед `.includes(...)`.

❌ Никогда не используй `{varName}` внутри `condition`.
