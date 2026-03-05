# RSSI & LQ на OSD — Cube Orange + ELRS + Walksnail + ArduPilot

Настройка параметров ArduPilot для отображения **реальных значений RSSI и LQ** на OSD через Walksnail (MSP DisplayPort).

---

## Оборудование

| Компонент | Модель / Протокол |
|-----------|-------------------|
| Автопилот | Cube Orange |
| Прошивка | ArduPilot 4.1+ (рекомендуется 4.5+) |
| RC-линк | ExpressLRS (CRSF) |
| Видео | Walksnail (MSP DisplayPort OSD) |

---

## Проблема

При неправильных параметрах RSSI и LQ на OSD ведут себя некорректно:
- RSSI застревает на **99** или **0**
- LQ не обновляется, показывает **0** или **100** постоянно
- Значения не соответствуют реальному качеству связи

**Причины:**
1. `RSSI_TYPE=2` — берёт RSSI из RC-канала (PWM), но ELRS так не передаёт
2. `RSSI_CHANNEL=15` — ссылается на несуществующий канал
3. Неверная скорость UART (115200 вместо 420000)
4. Лишние флаги в `RC_OPTIONS`, мешающие разбору CRSF-телеметрии

---

## Решение — параметры в файле `GR_ERLS_v28c_RSSI_LQ_FIX.param`

### Основные изменения

| Параметр | Было | Стало | Зачем |
|----------|------|-------|-------|
| `SERIAL4_BAUD` | 115 | **420** | ELRS использует 420000 baud — стандарт CRSF |
| `RSSI_TYPE` | 2 | **3** | ReceiverProtocol — ArduPilot берёт RSSI/LQ из CRSF Link Statistics |
| `RSSI_CHANNEL` | 15 | **0** | При `RSSI_TYPE=3` канал не нужен |
| `RC_OPTIONS` | 8708 | **768** | Bit 8 (256): CRSF passthru + Bit 9 (512): подавление ELRS rate-сообщений |
| `RC_SPEED` | 490 | **0** | AUTO — частоту задаёт сам ELRS |
| `SCHED_LOOP_RATE` | 400 | **800** | Cube Orange тянет 800 Hz — быстрее PID, меньше задержка |

### Walksnail OSD (проверить, не менять если уже настроено)

| Параметр | Значение | Описание |
|----------|----------|----------|
| `OSD_TYPE` | 5 | MSP DisplayPort |
| `SERIAL2_PROTOCOL` | 42 | MSP DisplayPort на SERIAL2 |
| `SERIAL2_BAUD` | 115 | 115200 baud для MSP |

### OSD-элементы

| Параметр | Значение | Описание |
|----------|----------|----------|
| `OSD1_RSSI_EN` | 1 | Включить отображение RSSI на экране 1 |
| `OSD1_LQ_EN` | 1 | Включить отображение LQ на экране 1 |

> Позиции элементов на экране настраиваются через вкладку OSD в Mission Planner.

---

## Как работает RSSI/LQ в ArduPilot с ELRS

При `RSSI_TYPE=3` ArduPilot получает данные из **CRSF Link Statistics** — специального пакета телеметрии, который ELRS-приёмник отправляет автопилоту ~2 раза в секунду.

Этот пакет содержит:
- **RSSI (dBm)** — мощность принятого сигнала (от 0 до -130 dBm)
- **LQ (Link Quality)** — процент успешно принятых пакетов (0–100%)

**Что отображается на OSD:**
- Поле **RSSI** в ArduPilot OSD фактически показывает **LQ в процентах** (это нормальное поведение)
- Для отображения реального RSSI в dBm нужен элемент RSSI dBm (если поддерживается прошивкой)

### Ожидаемые значения

| LQ | Качество связи |
|----|----------------|
| 80–100% | Отличная связь |
| 60–80% | Нормальная |
| 40–60% | Слабая |
| < 30% | Близко к failsafe |

