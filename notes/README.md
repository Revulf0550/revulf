# notes/

Markdown-шпаргалки и референсы — твоя личная база знаний по UAV. Сюда отправляется всё, что:

1. Сложно гуглить (специфические термины, мало материалов в открытом доступе)
2. Часто понадобится снова (биткарты, протоколы, распиновки разъёмов)
3. Накопилось как побочный продукт инцидентов (`builds/*/incidents/`)

## Текущие заметки

- [ardupilot-rc-options-bitmask.md](ardupilot-rc-options-bitmask.md) — расшифровка битов `RC_OPTIONS` для ArduPilot
- [elrs-packet-rate-vs-range.md](elrs-packet-rate-vs-range.md) — таблица Packet Rate / задержка / дальность для ELRS

## Идеи будущих заметок

- `crsf-protocol-reference.md` — структура CRSF пакетов, типы сообщений (Link Statistics, RC Channels, Battery)
- `connector-pinouts.md` — JST-SH, JST-GH, Picoblade, DF13, MR30 — распиновки разъёмов часто встречающихся в UAV
- `ardupilot-failsafe-modes.md` — все типы failsafe в ArduPilot (RC / Battery / GCS / EKF / GPS Glitch) и их параметры
- `dshot-protocol-reference.md` — DShot150/300/600 — структура frame'а, telemetry, bidirectional
- `stm32-bootloader-quirks.md` — нюансы DFU mode на разных STM32 (boot pins, USART boot)

## Соглашения

- Имя файла = **тема в kebab-case** (`elrs-tuning-cheatsheet.md`, не `ELRS_Tuning_Cheatsheet.md`).
- В начале файла — однострочное описание того, **зачем эта заметка существует**.
- В конце — раздел `## Источники` с ссылками на authoritative docs.
- Если заметка вытащена из конкретного инцидента — упомянуть в начале (например: «Вытащено из `builds/cube-orange-elrs-walksnail/ANALYSIS.md` 2026-03-05»).
