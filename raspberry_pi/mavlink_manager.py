"""
MAVLink connection manager for Cube Orange autopilot.
Handles connection, heartbeats, and message routing.
"""

import time
import threading
import logging
from typing import Optional, Callable

from pymavlink import mavutil

import config

logger = logging.getLogger(__name__)


class MAVLinkManager:
    """Manages MAVLink connection to the autopilot."""

    def __init__(self, connection_string: Optional[str] = None, baud: int = config.MAVLINK_BAUD):
        self.connection_string = connection_string or config.MAVLINK_CONNECTION
        self.baud = baud
        self.conn: Optional[mavutil.mavlink_connection] = None
        self._running = False
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._listeners: dict[str, list[Callable]] = {}
        self._last_heartbeat = 0.0
        self._connected = False

    def connect(self) -> bool:
        """Establish MAVLink connection, trying fallback ports if needed."""
        ports = [self.connection_string] + config.MAVLINK_FALLBACK
        for port in ports:
            try:
                logger.info("Connecting to %s at %d baud...", port, self.baud)
                self.conn = mavutil.mavlink_connection(
                    port,
                    baud=self.baud,
                    source_system=config.MAVLINK_SOURCE_SYSTEM,
                    source_component=config.MAVLINK_SOURCE_COMPONENT,
                )
                logger.info("Waiting for heartbeat...")
                hb = self.conn.wait_heartbeat(timeout=10)
                if hb:
                    self._connected = True
                    logger.info(
                        "Connected to system %d component %d (type=%d autopilot=%d)",
                        self.conn.target_system,
                        self.conn.target_component,
                        hb.type,
                        hb.autopilot,
                    )
                    return True
            except Exception as e:
                logger.warning("Failed to connect on %s: %s", port, e)
                continue

        logger.error("Could not connect to autopilot on any port")
        return False

    @property
    def is_connected(self) -> bool:
        return self._connected and self.conn is not None

    def start(self):
        """Start background heartbeat and message receive loops."""
        if not self.is_connected:
            raise RuntimeError("Not connected. Call connect() first.")

        self._running = True
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

        recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
        recv_thread.start()

    def stop(self):
        """Stop background threads."""
        self._running = False
        if self.conn:
            self.conn.close()
            self._connected = False

    def subscribe(self, msg_type: str, callback: Callable):
        """Register a callback for a specific MAVLink message type."""
        self._listeners.setdefault(msg_type, []).append(callback)

    def request_data_streams(self, rate_hz: int = config.TELEMETRY_RATE_HZ):
        """Request specific data streams from the autopilot."""
        if not self.conn:
            return

        streams = [
            mavutil.mavlink.MAV_DATA_STREAM_RAW_SENSORS,
            mavutil.mavlink.MAV_DATA_STREAM_EXTENDED_STATUS,
            mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS,
            mavutil.mavlink.MAV_DATA_STREAM_POSITION,
            mavutil.mavlink.MAV_DATA_STREAM_EXTRA1,
            mavutil.mavlink.MAV_DATA_STREAM_EXTRA2,
            mavutil.mavlink.MAV_DATA_STREAM_EXTRA3,
        ]
        for stream_id in streams:
            self.conn.mav.request_data_stream_send(
                self.conn.target_system,
                self.conn.target_component,
                stream_id,
                rate_hz,
                1,
            )
        logger.info("Requested data streams at %d Hz", rate_hz)

    def get_param(self, param_name: str, timeout: float = 5.0) -> Optional[float]:
        """Read a single parameter value from the autopilot."""
        if not self.conn:
            return None

        self.conn.mav.param_request_read_send(
            self.conn.target_system,
            self.conn.target_component,
            param_name.encode("utf-8"),
            -1,
        )

        start = time.time()
        while time.time() - start < timeout:
            msg = self.conn.recv_match(type="PARAM_VALUE", blocking=True, timeout=1)
            if msg and msg.param_id.rstrip("\x00") == param_name:
                return msg.param_value
        return None

    def set_param(self, param_name: str, value: float, timeout: float = 5.0) -> bool:
        """Write a parameter value to the autopilot."""
        if not self.conn:
            return False

        self.conn.mav.param_set_send(
            self.conn.target_system,
            self.conn.target_component,
            param_name.encode("utf-8"),
            value,
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32,
        )

        start = time.time()
        while time.time() - start < timeout:
            msg = self.conn.recv_match(type="PARAM_VALUE", blocking=True, timeout=1)
            if msg and msg.param_id.rstrip("\x00") == param_name:
                if abs(msg.param_value - value) < 0.01:
                    logger.info("Parameter %s set to %s", param_name, value)
                    return True
        logger.error("Failed to set parameter %s to %s", param_name, value)
        return False

    def _heartbeat_loop(self):
        interval = 1.0 / config.HEARTBEAT_RATE_HZ
        while self._running:
            if self.conn:
                self.conn.mav.heartbeat_send(
                    mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
                    mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                    0, 0, 0,
                )
            time.sleep(interval)

    def _receive_loop(self):
        while self._running:
            if not self.conn:
                time.sleep(0.1)
                continue
            try:
                msg = self.conn.recv_match(blocking=True, timeout=1)
                if msg is None:
                    continue

                msg_type = msg.get_type()
                if msg_type == "HEARTBEAT":
                    self._last_heartbeat = time.time()

                for callback in self._listeners.get(msg_type, []):
                    try:
                        callback(msg)
                    except Exception as e:
                        logger.error("Listener error for %s: %s", msg_type, e)

            except Exception as e:
                logger.error("Receive error: %s", e)
                time.sleep(0.1)

    @property
    def seconds_since_heartbeat(self) -> float:
        if self._last_heartbeat == 0:
            return float("inf")
        return time.time() - self._last_heartbeat
