#!/usr/bin/env python3
"""
Raspberry Pi Companion Computer for Cube Orange + ELRS + Walksnail.

Features:
  - MAVLink telemetry monitoring
  - ELRS link quality tracking with alerts
  - ArduPilot parameter verification and auto-fix
  - Real-time terminal dashboard
  - Flight data logging to CSV

Usage:
  python3 main.py                    # start dashboard
  python3 main.py --check-params     # verify ArduPilot parameters
  python3 main.py --fix-params       # apply critical RSSI fixes
  python3 main.py --log-only         # headless logging mode
  python3 main.py --port /dev/ttyUSB0 --baud 57600  # custom connection
"""

import argparse
import logging
import signal
import sys
import time
import threading

import config
from mavlink_manager import MAVLinkManager
from telemetry import TelemetryCollector
from elrs_monitor import ELRSMonitor
from param_manager import ParamManager
from data_logger import DataLogger
from dashboard import Dashboard


def setup_logging(level: str = config.LOG_LEVEL):
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=getattr(logging, level), format=fmt)


def parse_args():
    p = argparse.ArgumentParser(description="Raspberry Pi Companion Computer")
    p.add_argument("--port", default=None, help="MAVLink serial port or connection string")
    p.add_argument("--baud", type=int, default=config.MAVLINK_BAUD, help="Baud rate")
    p.add_argument("--check-params", action="store_true", help="Verify ArduPilot parameters and exit")
    p.add_argument("--fix-params", action="store_true", help="Apply critical RSSI fixes (RSSI_TYPE, RSSI_CHANNEL)")
    p.add_argument("--dry-run", action="store_true", help="Show what --fix-params would do without writing")
    p.add_argument("--log-only", action="store_true", help="Headless mode: log telemetry to CSV, no dashboard")
    p.add_argument("--log-dir", default=None, help="Override telemetry log directory")
    p.add_argument("--no-log", action="store_true", help="Disable CSV logging")
    p.add_argument("--refresh", type=float, default=4.0, help="Dashboard refresh rate in Hz")
    return p.parse_args()


def run_check_params(mav: MAVLinkManager):
    """Verify all parameters and print report."""
    pm = ParamManager(mav)
    pm.verify_all()
    print(pm.get_report())

    rc_info = pm.check_rc_options_bits()
    print("\nRC_OPTIONS bitmask analysis:")
    if "error" in rc_info:
        print(f"  Error: {rc_info['error']}")
    else:
        print(f"  Raw value: {rc_info['raw_value']}")
        for bit_name, val in rc_info["bits"].items():
            expected = rc_info["expected"][bit_name]
            status = "OK" if val == expected else "WRONG"
            print(f"  {bit_name}: {val} (expected: {expected}) [{status}]")
        overall = "ALL CORRECT" if rc_info["all_correct"] else "ISSUES FOUND"
        print(f"  Overall: {overall}")

    has_critical = any(not r.match and r.critical for r in pm.results)
    if has_critical:
        print("\n  Run with --fix-params to apply critical fixes.")
        print("  Run with --fix-params --dry-run to preview changes.")

    return 0 if not has_critical else 1


def run_fix_params(mav: MAVLinkManager, dry_run: bool):
    """Apply critical parameter fixes."""
    pm = ParamManager(mav)
    print("Applying critical ELRS parameter fixes...")
    if dry_run:
        print("(DRY RUN — no changes will be written)\n")

    results = pm.apply_critical_fixes(dry_run=dry_run)

    all_ok = all(success for _, success in results)
    for name, success in results:
        status = "OK" if success else "FAILED"
        print(f"  {name}: {status}")

    if all_ok and not dry_run:
        print("\nAll critical parameters applied successfully.")
        print("Reboot the autopilot for changes to take effect.")
    elif not all_ok:
        print("\nSome parameters failed to apply. Check connection and try again.")

    return 0 if all_ok else 1


def run_dashboard(mav: MAVLinkManager, args):
    """Run the real-time monitoring dashboard."""
    telem = TelemetryCollector()
    elrs = ELRSMonitor()

    telem.register(mav)

    def on_rc_update(msg):
        lq = int(msg.rssi * 100 / 254) if msg.rssi < 255 else 0
        elrs.update(lq)

    mav.subscribe("RC_CHANNELS", on_rc_update)
    mav.request_data_streams()
    mav.start()

    data_logger = None
    if not args.no_log:
        data_logger = DataLogger(telem, args.log_dir)
        data_logger.start()

        def log_loop():
            while mav.is_connected:
                if data_logger.is_recording:
                    data_logger.record()
                time.sleep(config.RECORD_INTERVAL_SEC)

        threading.Thread(target=log_loop, daemon=True).start()

    dash = Dashboard(telem, elrs)

    def shutdown(signum, frame):
        print("\nShutting down...")
        if data_logger and data_logger.is_recording:
            data_logger.stop()
        mav.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    dash.run(refresh_hz=args.refresh)


def run_headless(mav: MAVLinkManager, args):
    """Headless mode: log telemetry without dashboard."""
    telem = TelemetryCollector()
    elrs = ELRSMonitor()
    telem.register(mav)

    def on_rc_update(msg):
        lq = int(msg.rssi * 100 / 254) if msg.rssi < 255 else 0
        elrs.update(lq)

    mav.subscribe("RC_CHANNELS", on_rc_update)
    mav.request_data_streams()
    mav.start()

    data_logger = DataLogger(telem, args.log_dir)
    data_logger.start()

    print(f"Headless mode. Logging to: {data_logger.filename}")
    print("Press Ctrl+C to stop.")

    def shutdown(signum, frame):
        print("\nStopping...")
        data_logger.stop()
        mav.stop()
        print(f"Saved {data_logger.rows_written} rows.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        data_logger.record()
        if elrs.recent_alerts:
            for alert in elrs.recent_alerts[-1:]:
                print(f"[{alert.level}] {alert.message}")
        time.sleep(config.RECORD_INTERVAL_SEC)


def main():
    args = parse_args()
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Raspberry Pi Companion Computer starting...")

    mav = MAVLinkManager(connection_string=args.port, baud=args.baud)
    if not mav.connect():
        print("ERROR: Could not connect to autopilot.")
        print("Check connection and try:")
        print("  --port /dev/ttyAMA0      (GPIO UART)")
        print("  --port /dev/ttyUSB0      (USB adapter)")
        print("  --port udpin:0.0.0.0:14550  (UDP)")
        print("  --port tcp:127.0.0.1:5760   (SITL)")
        sys.exit(1)

    if args.check_params:
        code = run_check_params(mav)
        mav.stop()
        sys.exit(code)

    if args.fix_params:
        code = run_fix_params(mav, dry_run=args.dry_run)
        mav.stop()
        sys.exit(code)

    if args.log_only:
        run_headless(mav, args)
    else:
        run_dashboard(mav, args)


if __name__ == "__main__":
    main()
