# RC_OPTIONS bitmask (ArduPilot)

Параметр `RC_OPTIONS` в ArduPilot — это **битовое поле**. Каждый бит включает / выключает свою опцию. Значение параметра = сумма (логическое ИЛИ) значений включённых битов.

Извлечено из разбора в `builds/cube-orange-elrs-walksnail/ANALYSIS.md` Часть 2.

## Часто используемые биты (для ELRS / CRSF)

| Бит | Десятичное | Что делает |
|---:|---:|---|
| 0 | 1 | Ignore RC Receiver |
| 1 | 2 | Ignore RC Override Channel |
| 2 | 4 | Ignore receiver failsafe bit |
| 3 | 8 | FPort PAD |
| 4 | 16 | Log RC Input |
| 5 | 32 | Arming check throttle |
| 6 | 64 | Allow Switch Reverse |
| 7 | 128 | CRSF custom telemetry |
| 8 | 256 | Suppress CRSF mode/rate сообщение |
| 9 | 512 | Suppress CRSF mode/rate (ELRS-specific) |
| 10 | 1024 | Bypass RC failsafe with throttle |
| 11 | 2048 | Disable RC Filtering |
| 12 | 4096 | RC Loss after Initial Connection |
| **13** | **8192** | **Use 420K baud rate для ELRS** ← критически важно |
| 14 | 16384 | Enable MAVLink output of RC |

## Типовая конфигурация для ELRS на Cube Orange

```
RC_OPTIONS = 8708
```

Раскладка:
- **8192** (бит 13) — 420K baud для ELRS
- **512** (бит 9) — suppress CRSF mode/rate сообщение
- **4** (бит 2) — ignore receiver failsafe bit
- Сумма = **8708** ✓

## Важное взаимодействие с `SERIAL4_BAUD`

**Бит 13 (`8192`) автоматически переопределяет `SERIAL4_BAUD = 115` на 420000 baud.** Менять `SERIAL4_BAUD` отдельно НЕ нужно.

Официальная рекомендация ExpressLRS: оставить `SERIAL4_BAUD = 115` и включить бит 13 в `RC_OPTIONS`. Это **более надёжный** способ, чем выставлять `SERIAL4_BAUD = 420` напрямую.

## Калькулятор

В Mission Planner: **Config → Full Parameter List → клик по `RC_OPTIONS`** → выпадает диалог с галочками по каждому биту, сам считает сумму.

Вручную: `RC_OPTIONS = сумма значений включённых битов`.

## Источники

- [ArduPilot — RC_OPTIONS parameter reference](https://ardupilot.org/copter/docs/parameters.html#rc-options-rc-options)
- [ArduPilot — Common TBS Crossfire / ELRS setup](https://ardupilot.org/copter/docs/common-tbs-rc.html)
- [ExpressLRS — ArduPilot quick start](https://expresslrs.org/quick-start/ardupilot-setup/)
