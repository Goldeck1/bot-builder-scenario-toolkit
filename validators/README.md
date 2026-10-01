# validators/

## validate_scenario.py

Пред-полётный валидатор сценария Bot Builder. Проверяет JSON по жёстким правилам движка
(см. [`../reference/06-hard-rules.md`](../reference/06-hard-rules.md)) ДО импорта в продукт.

### Запуск
```bash
python3 validate_scenario.py scenario.json
python3 validate_scenario.py a.json b.json          # несколько файлов
cat scenario.json | python3 validate_scenario.py -  # из stdin
```

### Коды возврата
- `0` — ERROR нет (можно импортировать; WARNINGS просмотреть).
- `1` — есть ERROR (импортировать нельзя — поломается).
- `2` — файл не прочитан / невалидный JSON.

### Что ловит
- ERROR: нет start/end, битые ссылки на узлы, condition с transitions, `{var}` в condition,
  инлайн-флаги `(?i)` в regex, недопустимые типы узлов, нечисловой priority, кривой
  variableMappings, отсутствие initial и т.д.
- WARN: служебный узел без `unconditional`, message без обработки ошибок, fallback с низким
  priority, повтор priority, необъявленные переменные, подозрительные поля узлов.

### Контракт
**Любой сгенерированный сценарий проходит этот валидатор с 0 ERROR перед выдачей.**
Зависимостей нет — только стандартная библиотека Python 3.

### Проверка самого валидатора
```bash
# валидные эталоны → 0 ERROR
python3 validate_scenario.py ../examples/minimal.json ../examples/all-nodes.json
```
