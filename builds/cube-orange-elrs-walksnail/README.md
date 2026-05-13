# Cube Orange + ELRS + Walksnail

Основной коптер на ArduPilot. Перенесён в эту папку из корня репозитория при реструктуризации workspace 2026-05-13.

## Hardware

| Компонент | Что стоит | Заметки |
|---|---|---|
| FC | **Cube Orange** | STM32H7-based, два процессора (FMU + IOMCU) |
| Прошивка FC | **ArduPilot Copter** (версия TODO) | |
| RC-линк | **ExpressLRS** через CRSF на SERIAL4 | RX baud rate в Web UI — поставить 420000 (см. ANALYSIS) |
| Видео / OSD | **Walksnail Avatar V2 Dual Kit** через MSP DisplayPort на SERIAL2 | OSD_TYPE = 5 |
| Моторы | TODO | |
| ESC | TODO | DShot возможен только на AUX OUT (Cube Orange limitation) |
| Пропеллеры | TODO | |
| Рама | TODO | |
| Аккумулятор | TODO | |
| GPS / компас | TODO | |
| Телеметрия (отдельная) | TODO | |

## Файлы

- [`ELRS_OSD_FIX.param`](ELRS_OSD_FIX.param) — текущий боевой `.param` файл (исторически назван так после фикса RSSI/LQ на OSD)
- [`ANALYSIS.md`](ANALYSIS.md) — журнал решённых проблем
- [`incidents/`](incidents/) — детальные разборы каждого инцидента
- [`history/`](history/) — архив прошлых версий параметров

## TODO

Из существующего `ANALYSIS.md` — список оставшихся правок:

- [ ] **RX baud rate:** установить 420000 в ELRS Web UI (сейчас 460800, что вызывает потери пакетов из-за mismatch с ожидаемыми ArduPilot 420000)
- [ ] **`ATC_INPUT_TC`:** проверить значение, возможно уменьшить с 0.15 до 0.05–0.10 для меньшей задержки стиков (главный убийца отзывчивости)
- [ ] **DShot:** если ESC поддерживает — рассмотреть переход с PWM 490Гц на DShot600 (`MOT_PWM_TYPE = 6`), требует перенос моторов на AUX OUT
- [ ] **Заполнить TODO в Hardware-таблице выше**

## История

- **2026-03-05** — фикс RSSI/LQ на OSD (`RSSI_TYPE: 2→3`, `RSSI_CHANNEL: 15→0`)
- **2026-05-13** — перенос в новую структуру workspace
