# companion/

Софт для companion-компьютеров на дроне (Raspberry Pi, Jetson, Orange Pi).

Каждый проект здесь — **самостоятельный**, со своим `pyproject.toml`, тестами, инструкциями. По шаблону `u1u2-bridge` (если знаком — посмотри как там устроено).

## Что относится сюда

- Скрипты, которые запускаются через `systemd` на companion-компьютере
- Компьютерное зрение, precision landing (ArUco), object tracking
- Видеостриминг через GStreamer (RTSP, RTP, low-latency H.264)
- Мониторинг и телеметрия (proxy между FC и GCS)
- Сетевые мосты (UART↔IP, как `u1u2-bridge`)

## Что НЕ сюда

- Прошивка FC (это в `firmware/`)
- ArduPilot параметры (это в `builds/`)
- Универсальные утилиты разработки/анализа на ПК (это в `tools/`)

## Соглашения

- Каждый подпроект — отдельная папка с `README.md`, `pyproject.toml`, `CLAUDE.md`, `verify.ps1` (если стек Python).
- Когда подпроект созревает и становится самостоятельным — можно вынести в отдельный репо (например, как было сделано с `u1u2-bridge`).

## Скил для этого раздела

`drone-companion-dev` — Raspberry Pi headless setup, GStreamer pipelines, networking (WireGuard, 4G/LTE), watchdog, read-only rootfs, Edge AI, visual nav.
