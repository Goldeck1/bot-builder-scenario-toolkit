# reference/04 — Переменные и context (выверено)

## Два синтаксиса

| Где | Форма | Пример |
|---|---|---|
| Тексты, URL, body, recipientId (подстановка значения) | `{var}` | `"Привет, {user_name}!"` |
| Условия `condition` (JS над context) | `context.var` | `"parseInt(context.score) >= 9"` |

`{var}` работает в: `message.message`, `schedule_message.message`, `http.url`, `http.body`,
`notify_user.recipientId`, `notify_user.message`. Нет значения → подставляется пустая строка.

## Где живут переменные (namespace)

- **`context.var`** — flat-ключи. Сюда пишет `saveVariable`, `action`, `http.variableMappings`,
  и сюда кладутся flat-ключи из `config.context`. Это основной namespace для условий.
- **`context.variables.var`** — «Начальные переменные», если заданы как объект
  `config.context.variables = { "userName": "Иван" }`. В условиях: `context.variables.userName`.
- **`context.lastUserInput`** — текст последнего сообщения пользователя (для условий вида
  `context.lastUserInput.includes('да')`).

> Рекомендация для генерации: используй **flat-подход** — объявляй переменные плоско в
> `config.context` и обращайся как `context.var` (так в эталонной спеке платформы). Namespace
> `context.variables.*` применяй только если осознанно кладёшь объект `variables` в context.

## Объявление

Объявляй ВСЕ используемые переменные в `config.context` (пустыми строками):
```json
"context": { "lead_name": "", "phone": "", "user_choice": "", "manager_id": "123456789" }
```

## Как заполняются

1. `saveVariable` в `message` — сохраняет ответ пользователя в `context.<saveVariable>`.
2. `action.data.variables: [{name, value}]` — присваивание констант/значений.
3. `http.data.variableMappings: [{field, variable}]` — из JSON-ответа API (`field` — путь, напр. `data.user.name`).
4. Начальные значения — прямо в `config.context`.

## Встроенные переменные (доступны без объявления)

| Переменная | Значение |
|---|---|
| `{username}` | Отображаемое имя для обращения (имя и фамилия из профиля мессенджера) |
| `{userHandle}` | @ник пользователя (Telegram и др.), если доступен |
| `{firstName}` | Имя из профиля мессенджера |
| `{lastName}` | Фамилия из профиля мессенджера |
| `{userId}` | ID пользователя в канале (chat id, phone, vk id и т.д.) |
| `{messengerType}` | Канал диалога: `telegram`, `whatsapp`, `vk`, `max`, `web` |
| `{recipient}` | ID получателя для отправки сообщений в текущем канале |
| `{lastUserInput}` | Текст последнего сообщения пользователя |
| `{user_name}` | Алиас username; если задана явно в начальных переменных — берётся она |

> Полный список (9 шт.) выверен по коду движка. В Предпросмотре `{username}` пустой (нет реального
> профиля мессенджера) — в реальном Telegram подставляется. `{messengerType}` в Предпросмотре = `web`.

Применение:
- `notify_user.recipientId`: для менеджера — переменная из context (напр. `{manager_id}`);
  чтобы написать самому пользователю — `{userId}` или `{recipient}`.
- В тексты можно вставлять `{username}`, `{user_name}`, `{lastUserInput}`.

## Условия (`condition`) — приёмы

```js
context.choice && context.choice.includes('цены')          // строка содержит
parseInt(context.nps) >= 9                                  // число (ответы — строки!)
context.lastUserInput.includes('да')                        // по последнему сообщению
context.variables.userName === 'Иван'                       // начальная переменная
context.exp && (context.exp.includes('3') || context.exp.includes('5'))
```
Всегда защищай от `undefined`: `context.x && context.x.includes(...)`.
**Никогда** `{var}` внутри `condition`.
