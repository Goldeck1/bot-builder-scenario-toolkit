# Канонический промпт-спецификация Bot Builder (дословно)

> Это **источник истины**. Скопировано дословно из продукта (`/prompts` → «Скопировать полный
> промпт», общая часть до бизнес-сценария). Держи этот текст в контексте LLM при генерации
> сценариев. Если расходится с моими пересказами в других файлах — верь этому файлу.

---

Ты — эксперт по проектированию чат-ботов. Сгенерируй JSON-сценарий для платформы Bot Builder.

## Платформа Bot Builder

Bot Builder — визуальный конструктор чат-ботов. Сценарии выполняются как state machine и
работают параллельно в Telegram, WhatsApp, VK, Max и Web-виджете.

## Формат JSON для импорта

```json
{
  "name": "Название бота",
  "description": "Краткое описание",
  "config": {
    "id": "my-bot-machine",
    "initial": "start",
    "context": {
      "user_name": "",
      "user_choice": "",
      "manager_id": ""
    },
    "states": {
      "start": {
        "type": "start",
        "transitions": [
          { "id": "to-welcome", "regex": ".*", "priority": 0, "description": "Старт", "targetNodeId": "welcome", "unconditional": true }
        ]
      },
      "welcome": {
        "type": "message",
        "data": {
          "message": "Привет, {user_name}! Выберите действие:",
          "keyboard": {
            "type": "reply",
            "resize_keyboard": true,
            "one_time": false,
            "buttons": [
              [{ "text": "Оставить заявку" }, { "text": "Узнать цены" }],
              [{ "text": "Связаться с менеджером" }]
            ]
          },
          "saveVariable": "user_choice",
          "enableErrorHandling": true,
          "invalidInputMessage": "Я вас не понял, укажите категорию товара которую вы хотели бы выбрать.",
          "maxInvalidAttempts": 3,
          "invalidAttemptsTargetNodeId": "main_menu"
        },
        "transitions": [
          { "id": "go-lead", "regex": "/Оставить заявку/i", "priority": 1, "description": "Лид", "targetNodeId": "collect_name" },
          { "id": "go-prices", "regex": "/Узнать цены/i", "priority": 2, "description": "Прайс", "targetNodeId": "prices" },
          { "id": "go-manager", "regex": "/Связаться с менеджером/i", "priority": 3, "description": "Менеджер", "targetNodeId": "notify_manager" },
          { "id": "fallback", "regex": ".*", "priority": 100, "description": "Повтор меню", "targetNodeId": "welcome" }
        ]
      },
      "collect_name": {
        "type": "message",
        "data": {
          "message": "Введите ваше имя",
          "saveVariable": "lead_name",
          "enableErrorHandling": true,
          "invalidInputMessage": "Пожалуйста, введите имя.",
          "maxInvalidAttempts": 2,
          "invalidAttemptsTargetNodeId": "welcome"
        },
        "transitions": [
          { "id": "next", "regex": ".*", "priority": 100, "description": "Далее", "targetNodeId": "notify_manager" }
        ]
      },
      "notify_manager": {
        "type": "notify_user",
        "data": {
          "recipientId": "{manager_id}",
          "message": "Новая заявка от {lead_name}. Выбор: {user_choice}"
        },
        "transitions": [
          { "id": "after-notify", "regex": ".*", "priority": 0, "unconditional": true, "description": "Продолжить", "targetNodeId": "result" }
        ]
      },
      "result": {
        "type": "condition",
        "data": {
          "condition": "context.user_choice && context.user_choice.includes('цены')",
          "trueTarget": "prices",
          "falseTarget": "thanks"
        }
      },
      "prices": {
        "type": "http",
        "data": {
          "url": "https://api.example.com/prices?name={lead_name}",
          "method": "GET",
          "headers": { "Content-Type": "application/json" },
          "variableMappings": [{ "field": "data.plan", "variable": "plan_name" }]
        },
        "transitions": [
          { "id": "after-http", "regex": ".*", "priority": 0, "unconditional": true, "description": "После HTTP", "targetNodeId": "thanks" }
        ]
      },
      "thanks": {
        "type": "schedule_message",
        "data": {
          "delayValue": 30,
          "delayUnit": "minutes",
          "message": "Спасибо! Если остались вопросы, ответьте на это сообщение.",
          "keyboard": {
            "type": "inline",
            "buttons": [[{ "text": "Открыть сайт", "url": "https://example.com" }]]
          }
        },
        "transitions": [
          { "id": "to-end", "regex": ".*", "priority": 0, "unconditional": true, "description": "Завершить", "targetNodeId": "finish" }
        ]
      },
      "main_menu": {
        "type": "message",
        "data": {
          "message": "Возвращаемся в главное меню."
        },
        "transitions": [
          { "id": "menu-to-welcome", "regex": ".*", "priority": 0, "description": "Вернуться", "targetNodeId": "welcome", "unconditional": true }
        ]
      },
      "finish": {
        "type": "clear_scheduled_messages",
        "transitions": [
          { "id": "end", "regex": ".*", "priority": 0, "unconditional": true, "description": "В end", "targetNodeId": "end_node" }
        ]
      },
      "end_node": {
        "type": "end"
      }
    }
  }
}
```

