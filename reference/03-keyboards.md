# reference/03 — Клавиатуры (reply / inline)

`keyboard` — поле внутри `data` узлов `message` и `schedule_message`. Не отдельный тип узла.

## Структура

```json
"keyboard": {
  "type": "reply",            // "reply" | "inline"
  "resize_keyboard": true,    // только reply
  "one_time": false,          // только reply
  "buttons": [                // массив РЯДОВ, ряд = массив кнопок
    [ { "text": "Да" }, { "text": "Нет" } ],
    [ { "text": "Назад" } ]
  ]
}
```

## reply — кнопки под полем ввода
- Кнопка: `{ "text": "Текст" }`.
- При нажатии бот получает **текст** кнопки → **regex перехода матчит текст**.
  ```json
  "keyboard": { "type": "reply", "resize_keyboard": true, "one_time": false,
    "buttons": [[{ "text": "Тарифы" }, { "text": "Заявка" }]] },
  "transitions": [
    { "id": "t1", "regex": "/Тарифы/i", "priority": 1, "description": "", "targetNodeId": "plans" },
    { "id": "t2", "regex": "/Заявка/i", "priority": 2, "description": "", "targetNodeId": "lead" },
    { "id": "tf", "regex": ".*", "priority": 100, "description": "", "targetNodeId": "menu" }
  ]
  ```
- `resize_keyboard` (по умолчанию `true`) — ужать клавиатуру. `one_time` — скрыть после нажатия.
- Для коротких известных ответов, меню, квизов.

## inline — кнопки внутри сообщения
- Кнопка: `{ "text": "Текст", "callback_data": "code" }` или ссылка `{ "text": "Сайт", "url": "https://..." }`.
- При нажатии кнопки с `callback_data` бот получает **callback_data** (НЕ текст) →
  **regex перехода матчит callback_data**.
  ```json
  "keyboard": { "type": "inline",
    "buttons": [[{ "text": "Да", "callback_data": "yes" }, { "text": "Нет", "callback_data": "no" }]] },
  "transitions": [
    { "id": "t1", "regex": "/yes/i", "priority": 1, "description": "", "targetNodeId": "ok" },
    { "id": "t2", "regex": "/no/i",  "priority": 2, "description": "", "targetNodeId": "bye" }
  ]
  ```
- Кнопка с `url` (без `callback_data`) просто открывает ссылку и **не шлёт ввод** —
  под неё переход не нужен.
- Поля кнопки inline в редакторе: `text`, `callback_data`, `url`. (`web_app` упомянут в
  спецификации, но в UI-редакторе кнопок не выставляется.)

## Лимиты кнопок по каналам (из движка)

| Канал | Кнопок в ряду | Рядов | Всего |
|---|---|---|---|
| telegram | 8 | ∞ | ∞ |
| whatsapp | 3 | 1 | 3 |
| vk | 10 | 6 | 40 |
| max | 7 | 30 | 210 |

Если бот публикуется в нескольких каналах — ориентируйся на **самый строгий** канал из целевых
(обычно WhatsApp: ≤3 кнопок, 1 ряд). Для Telegram-only можно свободно.

## Правила
- reply: тексты кнопок зеркаль в `regex`; делай fallback-переход на повтор вопроса.
- inline: матчь `callback_data`; держи `callback_data` короткими латинскими кодами (`yes`, `plan_pro`).
- Не маршрутизируй кнопки через `condition`, если можно через `transitions`.
- Избегай двусмысленных похожих текстов кнопок.
