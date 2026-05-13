# builds/

Папка для конкретных физических сборок дронов. Каждая сборка — отдельная подпапка.

## Структура папки сборки

| Файл / папка | Назначение |
|---|---|
| `README.md` | Описание железа: рама, моторы, ESC, FC, RC, видео-система, GPS, прошивки |
| `current.param` | **Текущий боевой `.param` файл** — тот, что прошит сейчас |
| `ANALYSIS.md` | Накапливающий журнал решённых проблем по этой сборке |
| `incidents/` | История инцидентов: `YYYY-MM-DD-симптом.md` за каждый разбор |
| `history/` | Архив параметр-файлов: `YYYY-MM-DD.param` перед каждой правкой |

## Текущие сборки

- **[cube-orange-elrs-walksnail/](cube-orange-elrs-walksnail/)** — Cube Orange + ArduCopter + ELRS + Walksnail Avatar V2

## Добавление новой сборки

```powershell
mkdir builds\<имя_сборки>\incidents
mkdir builds\<имя_сборки>\history
# Скопировать ближайший шаблон из templates/ardupilot/ в builds/<имя>/current.param
# Создать README.md с описанием железа (см. cube-orange-elrs-walksnail/README.md как образец)
```

Имя сборки — kebab-case, начинается с FC: `cube-orange-...`, `pixhawk6c-...`, `matek-h743-...`.
