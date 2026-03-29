"""
Telemetry data collector and processor.
Captures RSSI, LQ, GPS, battery, attitude, and RC channels from ArduPilot.
"""

import time
import math
import logging
from dataclasses import dataclass, field
from typing import Optional

import config

logger = logging.getLogger(__name__)


@dataclass
class GPSData:
    fix_type: int = 0
    satellites: int = 0
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_msl: float = 0.0
    altitude_rel: float = 0.0
    groundspeed: float = 0.0
    heading: float = 0.0
    hdop: float = 99.9
    vdop: float = 99.9
    updated_at: float = 0.0

    @property
    def fix_type_name(self) -> str:
        names = {0: "No GPS", 1: "No Fix", 2: "2D", 3: "3D", 4: "DGPS", 5: "RTK Float", 6: "RTK Fixed"}
        return names.get(self.fix_type, f"Unknown({self.fix_type})")

    @property
    def has_fix(self) -> bool:
        return self.fix_type >= 3


@dataclass
class BatteryData:
    voltage: float = 0.0
    current: float = 0.0
    remaining_pct: int = -1
    consumed_mah: float = 0.0
    cell_count: int = 0
    updated_at: float = 0.0

    @property
    def voltage_per_cell(self) -> float:
        if self.cell_count > 0:
            return self.voltage / self.cell_count
        return 0.0

    @property
    def cell_status(self) -> str:
        vpc = self.voltage_per_cell
        if vpc <= 0:
            return "UNKNOWN"
        if vpc >= config.BATTERY_CELL_NOMINAL:
            return "OK"
        if vpc >= config.BATTERY_CELL_LOW:
            return "LOW"
        if vpc >= config.BATTERY_CELL_CRITICAL:
            return "CRITICAL"
        return "DANGER"

    def estimate_cell_count(self):
        """Auto-detect number of cells from voltage."""
        if self.voltage > 0:
            self.cell_count = max(1, round(self.voltage / config.BATTERY_CELL_NOMINAL))


@dataclass
class AttitudeData:
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    rollspeed: float = 0.0
    pitchspeed: float = 0.0
    yawspeed: float = 0.0
    updated_at: float = 0.0

    @property
    def roll_deg(self) -> float:
        return math.degrees(self.roll)

    @property
    def pitch_deg(self) -> float:
        return math.degrees(self.pitch)

    @property
    def yaw_deg(self) -> float:
        return math.degrees(self.yaw) % 360


@dataclass
class LinkData:
    rssi: int = 0
    remrssi: int = 0
    rssi_dbm: int = 0
    noise: int = 0
    remnoise: int = 0
    link_quality: int = 0
    rc_channels: list = field(default_factory=lambda: [0] * 16)
    rc_rssi: int = 0
    updated_at: float = 0.0

    @property
    def lq_status(self) -> str:
        lq = self.link_quality
        if lq >= config.ELRS_LQ_EXCELLENT:
            return "EXCELLENT"
        if lq >= config.ELRS_LQ_GOOD:
            return "GOOD"
        if lq >= config.ELRS_LQ_WEAK:
            return "WEAK"
        if lq >= config.ELRS_LQ_CRITICAL:
            return "CRITICAL"
        return "LOST"

    @property
    def rssi_dbm_status(self) -> str:
        rssi = self.rssi_dbm
        if rssi == 0:
            return "N/A"
        if rssi >= config.ELRS_RSSI_EXCELLENT:
            return "EXCELLENT"
        if rssi >= config.ELRS_RSSI_GOOD:
            return "GOOD"
        if rssi >= config.ELRS_RSSI_WEAK:
            return "WEAK"
        return "CRITICAL"


@dataclass
class FlightMode:
    mode_number: int = 0
    mode_name: str = "UNKNOWN"
    armed: bool = False
    updated_at: float = 0.0


@dataclass
class SystemStatus:
    cpu_load: int = 0
    voltage_board: float = 0.0
    errors_count: int = 0
    uptime_sec: int = 0
    updated_at: float = 0.0


