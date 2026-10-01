# reference/01 — Корневая схема сценария

```json
{
  "name": "Название бота",            // string, обязательно
  "description": "Описание",          // string
  "config": {
    "id": "my-bot-machine",           // string, id машины состояний
    "initial": "start",               // id стартового узла (обычно "start")
    "context": {                      // объект начальных переменных (объявляй все)
      "var1": "",
      "manager_id": "123456789"
    },
    "states": {                       // словарь узлов: ключ = id узла
      "start": { "type": "start", "transitions": [ /* ... */ ] },
      "...":   { "type": "...",   "data": { /* ... */ }, "transitions": [ /* ... */ ] },
      "end":   { "type": "end" }
    }
  }
}
```

## Поля

| Путь | Тип | Обязательно | Назначение |
|---|---|---|---|
| `name` | string | да | Имя бота в списке «Мои боты». |
| `description` | string | желательно | Описание. |
| `config.id` | string | да | Идентификатор state-machine (kebab-case). |
| `config.initial` | string | да | Стартовый узел = `"start"`. |
| `config.context` | object | да | Начальные переменные (flat-ключи; опц. вложенный `variables`). |
| `config.states` | object | да | Узлы. Ключ — id узла, значение — объект узла. |

## Не входит в JSON-сценарий
- **Позиции узлов** (x/y) — раскладка авто при импорте.
- **Цикличность** — настройка бота (`is_cyclic`), тумблер в списке «Боты».
- **Статус (вкл/выкл)**, **мессенджеры/токены** — настройки бота, не сценария.

## Узел = состояние
```json
{ "type": "<один из 9 типов>", "data": { /* поля под тип */ }, "transitions": [ /* переходы */ ] }
```
- `condition` — без `transitions` (есть `trueTarget`/`falseTarget` в `data`).
- `end` — без `data` и `transitions`.
- `start` — без `data`.

Детали по типам — [02-node-types.md](02-node-types.md). Переходы — [05-transitions-regex.md](05-transitions-regex.md).