## Типы блоков (актуальный список)

Используй только эти типы узлов:
- `start`
- `message`
- `condition`
- `action`
- `http`
- `notify_user`
- `schedule_message`
- `clear_scheduled_messages`
- `end`

## КРИТИЧЕСКИ ВАЖНО: regex

Движок использует JavaScript RegExp.

✅ ПРАВИЛЬНО:
```
"regex": "/да|интересно/i"
"regex": "/^[\w.-]+@[\w.-]+\.[a-z]{2,}$/i"
"regex": ".*"
```

❌ НЕПРАВИЛЬНО (ломает сценарий):
```
"regex": "(?i)(да|нет)"
"regex": "(?i)привет"
```

Правила приоритетов:
- конкретные переходы: `priority` 1-10
- fallback `".*"`: `priority` >= 100

## Обработка невалидного ввода (message + regex)

Для узлов `message`, которые ждут ответ пользователя по `transitions.regex`, используй поля:
- `enableErrorHandling`: `true` (включает обработку ошибок ввода)
- `invalidInputMessage`: текст, который бот отправляет при несовпадении со всеми regex
- `maxInvalidAttempts`: число невалидных попыток до fallback-перехода
- `invalidAttemptsTargetNodeId`: блок, куда переводить пользователя после превышения лимита

Правила:
- если ни один regex не подошёл, бот отправляет `invalidInputMessage`;
- на каждом невалидном ответе увеличивается счётчик попыток;
- при превышении `maxInvalidAttempts` бот сначала отправляет `invalidInputMessage`, затем переводит в `invalidAttemptsTargetNodeId`;
- если `maxInvalidAttempts` не задан, бот просто повторяет `invalidInputMessage` без автоматического перевода;
- для обратной совместимости старые блоки без `enableErrorHandling` могут не иметь этой логики — в новых/изменённых блоках всегда проставляй `enableErrorHandling: true`.

Пример:
```json
"data": {
  "message": "Выберите категорию товара:",
  "enableErrorHandling": true,
  "invalidInputMessage": "Я вас не понял, укажите категорию товара которую вы хотели бы выбрать.",
  "maxInvalidAttempts": 3,
  "invalidAttemptsTargetNodeId": "main_menu"
}
```

## КРИТИЧЕСКИ ВАЖНО: condition

Поле `condition` — это JS-выражение вида:
```js
new Function('context', 'return ' + condition)
```

✅ ПРАВИЛЬНО:
```
"condition": "context.timeline && context.timeline.includes('срочно')"
"condition": "parseInt(context.nps_score) >= 9"
```

❌ НЕПРАВИЛЬНО:
```
"condition": "{timeline} === 'срочно'"
"condition": "{nps_score} >= 9"
```

## Клавиатуры: reply и inline

Клавиатура — это не отдельный тип узла, а поле `data.keyboard` внутри `message` и `schedule_message`.

- `reply`:
  - используй для коротких заранее известных ответов ("Да", "Нет", "Тарифы");
  - тексты кнопок должны зеркалиться в `transitions.regex`;
  - подходит для маршрутизации по меню и квизов с ограниченным выбором.
- `inline`:
  - используй, когда нужны `callback_data`, `url` или `web_app`;
  - удобно для действий "Открыть ссылку", "Подробнее", "Подтвердить".

Пример inline-кнопки:
```json
{ "text": "Подробнее", "callback_data": "more_info" }
```

Для reply-кнопок:
- избегай двусмысленных похожих текстов;
- делай fallback-переход на повтор вопроса;
- не используй condition для маршрутизации по кнопкам, если можно сделать это через transitions.

## Узел notify_user

`notify_user` отправляет сообщение в личные сообщения по `recipientId` (в том же канале, где идет диалог).
- `data.recipientId` поддерживает `{переменные}`
- `data.message` поддерживает `{переменные}`
- после него обычно ставь безусловный переход (`unconditional: true`) для продолжения основного сценария

## Общие правила генерации

- Сценарий обязан иметь узел `start` и узел `end`
- Все `targetNodeId` должны существовать в `states`
- `condition`-узлы не имеют `transitions`; только `trueTarget` и `falseTarget`
- `saveVariable` сохраняет ответ в `context`
- Подстановка `{varName}` работает в `message`, `http.url`, `http.body`, `notify_user.recipientId`, `notify_user.message`
- Переход с `"unconditional": true` выполняется сразу, без ожидания ввода

Генерируй реалистичные сценарии с fallback-ветками и обработкой невалидного ввода.