---

## Разбор RC_OPTIONS = 768

`RC_OPTIONS` — битовая маска. Значение 768 = 256 + 512:

| Бит | Значение | Назначение |
|-----|----------|------------|
| Bit 8 | 256 | CRSF Passthru extensions — пробрасывает расширенную телеметрию (поддержка Yaapu скрипта и др.) |
| Bit 9 | 512 | Suppress CRSF mode/rate messages — подавляет предупреждения ArduPilot о несовпадении packet rate с ELRS |

**Почему не 8708?** Значение 8708 включает биты, которые конфликтуют с CRSF-телеметрией ELRS и приводят к тому, что RSSI застревает на 99 или LQ не обновляется.

---

## Настройки ELRS (TX и RX)

| Параметр | Значение | Примечание |
|----------|----------|------------|
| UART Baud | 420000 | Должен совпадать с `SERIAL4_BAUD=420` |
| Packet Rate | 150 Hz | Баланс задержки и дальности |
| Telemetry Ratio | 1:32 | Реже телеметрия — меньше задержка стиков |
| Switch Mode | Hybrid | Стандартный режим переключателей |
| RF Mode | Dynamic | Автоподбор мощности/частоты |
| Model Match | OFF | Меньше конфликтов с автопилотом |

---

## Инструкция по установке

### Шаг 1 — Загрузить параметры

1. Подключить Cube Orange к Mission Planner / QGroundControl
2. Загрузить файл `GR_ERLS_v28c_RSSI_LQ_FIX.param`
   - Mission Planner: Config → Full Parameter List → Load from file
3. Нажать "Write Params"

### Шаг 2 — Перезагрузить

Отключить и подключить питание Cube Orange (не просто перезагрузить — полный power cycle).

### Шаг 3 — Настроить OSD-элементы

1. Mission Planner → вкладка OSD
2. Перетащить элементы RSSI и LQ на желаемые позиции на экране
3. Записать параметры

### Шаг 4 — Проверить

1. Включить передатчик и ELRS-приёмник
2. В Mission Planner: **Status** → искать `rssi` и `link_quality`
3. Значения должны меняться в реальном времени при удалении/приближении передатчика
4. На очках/экране Walksnail RSSI и LQ должны отображать реальные значения

---

## Диагностика проблем

| Симптом | Причина | Решение |
|---------|---------|---------|
| RSSI = 99 постоянно | `RSSI_TYPE` не равен 3 или неверный `RC_OPTIONS` | Установить `RSSI_TYPE=3`, `RC_OPTIONS=768` |
| LQ = 0 постоянно | UART скорость не совпадает | Проверить `SERIAL4_BAUD=420` и baud на приёмнике = 420000 |
| Нет данных на OSD | OSD-элементы не включены | Включить `OSD1_RSSI_EN=1`, `OSD1_LQ_EN=1` в Mission Planner |
| OSD не работает вообще | Неверный `OSD_TYPE` или `SERIAL_PROTOCOL` | `OSD_TYPE=5`, `SERIAL2_PROTOCOL=42` |
| RSSI скачет | Антенна приёмника повреждена или помехи | Проверить антенну, переместить приёмник |

---

## Источники

- [ExpressLRS — ArduPilot Setup](https://expresslrs.org/quick-start/ardupilot-setup)
- [ArduPilot — CRSF Telemetry](https://ardupilot.org/copter/docs/common-crsf-telemetry.html)
- [ArduPilot — RC_OPTIONS](https://ardupilot.org/copter/docs/common-rc-options.html)
- [ArduPilot — DisplayPort OSD](https://ardupilot.org/copter/docs/common-displayport.html)
- [ArduPilot — MSP OSD](https://ardupilot.org/copter/docs/common-msp-osd-overview-4.2.html)
- [Oscar Liang — LQ and RSSI Explained](https://oscarliang.com/lq-rssi/)