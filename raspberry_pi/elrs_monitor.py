"""
ELRS (ExpressLRS) link quality monitor.
Tracks RSSI, LQ, packet loss, and generates alerts.
"""

import time
import logging
from collections import deque
from dataclasses import dataclass

import config

logger = logging.getLogger(__name__)


@dataclass
class ELRSAlert:
    level: str  # INFO, WARNING, CRITICAL
    message: str
    timestamp: float


class ELRSMonitor:
    """
    Monitors ELRS link quality over time.
    Tracks history, detects degradation, and generates alerts.
    """

    HISTORY_SIZE = 300  # ~5 min at 1Hz

    def __init__(self):
        self.lq_history: deque[int] = deque(maxlen=self.HISTORY_SIZE)
        self.rssi_history: deque[int] = deque(maxlen=self.HISTORY_SIZE)
        self.alerts: deque[ELRSAlert] = deque(maxlen=50)
        self._last_lq = 100
        self._last_rssi_dbm = 0
        self._last_alert_time = 0.0
        self._failsafe_count = 0
        self._packet_loss_total = 0
        self._packets_total = 0
        self._start_time = time.time()

    def update(self, link_quality: int, rssi_dbm: int = 0):
        """Process new link quality data point."""
        now = time.time()
        self._packets_total += 1

        self.lq_history.append(link_quality)
        if rssi_dbm != 0:
            self.rssi_history.append(rssi_dbm)

        self._check_alerts(link_quality, rssi_dbm, now)

        self._last_lq = link_quality
        self._last_rssi_dbm = rssi_dbm

    def _check_alerts(self, lq: int, rssi_dbm: int, now: float):
        min_interval = 5.0
        if now - self._last_alert_time < min_interval:
            return

        if lq == 0:
            self._failsafe_count += 1
            self._add_alert("CRITICAL", f"FAILSAFE! LQ=0% (#{self._failsafe_count})", now)
        elif lq < config.ELRS_LQ_CRITICAL:
            self._add_alert("CRITICAL", f"LQ critically low: {lq}%", now)
        elif lq < config.ELRS_LQ_WEAK:
            self._add_alert("WARNING", f"LQ weak: {lq}%", now)

        if rssi_dbm < config.ELRS_RSSI_CRITICAL and rssi_dbm != 0:
            self._add_alert("CRITICAL", f"RSSI critically low: {rssi_dbm} dBm", now)
        elif rssi_dbm < config.ELRS_RSSI_WEAK and rssi_dbm != 0:
            self._add_alert("WARNING", f"RSSI weak: {rssi_dbm} dBm", now)

        if len(self.lq_history) >= 30:
            recent = list(self.lq_history)[-30:]
            avg_recent = sum(recent) / len(recent)
            older = list(self.lq_history)[-60:-30] if len(self.lq_history) >= 60 else []
            if older:
                avg_older = sum(older) / len(older)
                drop = avg_older - avg_recent
                if drop > 20:
                    self._add_alert("WARNING", f"Rapid LQ degradation: -{drop:.0f}% in 30s", now)

    def _add_alert(self, level: str, message: str, now: float):
        alert = ELRSAlert(level=level, message=message, timestamp=now)
        self.alerts.append(alert)
        self._last_alert_time = now

        if level == "CRITICAL":
            logger.critical("ELRS: %s", message)
        elif level == "WARNING":
            logger.warning("ELRS: %s", message)
        else:
            logger.info("ELRS: %s", message)

    @property
    def avg_lq(self) -> float:
        if not self.lq_history:
            return 0.0
        return sum(self.lq_history) / len(self.lq_history)

    @property
    def min_lq(self) -> int:
        return min(self.lq_history) if self.lq_history else 0

    @property
    def max_lq(self) -> int:
        return max(self.lq_history) if self.lq_history else 0

    @property
    def avg_rssi_dbm(self) -> float:
        if not self.rssi_history:
            return 0.0
        return sum(self.rssi_history) / len(self.rssi_history)

    @property
    def packet_loss_pct(self) -> float:
        """Estimate packet loss from average LQ (LQ represents % of packets received)."""
        if not self.lq_history:
            return 0.0
        return max(0.0, 100.0 - self.avg_lq)

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._start_time

    @property
    def recent_alerts(self) -> list[ELRSAlert]:
        """Get alerts from the last 60 seconds."""
        cutoff = time.time() - 60
        return [a for a in self.alerts if a.timestamp > cutoff]

    def get_status_summary(self) -> dict:
        return {
            "current_lq": self._last_lq,
            "avg_lq": round(self.avg_lq, 1),
            "min_lq": self.min_lq,
            "max_lq": self.max_lq,
            "current_rssi_dbm": self._last_rssi_dbm,
            "avg_rssi_dbm": round(self.avg_rssi_dbm, 1),
            "packet_loss_pct": round(self.packet_loss_pct, 2),
            "failsafe_count": self._failsafe_count,
            "uptime_sec": round(self.uptime_seconds),
            "active_alerts": len(self.recent_alerts),
            "lq_status": self._lq_status_text(self._last_lq),
        }

    @staticmethod
    def _lq_status_text(lq: int) -> str:
        if lq >= config.ELRS_LQ_EXCELLENT:
            return "EXCELLENT"
        if lq >= config.ELRS_LQ_GOOD:
            return "GOOD"
        if lq >= config.ELRS_LQ_WEAK:
            return "WEAK"
        if lq >= config.ELRS_LQ_CRITICAL:
            return "CRITICAL"
        return "LOST"
