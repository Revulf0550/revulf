"""
Terminal-based real-time telemetry dashboard.
Displays flight data, ELRS link quality, battery status, and alerts.
"""

import os
import time
import sys
from typing import Optional

from telemetry import TelemetryCollector
from elrs_monitor import ELRSMonitor
import config


def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")


def color(text: str, code: str) -> str:
    """ANSI color wrapper."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "reset": "\033[0m",
    }
    return f"{colors.get(code, '')}{text}\033[0m"


def lq_color(lq: int) -> str:
    if lq >= config.ELRS_LQ_EXCELLENT:
        return "green"
    if lq >= config.ELRS_LQ_GOOD:
        return "cyan"
    if lq >= config.ELRS_LQ_WEAK:
        return "yellow"
    return "red"


def batt_color(vpc: float) -> str:
    if vpc >= config.BATTERY_CELL_NOMINAL:
        return "green"
    if vpc >= config.BATTERY_CELL_LOW:
        return "yellow"
    return "red"


def bar(value: float, max_val: float, width: int = 20, fill: str = "█", empty: str = "░") -> str:
    ratio = max(0, min(1, value / max_val)) if max_val > 0 else 0
    filled = int(ratio * width)
    return fill * filled + empty * (width - filled)


class Dashboard:
    """Terminal dashboard for drone telemetry."""

    def __init__(self, telemetry: TelemetryCollector, elrs: ELRSMonitor):
        self.telem = telemetry
        self.elrs = elrs
        self._frame = 0

    def render(self):
        """Render one frame of the dashboard."""
        clear_screen()
        self._frame += 1

        t = self.telem
        e = self.elrs
        lines = []

        lines.append(color("╔══════════════════════════════════════════════════════════════╗", "cyan"))
        lines.append(color("║", "cyan") + color("   COMPANION COMPUTER — Cube Orange + ELRS + Walksnail    ", "bold") + color("║", "cyan"))
        lines.append(color("╚══════════════════════════════════════════════════════════════╝", "cyan"))
        lines.append("")

        # Flight mode & arm status
        armed_txt = color(" ARMED ", "red") if t.mode.armed else color("DISARMED", "green")
        mode_txt = color(t.mode.mode_name, "yellow")
        lines.append(f"  Mode: {mode_txt}  |  Status: {armed_txt}")
        lines.append("")

        # ELRS Link Quality
        lq = t.link.link_quality
        lq_c = lq_color(lq)
        lq_bar = bar(lq, 100, 20)
        lines.append(color("  ── ELRS Link ──────────────────────────────────", "dim"))
        lines.append(f"  LQ:      {color(f'{lq:3d}%', lq_c)}  {lq_bar}  [{color(t.link.lq_status, lq_c)}]")
        lines.append(f"  RSSI:    {t.link.rssi:3d}/254  |  RC RSSI: {t.link.rc_rssi}")

        elrs_status = e.get_status_summary()
        lines.append(f"  Avg LQ:  {elrs_status['avg_lq']:5.1f}%  |  Min: {elrs_status['min_lq']}%  |  Max: {elrs_status['max_lq']}%")
        lines.append(f"  PktLoss: {elrs_status['packet_loss_pct']:5.2f}%  |  Failsafes: {elrs_status['failsafe_count']}")
        lines.append("")

        # GPS
        lines.append(color("  ── GPS ────────────────────────────────────────", "dim"))
        fix_c = "green" if t.gps.has_fix else "red"
        lines.append(
            f"  Fix: {color(t.gps.fix_type_name, fix_c)}  |  Sats: {color(str(t.gps.satellites), fix_c)}"
            f"  |  HDOP: {t.gps.hdop:.1f}"
        )
        lines.append(f"  Lat: {t.gps.latitude:11.7f}  |  Lon: {t.gps.longitude:12.7f}")
        lines.append(f"  Alt MSL: {t.gps.altitude_msl:7.1f}m  |  Alt REL: {t.gps.altitude_rel:7.1f}m")
        lines.append(f"  Speed:   {t.gps.groundspeed:5.1f} m/s  |  Heading: {t.gps.heading:5.1f}°")
        lines.append(f"  Home:    {t.distance_to_home:7.0f}m")
        lines.append("")

        # Battery
        lines.append(color("  ── Battery ────────────────────────────────────", "dim"))
        vpc = t.battery.voltage_per_cell
        bc = batt_color(vpc)
        batt_bar = bar(vpc - 3.0, 1.2, 20)
        lines.append(
            f"  Voltage: {color(f'{t.battery.voltage:5.1f}V', bc)}"
            f"  ({t.battery.cell_count}S, {color(f'{vpc:.2f}V/cell', bc)})"
            f"  {batt_bar}"
        )
        pct = t.battery.remaining_pct if t.battery.remaining_pct >= 0 else 0
        lines.append(f"  Current: {t.battery.current:5.1f}A  |  Remaining: {pct}%")
        lines.append(f"  Used:    {t.battery.consumed_mah:5.0f} mAh  |  Status: {color(t.battery.cell_status, bc)}")
        lines.append("")

        # Attitude
        lines.append(color("  ── Attitude ───────────────────────────────────", "dim"))
        lines.append(
            f"  Roll: {t.attitude.roll_deg:+7.1f}°  |  Pitch: {t.attitude.pitch_deg:+7.1f}°"
            f"  |  Yaw: {t.attitude.yaw_deg:5.1f}°"
        )
        lines.append("")

        # RC Channels (first 8)
        lines.append(color("  ── RC Channels ────────────────────────────────", "dim"))
        ch = t.link.rc_channels
        ch_names = ["Roll", " Ptch", " Thr", " Yaw", " CH5", " CH6", " CH7", " CH8"]
        line1 = "  "
        for i in range(min(8, len(ch))):
            line1 += f"{ch_names[i]}:{ch[i]:4d}  "
        lines.append(line1)
        lines.append("")

        # System
        lines.append(color("  ── System ─────────────────────────────────────", "dim"))
        lines.append(
            f"  CPU: {t.system.cpu_load:4.1f}%  |  Errors: {t.system.errors_count}"
            f"  |  Uptime: {elrs_status['uptime_sec']}s"
        )
        lines.append("")

        # Alerts
        recent = e.recent_alerts
        if recent:
            lines.append(color("  ── Alerts ─────────────────────────────────────", "red"))
            for alert in recent[-5:]:
                ac = "red" if alert.level == "CRITICAL" else "yellow"
                ts = time.strftime("%H:%M:%S", time.localtime(alert.timestamp))
                lines.append(f"  {color(f'[{alert.level}]', ac)} {ts} {alert.message}")
            lines.append("")

        lines.append(color(f"  Frame: {self._frame}  |  Press Ctrl+C to exit", "dim"))

        print("\n".join(lines))

    def run(self, refresh_hz: float = 4):
        """Main dashboard loop."""
        interval = 1.0 / refresh_hz
        try:
            while True:
                self.render()
                time.sleep(interval)
        except KeyboardInterrupt:
            clear_screen()
            print("Dashboard stopped.")
