# Cube Orange + ELRS + Walksnail — исправление RSSI/LQ на OSD

Решение проблемы: на OSD Walksnail не отображаются реальные значения RSSI и LQ при использовании ExpressLRS + Cube Orange (ArduPilot).

## Файлы

- **[ELRS_OSD_RSSI_FIX.param](ELRS_OSD_RSSI_FIX.param)** — файл параметров для загрузки в Mission Planner (содержит только 2 параметра, которые нужно изменить)
- **[ANALYSIS.md](ANALYSIS.md)** — полный аудит: причины проблемы, объяснение каждого параметра, настройка задержки управления, оптимальные настройки ELRS

## Быстрое решение

В Mission Planner изменить 2 параметра:

```
RSSI_TYPE    = 3   (было 2 — RC Channel)
RSSI_CHANNEL = 0   (было 15)
```

В ELRS приёмнике (Web UI):

```
UART Baud = 420000  (если стоит 460800 — изменить)
```

Подробнее — в [ANALYSIS.md](ANALYSIS.md).
