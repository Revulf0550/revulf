# Raspberry Pi Companion Computer

Код компаньон-компьютера для дрона на базе **Cube Orange + ExpressLRS + Walksnail Avatar V2**.

## Возможности

- **Мониторинг телеметрии** — GPS, батарея, attitude, RC-каналы через MAVLink
- **Мониторинг ELRS** — Link Quality, RSSI, детектирование деградации связи, алерты
- **Проверка параметров** — автоматическая верификация настроек ArduPilot для ELRS/Walksnail
- **Исправление RSSI** — автоматическое исправление RSSI_TYPE и RSSI_CHANNEL для корректного отображения LQ на OSD
- **Терминальный дашборд** — цветной real-time мониторинг в консоли
- **Логирование** — запись телеметрии в CSV для анализа полётов

## Структура

```
raspberry_pi/
├── main.py            # Точка входа, CLI-интерфейс
├── config.py          # Конфигурация (порты, пороги, параметры)
├── mavlink_manager.py # MAVLink соединение и управление
├── telemetry.py       # Сбор телеметрии (GPS, батарея, attitude, RC)
├── elrs_monitor.py    # Мониторинг качества связи ELRS
├── param_manager.py   # Проверка и исправление параметров ArduPilot
├── dashboard.py       # Терминальный дашборд
├── data_logger.py     # Запись телеметрии в CSV
├── requirements.txt   # Python-зависимости
└── setup.sh           # Скрипт установки на Raspberry Pi
```

## Быстрый старт

### Установка на Raspberry Pi

```bash
git clone <repo> ~/companion
cd ~/companion/raspberry_pi
chmod +x setup.sh
sudo ./setup.sh
```

### Запуск

```bash
# Активация виртуального окружения
source ~/companion_venv/bin/activate
cd ~/companion/raspberry_pi

# Дашборд (основной режим)
python3 main.py

# Проверка параметров
python3 main.py --check-params

# Исправление RSSI (предпросмотр)
python3 main.py --fix-params --dry-run

# Исправление RSSI (применить)
python3 main.py --fix-params

# Без дашборда, только логирование
python3 main.py --log-only
```

### Подключение

```bash
# GPIO UART (по умолчанию)
python3 main.py --port /dev/ttyAMA0

# USB-to-serial адаптер
python3 main.py --port /dev/ttyUSB0

# UDP (WiFi телеметрия)
python3 main.py --port udpin:0.0.0.0:14550

# TCP (SITL симулятор)
python3 main.py --port tcp:127.0.0.1:5760
```

## Подключение Raspberry Pi к Cube Orange

### Схема подключения (UART)

```
Raspberry Pi           Cube Orange (TELEM2)
  GPIO 14 (TX) ──────── RX
  GPIO 15 (RX) ──────── TX
  GND ─────────────────── GND
```

### Параметры ArduPilot для MAVLink на TELEM2

```
SERIAL2_PROTOCOL = 2      # MAVLink2
SERIAL2_BAUD = 921        # 921600 baud
```

> Если SERIAL2 уже используется для Walksnail MSP, подключите Raspberry Pi к другому порту (TELEM1, GPS2 и т.д.) и измените `SERIAL*` параметры соответственно.

## Критические исправления

Этот код автоматически проверяет и исправляет проблему с отображением RSSI/LQ на OSD:

| Параметр | Неправильно | Правильно | Причина |
|----------|-------------|-----------|---------|
| `RSSI_TYPE` | 2 | **3** | ELRS передаёт RSSI через CRSF, а не через RC-канал |
| `RSSI_CHANNEL` | 15 | **0** | Не нужен при RSSI_TYPE=3 |

## Автозапуск

```bash
sudo systemctl enable companion
sudo systemctl start companion
```

Логи: `journalctl -u companion -f`
