# ELRS: Packet Rate vs дальность vs задержка

Главный компромисс ExpressLRS — **частота пакетов управления**. Чем выше — меньше задержка стиков, но меньше энергии на пакет → меньше дальность. Эта таблица помогает выбрать.

Извлечено из `builds/cube-orange-elrs-walksnail/ANALYSIS.md` Часть 6.

## Таблица компромиссов

| Packet Rate | Задержка управления | Дальность (относительно) | Использование |
|---:|---:|---|---|
| 50 Гц | ~40 мс | Максимальная | Дальние полёты 100+ км |
| 100 Гц | ~25 мс | Очень большая | Дальние полёты 50–100 км |
| **150 Гц** | **~16 мс** | **Большая** | **Дальние полёты 20–50 км, оптимум для автопилотов** |
| 250 Гц | ~8 мс | Средняя | FPV freestyle / cruising до 20 км |
| 333 Гц | ~6 мс | Меньше | FPV средней дальности |
| 500 Гц | ~4 мс | Малая | FPV racing |
| 1000 Гц | ~2 мс | Минимальная | Чистые гонки, экстремум по latency |

## Сопутствующие настройки TX модуля (Lua Script) для дальних полётов на ArduPilot

| Параметр | Рекомендация | Почему |
|---|---|---|
| Packet Rate | 150 Гц | Баланс задержки (~16 мс) и дальности |
| Telemetry Ratio | 1:32 | Минимальное влияние на bandwidth стиков |
| Switch Mode | Hybrid | Стандарт для автопилотов |
| RF Mode | Dynamic | Авто-переключение для максимальной дальности |
| Model Match | OFF | Предотвращает странные failsafe на автопилотах |
| Dynamic Power | ON | Авто-регулировка мощности |
| Max Power | Максимум доступный по регулировке | Для дальности |

## Полный бюджет задержки управления (ArduCopter)

ELRS Packet Rate — только **часть** задержки. Полная цепочка от стика до движения дрона:

| Источник задержки | Типичное значение | Уменьшение |
|---|---:|---|
| ELRS Packet Rate (150 Гц) | ~16 мс | Увеличить Packet Rate |
| CRSF serial передача | ~2 мс | Не уменьшить |
| ArduPilot обработка RC (400 Гц) | ~2.5 мс | Не уменьшить (`SCHED_LOOP_RATE` рискованно менять) |
| PID контроллер | ~2.5 мс | Не уменьшить |
| ESC PWM output (490 Гц) | ~2 мс | DShot → ~100 мкс |
| **`ATC_INPUT_TC` (input shaping)** | **до 150 мс** | **Главное — уменьшить с 0.15 до 0.05–0.10** |
| IOMCU (MAIN OUT на Cube Orange) | ~2.5 мс | Использовать AUX OUT |

**Главный убийца отзывчивости стиков — НЕ ELRS Packet Rate, а `ATC_INPUT_TC`** (по умолчанию 0.15 секунд). Если кажется, что «лагает» — первое, что проверять.

## Связь с RSSI / LQ

При снижении Packet Rate (50–100 Гц) — статистика обновляется реже, скачки RSSI заметнее. Это нормально и не означает деградацию связи. LQ всё ещё показывает процент успешно принятых пакетов от ожидаемого.

## Источники

- [ExpressLRS — Signal Health](https://expresslrs.org/info/signal-health/)
- [ExpressLRS — Telemetry Bandwidth](https://expresslrs.org/info/telem-bandwidth/)
- [ExpressLRS — Switch Configs](https://expresslrs.org/software/switch-config/)
- [ArduPilot — Input Shaping (ATC_INPUT_TC)](https://ardupilot.org/copter/docs/input-shaping.html)
- [ArduPilot — Common DShot Setup](https://ardupilot.org/copter/docs/common-dshot.html)
