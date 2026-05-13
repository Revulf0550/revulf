# templates/

Базовые шаблоны параметров и конфигураций для **быстрого старта новой сборки**. Главная ценность workspace — то, что копится годами и страхует от "с нуля каждый раз".

| Подпапка | Что внутри |
|---|---|
| [ardupilot/](ardupilot/) | `.param` файлы — базовая конфигурация Copter / Plane на ELRS / Crossfire / FrSky |
| [elrs/](elrs/) | `.json` экспорт ELRS Web UI — long range / FPV / прочие профили |
| [betaflight/](betaflight/) | CLI-дампы Betaflight — `presets.txt` для freestyle / cinewhoop / long range |

## Workflow при новой сборке

1. **Подобрать ближайший шаблон** под класс сборки (длинноход / freestyle / агро).
2. **Скопировать** в `builds/<новая_сборка>/current.param`.
3. **Подстроить** под конкретное железо:
   - `FRAME_CLASS`, `FRAME_TYPE`
   - количество моторов (для гексы / окты — другие значения)
   - калибровки (компас, акселерометр)
   - ESC-протокол (`MOT_PWM_TYPE`)
4. **После полевых испытаний**, если получили улучшения — **обновить шаблон** в `templates/`, чтобы следующая сборка стартовала с лучшей точки.

## Соглашения именования

- `ardupilot/copter-elrs-base.param` — базовый Copter на ELRS
- `ardupilot/copter-elrs-longrange.param` — для дальних полётов
- `ardupilot/plane-elrs-base.param` — самолёт
- `elrs/longrange-150hz-1to32telem.json` — конкретный профиль (Packet Rate в названии)
- `betaflight/freestyle-5inch-4-5.txt` — Betaflight CLI dump (с версией прошивки)
