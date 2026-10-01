# Bot Builder Scenario Toolkit

Практический набор спецификаций, примеров и инструментов для проектирования JSON-сценариев
визуального no-code конструктора чат-ботов. Сценарии описываются как **машина состояний** и
могут использоваться для Telegram, WhatsApp, VK, MAX и Web-виджетов.

Репозиторий объединяет две дорожки: компактные правила для генерации сценариев с помощью LLM
и подробную документацию для разработчиков и аналитиков. Встроенный валидатор помогает
находить ошибки до импорта сценария в платформу.

---

## 🤖 Машинная дорожка (генерация сценариев) — главное

1. **[SKILL.md](SKILL.md)** — ★ вход. Сжатый свод правил генерации + чек-лист.
2. **[canonical/platform-spec.md](canonical/platform-spec.md)** — каноническая спецификация
   формата. При конфликте документации следует ориентироваться на неё.
3. **reference/** — выверенный по движку референс:
   - [01 — Корневая схема](reference/01-scenario-schema.md)
   - [02 — Типы узлов (точные поля)](reference/02-node-types.md)
   - [03 — Клавиатуры (reply/inline, callback_data, лимиты каналов)](reference/03-keyboards.md)
   - [04 — Переменные и context](reference/04-variables.md)
   - [05 — Переходы, regex, приоритеты](reference/05-transitions-regex.md)
   - [06 — Жёсткие правила (что проверяет валидатор)](reference/06-hard-rules.md)
   - [07 — API, запуск бота и эксплуатация](reference/07-api-и-эксплуатация.md)
4. **[validators/validate_scenario.py](validators/validate_scenario.py)** — ★ пред-полётный
   проверяльщик. **Контракт: сценарий выдаётся только при 0 ERROR.**
5. **examples/** — эталоны:
   - [minimal.json](examples/minimal.json) — минимальный валидный
   - [all-nodes.json](examples/all-nodes.json) — по одному узлу каждого из 9 типов
   - [lead-bot.json](examples/lead-bot.json) — реалистичный лид-бот
   - [roundtrip-demo.json](examples/roundtrip-demo.json) — «всё включено», протестирован вживую
6. **[VERIFIED-LIVE.md](VERIFIED-LIVE.md)** — обезличенный журнал интеграционной проверки.
7. **prompts/** — готовые промпты для LLM: [demo-universalnyi-bot.md](prompts/demo-universalnyi-bot.md).

### Быстрый цикл
```bash
# 1. сгенерировать scenario.json по SKILL.md
# 2. проверить:
python3 "validators/validate_scenario.py" scenario.json
# 3. при 0 ERROR — импорт: Боты → Импорт (файл) ИЛИ Редактор → JSON редактор → вставить → Сохранить
```

## 📖 Человеческая дорожка (читать) — `human-docs/`

Подробные объяснения с таблицами: обзор разделов, схема, типы нод, переходы, переменные,
генерация, тест/деплой, эксплуатация, шпаргалка. См. [human-docs/](human-docs/) (файлы 01–09).

---

## TL;DR

- Сценарий = `{name, description, config{id, initial:"start", context{}, states{}}}`.
- `states` — словарь нод; нода = `{type, data, transitions[]}`.
- **9 типов:** start · message · condition · action · http · notify_user · schedule_message ·
  clear_scheduled_messages · end.
- `condition` — без `transitions` (только `trueTarget`/`falseTarget`).
- Переход: `{id, regex, priority, description, targetNodeId, unconditional?}`. Меньше priority =
  выше. Fallback `.*` → priority ≥ 100.
- В текстах `{var}`, в условиях `context.var`. regex = `/.../i` (не `(?i)`).
- **reply-кнопки матчатся по тексту, inline — по `callback_data`.**
- Цикличность и позиции узлов — НЕ в JSON.
- Перед импортом — валидатор, 0 ERROR.

## Безопасность

- Не добавляйте в сценарии реальные токены ботов, API-ключи и персональные данные.
- Перед публикацией используйте переменные окружения или секрет-хранилище целевой платформы.
- Примеры в репозитории содержат только демонстрационные URL и значения.

## Ограничения

Формат сценария и доступные каналы зависят от конкретной реализации Bot Builder. Перед
продуктивным импортом проверьте совместимость со своей версией платформы и выполните тестовый
прогон в изолированном окружении.
