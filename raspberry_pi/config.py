"""
Configuration for Raspberry Pi companion computer.
Cube Orange + ELRS + Walksnail Avatar V2 Dual Kit
"""

# MAVLink connection settings
MAVLINK_CONNECTION = "/dev/ttyAMA0"  # UART on Raspberry Pi GPIO
MAVLINK_BAUD = 921600
MAVLINK_SOURCE_SYSTEM = 255
MAVLINK_SOURCE_COMPONENT = 190

# Fallback connections (tried in order if primary fails)
MAVLINK_FALLBACK = [
    "/dev/ttyUSB0",
    "/dev/ttyACM0",
    "udpin:0.0.0.0:14550",
    "tcp:127.0.0.1:5760",
]

# Telemetry refresh rates (Hz)
TELEMETRY_RATE_HZ = 4
HEARTBEAT_RATE_HZ = 1

# ELRS expected parameters (from ANALYSIS.md)
EXPECTED_PARAMS = {
    "RSSI_TYPE": 3,
    "RSSI_CHANNEL": 0,
    "SERIAL4_PROTOCOL": 23,
    "SERIAL4_BAUD": 115,
    "RC_PROTOCOLS": 512,
    "RC_OPTIONS": 8708,
    "OSD_TYPE": 5,
    "SERIAL2_PROTOCOL": 42,
    "SERIAL2_BAUD": 115,
    "OSD1_RSSI_EN": 1,
    "OSD1_LINK_Q_EN": 1,
    "RC_SPEED": 490,
    "TELEM_DELAY": 0,
}

# Parameters that MUST be changed (critical fixes)
CRITICAL_FIXES = {
    "RSSI_TYPE": {"wrong": 2, "correct": 3, "reason": "ReceiverProtocol for CRSF/ELRS telemetry"},
    "RSSI_CHANNEL": {"wrong": 15, "correct": 0, "reason": "Not needed when RSSI_TYPE=3"},
}

# ELRS link quality thresholds
ELRS_LQ_EXCELLENT = 95
ELRS_LQ_GOOD = 70
ELRS_LQ_WEAK = 40
ELRS_LQ_CRITICAL = 30

# ELRS RSSI dBm thresholds
ELRS_RSSI_EXCELLENT = -80
ELRS_RSSI_GOOD = -100
ELRS_RSSI_WEAK = -110
ELRS_RSSI_CRITICAL = -115

# Battery thresholds (per cell)
BATTERY_CELL_FULL = 4.2
BATTERY_CELL_NOMINAL = 3.7
BATTERY_CELL_LOW = 3.5
BATTERY_CELL_CRITICAL = 3.3

# Logging
LOG_DIR = "/var/log/companion"
LOG_FILE = "companion.log"
LOG_LEVEL = "INFO"

# Data recording
RECORD_TELEMETRY = True
RECORD_DIR = "/home/pi/telemetry_logs"
RECORD_INTERVAL_SEC = 1

# GPIO pins (BCM numbering)
GPIO_LED_STATUS = 17
GPIO_LED_ERROR = 27
GPIO_BUZZER = 22

# Dashboard settings
DASHBOARD_REFRESH_MS = 250