class TelemetryCollector:
    """Collects and stores telemetry data from MAVLink messages."""

    COPTER_MODES = {
        0: "STABILIZE", 1: "ACRO", 2: "ALT_HOLD", 3: "AUTO",
        4: "GUIDED", 5: "LOITER", 6: "RTL", 7: "CIRCLE",
        9: "LAND", 11: "DRIFT", 13: "SPORT", 14: "FLIP",
        15: "AUTOTUNE", 16: "POSHOLD", 17: "BRAKE", 18: "THROW",
        19: "AVOID_ADSB", 20: "GUIDED_NOGPS", 21: "SMART_RTL",
        22: "FLOWHOLD", 23: "FOLLOW", 24: "ZIGZAG", 25: "SYSTEMID",
        26: "AUTOROTATE", 27: "AUTO_RTL",
    }

    def __init__(self):
        self.gps = GPSData()
        self.battery = BatteryData()
        self.attitude = AttitudeData()
        self.link = LinkData()
        self.mode = FlightMode()
        self.system = SystemStatus()
        self.home_lat: float = 0.0
        self.home_lon: float = 0.0
        self.home_alt: float = 0.0
        self._home_set = False

    def register(self, mav_manager):
        """Register all message handlers with the MAVLink manager."""
        mav_manager.subscribe("GPS_RAW_INT", self._on_gps_raw)
        mav_manager.subscribe("GLOBAL_POSITION_INT", self._on_global_position)
        mav_manager.subscribe("SYS_STATUS", self._on_sys_status)
        mav_manager.subscribe("BATTERY_STATUS", self._on_battery_status)
        mav_manager.subscribe("ATTITUDE", self._on_attitude)
        mav_manager.subscribe("RC_CHANNELS", self._on_rc_channels)
        mav_manager.subscribe("HEARTBEAT", self._on_heartbeat)
        mav_manager.subscribe("VFR_HUD", self._on_vfr_hud)
        mav_manager.subscribe("RADIO_STATUS", self._on_radio_status)
        mav_manager.subscribe("HOME_POSITION", self._on_home_position)

    def _on_gps_raw(self, msg):
        self.gps.fix_type = msg.fix_type
        self.gps.satellites = msg.satellites_visible
        self.gps.latitude = msg.lat / 1e7
        self.gps.longitude = msg.lon / 1e7
        self.gps.altitude_msl = msg.alt / 1000.0
        self.gps.hdop = msg.eph / 100.0 if msg.eph != 65535 else 99.9
        self.gps.vdop = msg.epv / 100.0 if msg.epv != 65535 else 99.9
        self.gps.updated_at = time.time()

    def _on_global_position(self, msg):
        self.gps.altitude_rel = msg.relative_alt / 1000.0
        self.gps.heading = msg.hdg / 100.0 if msg.hdg != 65535 else 0
        self.gps.groundspeed = math.sqrt(msg.vx**2 + msg.vy**2) / 100.0

    def _on_sys_status(self, msg):
        self.battery.voltage = msg.voltage_battery / 1000.0
        self.battery.current = msg.current_battery / 100.0
        self.battery.remaining_pct = msg.battery_remaining
        if self.battery.cell_count == 0 and self.battery.voltage > 0:
            self.battery.estimate_cell_count()
        self.battery.updated_at = time.time()

        self.system.cpu_load = msg.load / 10.0
        self.system.errors_count = (
            msg.errors_count1 + msg.errors_count2 + msg.errors_count3 + msg.errors_count4
        )
        self.system.updated_at = time.time()

    def _on_battery_status(self, msg):
        self.battery.consumed_mah = msg.current_consumed
        self.battery.updated_at = time.time()

    def _on_attitude(self, msg):
        self.attitude.roll = msg.roll
        self.attitude.pitch = msg.pitch
        self.attitude.yaw = msg.yaw
        self.attitude.rollspeed = msg.rollspeed
        self.attitude.pitchspeed = msg.pitchspeed
        self.attitude.yawspeed = msg.yawspeed
        self.attitude.updated_at = time.time()

    def _on_rc_channels(self, msg):
        self.link.rc_channels = [
            msg.chan1_raw, msg.chan2_raw, msg.chan3_raw, msg.chan4_raw,
            msg.chan5_raw, msg.chan6_raw, msg.chan7_raw, msg.chan8_raw,
            msg.chan9_raw, msg.chan10_raw, msg.chan11_raw, msg.chan12_raw,
            msg.chan13_raw, msg.chan14_raw, msg.chan15_raw, msg.chan16_raw,
        ]
        self.link.rc_rssi = msg.rssi
        self.link.link_quality = int(msg.rssi * 100 / 254) if msg.rssi < 255 else 0
        self.link.updated_at = time.time()

    def _on_heartbeat(self, msg):
        if msg.get_srcSystem() == 0:
            return
        self.mode.mode_number = msg.custom_mode
        self.mode.mode_name = self.COPTER_MODES.get(msg.custom_mode, f"MODE_{msg.custom_mode}")
        self.mode.armed = (msg.base_mode & 0x80) != 0
        self.mode.updated_at = time.time()

    def _on_vfr_hud(self, msg):
        self.gps.groundspeed = msg.groundspeed
        self.gps.heading = msg.heading
        self.gps.altitude_rel = msg.alt

    def _on_radio_status(self, msg):
        self.link.rssi = msg.rssi
        self.link.remrssi = msg.remrssi
        self.link.noise = msg.noise
        self.link.remnoise = msg.remnoise
        self.link.updated_at = time.time()

    def _on_home_position(self, msg):
        self.home_lat = msg.latitude / 1e7
        self.home_lon = msg.longitude / 1e7
        self.home_alt = msg.altitude / 1000.0
        self._home_set = True

    @property
    def distance_to_home(self) -> float:
        """Calculate distance to home in meters using Haversine formula."""
        if not self._home_set or not self.gps.has_fix:
            return 0.0
        R = 6371000
        lat1, lat2 = math.radians(self.home_lat), math.radians(self.gps.latitude)
        dlat = lat2 - lat1
        dlon = math.radians(self.gps.longitude - self.home_lon)
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def to_dict(self) -> dict:
        """Export all telemetry as a flat dictionary for logging/display."""
        return {
            "timestamp": time.time(),
            "gps_fix": self.gps.fix_type_name,
            "gps_sats": self.gps.satellites,
            "lat": self.gps.latitude,
            "lon": self.gps.longitude,
            "alt_msl": self.gps.altitude_msl,
            "alt_rel": self.gps.altitude_rel,
            "groundspeed": self.gps.groundspeed,
            "heading": self.gps.heading,
            "hdop": self.gps.hdop,
            "batt_v": self.battery.voltage,
            "batt_a": self.battery.current,
            "batt_pct": self.battery.remaining_pct,
            "batt_mah": self.battery.consumed_mah,
            "batt_cells": self.battery.cell_count,
            "batt_vpc": self.battery.voltage_per_cell,
            "roll": self.attitude.roll_deg,
            "pitch": self.attitude.pitch_deg,
            "yaw": self.attitude.yaw_deg,
            "rssi": self.link.rssi,
            "lq": self.link.link_quality,
            "lq_status": self.link.lq_status,
            "rc_rssi": self.link.rc_rssi,
            "mode": self.mode.mode_name,
            "armed": self.mode.armed,
            "dist_home": self.distance_to_home,
            "cpu_load": self.system.cpu_load,
        }
