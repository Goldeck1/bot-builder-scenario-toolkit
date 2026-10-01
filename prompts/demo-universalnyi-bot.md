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
    "context": { "user_choice": "", "lead_name": "", "phone": "", "age": "", "manager_id": "" },
    "states": {
      "start": {
        "type": "start",
        "transitions": [
          { "id": "to-welcome", "regex": ".*", "priority": 0, "unconditional": true, "description": "Старт", "targetNodeId": "welcome" }
        ]
      },
      "welcome": {
        "type": "message",
        "data": {
          "message": "Привет, {username}! Выберите раздел:",
          "keyboard": {
            "type": "reply",
            "resize_keyboard": true,
            "one_time": false,
            "buttons": [ [{ "text": "Заявка" }, { "text": "Квиз" }], [{ "text": "О боте" }] ]
          },
          "saveVariable": "user_choice",
          "trackResponseInStats": true,
          "enableErrorHandling": true,
          "invalidInputMessage": "Не понял, выберите кнопку меню.",
          "maxInvalidAttempts": 3,
          "invalidAttemptsTargetNodeId": "welcome"
        },
        "transitions": [
          { "id": "go-lead", "regex": "/Заявка/i", "priority": 1, "description": "Заявка", "targetNodeId": "lead_name" },
          { "id": "go-quiz", "regex": "/Квиз/i",   "priority": 2, "description": "Квиз",   "targetNodeId": "quiz" },
          { "id": "fallback","regex": ".*",          "priority": 100,"description": "Повтор", "targetNodeId": "welcome" }
        ]
      },
      "lead_name": {
        "type": "message",
        "data": { "message": "Как вас зовут?", "saveVariable": "lead_name",
          "enableErrorHandling": true, "invalidInputMessage": "Введите имя.", "maxInvalidAttempts": 2, "invalidAttemptsTargetNodeId": "welcome" },
        "transitions": [ { "id": "ln", "regex": ".*", "priority": 100, "description": "Дальше", "targetNodeId": "enrich" } ]
      },
      "enrich": {
        "type": "http",
        "data": {
          "url": "https://api.agify.io/?name={lead_name}", "method": "GET",
          "headers": { "Content-Type": "application/json" }, "timeout": 30000, "auth": { "type": "none" },
          "variableMappings": [ { "field": "age", "variable": "age" } ]
        },
        "transitions": [ { "id": "en", "regex": ".*", "priority": 0, "unconditional": true, "description": "После HTTP", "targetNodeId": "ask_phone" } ]
      },
      "ask_phone": {
        "type": "message",
        "data": { "message": "{lead_name}, ориентировочно вам {age} лет. Оставьте телефон:", "saveVariable": "phone",
          "enableErrorHandling": true, "invalidInputMessage": "Введите телефон.", "maxInvalidAttempts": 3, "invalidAttemptsTargetNodeId": "welcome" },
        "transitions": [ { "id": "ap", "regex": ".*", "priority": 100, "description": "Проверка", "targetNodeId": "check_phone" } ]
      },
      "check_phone": {
        "type": "condition",
        "data": { "condition": "context.phone && context.phone.replace(/\\D/g,'').length >= 10", "trueTarget": "notify", "falseTarget": "ask_phone" }
      },
      "notify": {
        "type": "notify_user",
        "data": { "recipientId": "{manager_id}", "message": "Заявка: {lead_name}, тел {phone}, возраст ~{age}" },
        "transitions": [ { "id": "nt", "regex": ".*", "priority": 0, "unconditional": true, "description": "Дальше", "targetNodeId": "followup" } ]
      },
      "followup": {
        "type": "schedule_message",
        "data": { "delayValue": 1, "delayUnit": "minutes", "message": "Спасибо, {lead_name}! Мы на связи." },
        "transitions": [ { "id": "fu", "regex": ".*", "priority": 0, "unconditional": true, "description": "Дальше", "targetNodeId": "end" } ]
      },
      "quiz": {
        "type": "message",
        "data": {
          "message": "Сколько будет 2+2?",
          "keyboard": { "type": "inline", "buttons": [ [{ "text": "3", "callback_data": "a3" }, { "text": "4", "callback_data": "a4" }] ] },
          "enableErrorHandling": true, "invalidInputMessage": "Выберите кнопку.", "maxInvalidAttempts": 3, "invalidAttemptsTargetNodeId": "quiz"
        },
        "transitions": [
          { "id": "ok",  "regex": "/a4/i", "priority": 1, "description": "Верно",   "targetNodeId": "welcome" },
          { "id": "bad", "regex": "/a3/i", "priority": 2, "description": "Неверно", "targetNodeId": "quiz" }
        ]
      },
      "end": { "type": "end" }
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

✅ ПРАВИЛЬНО: `"/да|интересно/i"`, `"/^[\w.-]+@[\w.-]+\.[a-z]{2,}$/i"`, `".*"`
❌ НЕПРАВИЛЬНО (ломает сценарий): `"(?i)(да|нет)"`, `"(?i)привет"`

Правила приоритетов:
- конкретные переходы: `priority` 1-10
- fallback `".*"`: `priority` >= 100

## Кнопки: reply и inline (роутинг)

`keyboard` — поле внутри `message`/`schedule_message`, не отдельный узел.
- `reply`: при нажатии бот получает ТЕКСТ кнопки → `regex` перехода матчит текст кнопки. Кнопка: `{ "text": "Да" }`.
- `inline`: при нажатии бот получает `callback_data` → `regex` перехода матчит `callback_data` (НЕ текст).
  Кнопка: `{ "text": "Да", "callback_data": "yes" }`. Кнопка-ссылка: `{ "text": "Сайт", "url": "https://..." }` (перехода не требует).

## Обработка невалидного ввода

Для `message`, ждущих ответ: `enableErrorHandling: true`, `invalidInputMessage`, `maxInvalidAttempts`, `invalidAttemptsTargetNodeId`.
Важно: `invalidInputMessage` срабатывает ТОЛЬКО если не совпал ни один regex. Если у узла есть catch-all `".*"`
(priority ≥ 100) — он перехватит ввод первым, и `invalidInputMessage` не покажется. Выбирай ОДНУ стратегию на узел.

## КРИТИЧЕСКИ ВАЖНО: condition

`condition` — JS-выражение `new Function('context','return '+condition)`.
✅ `"context.timeline && context.timeline.includes('срочно')"`, `"parseInt(context.nps_score) >= 9"`
❌ `"{timeline} === 'срочно'"` — `{var}` в condition запрещён.

## Узлы action / http / notify_user / schedule_message / clear_scheduled_messages

- `action`: `data.variables: [{ "name": "...", "value": "..." }]`. После — безусловный переход.
- `http`: `data` = `{ url, method, headers, queryParams, body, timeout, auth:{type:none|basic|bearer}, variableMappings:[{field, variable}] }`. После — безусловный переход.
- `notify_user`: `data` = `{ recipientId, message }` (оба поддерживают `{var}`). После — безусловный переход.
- `schedule_message`: `data` = `{ delayValue, delayUnit(minutes|hours|days), message, keyboard? }`.
- `clear_scheduled_messages`: без `data`. После — безусловный переход.

## Общие правила генерации

- Сценарий обязан иметь узел `start` и узел `end`
- Все `targetNodeId` / `trueTarget` / `falseTarget` / `invalidAttemptsTargetNodeId` должны существовать в `states`
- `condition`-узлы не имеют `transitions`; только `trueTarget` и `falseTarget`
- `saveVariable` сохраняет ответ в `context`
- Подстановка `{var}` работает в `message`, `http.url`, `http.body`, `notify_user.recipientId`, `notify_user.message`, `schedule_message.message`
- Переход с `"unconditional": true` выполняется сразу, без ожидания ввода
- Все используемые переменные объяви в `config.context`
- Встроенные переменные (без объявления): `{userId}`, `{username}`, `{user_name}`, `{messengerType}`, `{recipient}`, `{lastUserInput}`

Генерируй реалистичные сценарии с fallback-ветками и обработкой невалидного ввода.

---

## Сценарий: Универсальный демо-бот (показывает ВСЕ возможности платформы)

Создай сценарий чат-бота, который демонстрирует все типы узлов и кнопок и при этом
полностью работоспособен. Бот должен:

1. Приветствовать пользователя по имени (`{username}`) и показывать главное меню **reply-кнопками**
   (3–4 раздела). Возврат в меню доступен из любой ветки.
2. Раздел «Квиз»: задать вопрос с **inline-кнопками** (маршрутизация по `callback_data`).
   При верном ответе — узел `action` начисляет балл (переменная `score`), показать балл `{score}`.
   При неверном — мягко предложить «Ещё раз» / «В меню» (inline callback).
3. Раздел «Заявка» (лид-форма):
   - спросить имя (`saveVariable`), затем через узел `http` обогатить данные внешним API
     `https://api.agify.io/?name={lead_name}` и сохранить поле `age` через `variableMappings`;
   - показать персонализированное сообщение с `{lead_name}` и `{age}`;
   - спросить телефон (`saveVariable`), проверить его узлом `condition`
     (минимум 10 цифр): при успехе — продолжить, иначе — переспросить;
   - узел `notify_user` шлёт заявку в личку (по `{manager_id}` или `{userId}`) с `{переменными}`;
   - узел `schedule_message` ставит отложенное напоминание (через 1 минуту);
   - финал с inline-кнопкой «Отменить напоминание» (callback) → узел `clear_scheduled_messages` → `end`.
4. Раздел «О боте» / «Ссылки»: сообщение с **inline-кнопками-ссылками** (`url`) и кнопкой «В меню» (callback).
5. Везде, где бот ждёт ввод, — корректная обработка нераспознанного ввода (fallback `.*`→повтор ИЛИ
   `invalidInputMessage`, но не одновременно на одном узле).

Используй context для хранения: `user_choice`, `lead_name`, `phone`, `age`, `score`, `manager_id`.

## Параметры вашего бизнеса

Заполните под себя (для демо можно оставить как есть):
- Название бота: Демонстрационный бот
- Разделы меню: Заявка, Квиз, О боте, Ссылки
- Вопрос квиза и варианты: «Сколько будет 2+2?» → 3 / 4 / 22 (верный — 4)
- Внешний API для обогащения: https://api.agify.io/?name={lead_name} (поле age)
- Получатель уведомлений: переменная manager_id (или {userId} для копии самому пользователю)
- Ссылки в разделе «Ссылки»: https://telegram.org , https://github.com

## Требования к выводу

Сгенерируй валидный JSON-файл для импорта в Bot Builder. Минимум 16–20 узлов и ОБЯЗАТЕЛЬНО задействуй
КАЖДЫЙ тип узла хотя бы один раз: `start`, `message`, `condition`, `action`, `http`, `notify_user`,
`schedule_message`, `clear_scheduled_messages`, `end`. Используй и `reply`, и `inline` кнопки, и
inline-кнопку-ссылку (`url`). Соблюдай все правила выше (regex `/.../i`, fallback priority ≥ 100,
condition на `context.*`, безусловные переходы после служебных узлов, объявленные переменные).

Верни ТОЛЬКО валидный JSON без пояснений.
