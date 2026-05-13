# firmware/

Кастомная прошивка и конфигурации для микроконтроллеров.

| Подпапка | Что внутри |
|---|---|
| [stm32/](stm32/) | STM32-проекты (CubeIDE / PlatformIO) — custom flight controllers, peripheral boards, telemetry bridges |
| [arduino/](arduino/) | Arduino sketches — простая периферия, прототипы датчиков, диагностические утилиты |
| [betaflight-configs/](betaflight-configs/) | CLI-дампы Betaflight по конкретным сборкам (`<имя_дрона>_<дата>.txt`) |

## Соглашения

- Каждый STM32-проект — отдельная подпапка с собственным `README.md` и build-системой (Makefile / `.ioc` / `platformio.ini`).
- Arduino sketches — папка на проект, как в Arduino IDE (главный `.ino` файл должен совпадать по имени с папкой).
- Betaflight CLI-дампы — один `.txt` файл на сборку, формат `<имя_сборки>_<YYYY-MM-DD>.txt`. Получается через `diff all` в Betaflight CLI или через export presets.

## Что подгружать из скилов

- **STM32 / Arduino / ESP32** — скилл `embedded-programmer` (Linux/Windows/Mac toolchain, peripherals, RTOS).
- **Betaflight CLI** — скилл `fpv-expert`, раздел `references/betaflight.md`.
- **Кастомные платы под ArduPilot (hwdef.dat)** — скилл `ardupilot-expert`, раздел `references/custom-firmware.md`.
