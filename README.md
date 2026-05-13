# revulf — UAV development workspace

Личный рабочий kit для разработки и настройки дронов и связанных изделий.

Накапливает анализы по конкретным сборкам, переиспользуемые шаблоны параметров, кастомную прошивку для микроконтроллеров, скрипты для companion-компьютеров, заметки и шпаргалки по UAV-стеку.

## Структура

| Папка | Что внутри |
|---|---|
| [builds/](builds/) | Конкретные сборки дронов: параметр-файлы, анализы, история инцидентов |
| [firmware/](firmware/) | Кастомный код для МК (STM32, Arduino) и CLI-дампы Betaflight |
| [companion/](companion/) | Софт для companion-компьютеров (Raspberry Pi, Jetson) |
| [tools/](tools/) | Переиспользуемые утилиты (param-diff, log-analyzer и т.п.) |
| [templates/](templates/) | Базовые шаблоны параметров (ArduPilot, ELRS, Betaflight) для новых сборок |
| [notes/](notes/) | Knowledge base — шпаргалки, биткарты, протоколы, распиновки |

Правила работы AI с этим workspace — в [CLAUDE.md](CLAUDE.md).

## Текущие сборки

- **[cube-orange-elrs-walksnail](builds/cube-orange-elrs-walksnail/)** — основной коптер на Cube Orange + ArduCopter + ExpressLRS + Walksnail Avatar V2

## Workflow при новой проблеме на сборке

1. Открываешь Project в claude.ai, привязанный к `revulf`.
2. Идёшь в `builds/<своя_сборка>/`. Создаёшь файл `incidents/YYYY-MM-DD-короткий-симптом.md` с описанием проблемы.
3. Чатишься с Claude — он по `CLAUDE.md` знает: проверять параметры по официальной документации, давать рекомендации таблицей «было/стало/почему», цитировать ardupilot.org/expresslrs.org.
4. Зафиксированный анализ — отдельный коммит, инцидент в `incidents/`.
5. Если есть правки `.param` файла — сохраняешь предыдущий в `history/YYYY-MM-DD.param`, применяешь новый через Mission Planner, проверяешь на железе.
6. Итог после проверки на железе — переносишь в накапливающий `ANALYSIS.md` сборки.

## Workflow при новой сборке

```bash
mkdir -p builds/<имя_сборки>/incidents builds/<имя_сборки>/history
# Скопируй ближайший шаблон из templates/ardupilot/ в builds/<имя>/current.param
# Подстрой под железо
# Создай README.md с описанием компонентов
```
