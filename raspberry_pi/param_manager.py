"""
ArduPilot parameter verification and management.
Checks current parameters against expected values for ELRS + Walksnail setup.
"""

import time
import logging
from dataclasses import dataclass
from typing import Optional

import config
from mavlink_manager import MAVLinkManager

logger = logging.getLogger(__name__)


@dataclass
class ParamCheckResult:
    name: str
    expected: float
    actual: Optional[float]
    match: bool
    critical: bool
    note: str


class ParamManager:
    """Verify and manage ArduPilot parameters for Cube Orange + ELRS + Walksnail."""

    def __init__(self, mav: MAVLinkManager):
        self.mav = mav
        self.results: list[ParamCheckResult] = []
        self._all_params: dict[str, float] = {}

    def verify_all(self) -> list[ParamCheckResult]:
        """Check all expected parameters against actual autopilot values."""
        self.results.clear()
        logger.info("Starting parameter verification...")

        for name, expected in config.EXPECTED_PARAMS.items():
            actual = self.mav.get_param(name, timeout=3)
            is_critical = name in config.CRITICAL_FIXES

            if actual is None:
                result = ParamCheckResult(
                    name=name, expected=expected, actual=None,
                    match=False, critical=is_critical, note="FAILED TO READ",
                )
            elif abs(actual - expected) < 0.01:
                result = ParamCheckResult(
                    name=name, expected=expected, actual=actual,
                    match=True, critical=is_critical, note="OK",
                )
            else:
                note = ""
                if is_critical:
                    fix_info = config.CRITICAL_FIXES[name]
                    note = f"NEEDS FIX: {fix_info['reason']}"
                else:
                    note = "MISMATCH (non-critical)"

                result = ParamCheckResult(
                    name=name, expected=expected, actual=actual,
                    match=False, critical=is_critical, note=note,
                )

            self.results.append(result)
            status = "OK" if result.match else "FAIL"
            logger.info(
                "  [%s] %s: expected=%s actual=%s %s",
                status, name, expected, actual, result.note,
            )

        return self.results

    def apply_critical_fixes(self, dry_run: bool = True) -> list[tuple[str, bool]]:
        """
        Apply critical parameter fixes (RSSI_TYPE and RSSI_CHANNEL).
        Set dry_run=False to actually write parameters.
        """
        applied = []
        for name, fix_info in config.CRITICAL_FIXES.items():
            current = self.mav.get_param(name, timeout=3)
            if current is None:
                logger.error("Cannot read %s, skipping", name)
                applied.append((name, False))
                continue

            if abs(current - fix_info["correct"]) < 0.01:
                logger.info("%s already correct (%s)", name, current)
                applied.append((name, True))
                continue

            if dry_run:
                logger.info(
                    "[DRY RUN] Would change %s from %s to %s (%s)",
                    name, current, fix_info["correct"], fix_info["reason"],
                )
                applied.append((name, True))
            else:
                logger.warning(
                    "Changing %s from %s to %s (%s)",
                    name, current, fix_info["correct"], fix_info["reason"],
                )
                success = self.mav.set_param(name, fix_info["correct"])
                applied.append((name, success))
                if success:
                    logger.info("%s successfully changed to %s", name, fix_info["correct"])
                else:
                    logger.error("FAILED to change %s", name)

        return applied

    def get_report(self) -> str:
        """Generate a human-readable verification report."""
        lines = [
            "=" * 60,
            "  PARAMETER VERIFICATION REPORT",
            "  Cube Orange + ELRS + Walksnail",
            "=" * 60,
            "",
        ]

        ok_count = sum(1 for r in self.results if r.match)
        fail_count = sum(1 for r in self.results if not r.match)
        crit_count = sum(1 for r in self.results if not r.match and r.critical)

        lines.append(f"  Total: {len(self.results)} | OK: {ok_count} | Failed: {fail_count} | Critical: {crit_count}")
        lines.append("")

        if crit_count > 0:
            lines.append("  CRITICAL ISSUES:")
            lines.append("  " + "-" * 40)
            for r in self.results:
                if not r.match and r.critical:
                    lines.append(f"  ! {r.name}: is {r.actual}, should be {r.expected}")
                    lines.append(f"    Reason: {r.note}")
            lines.append("")

        lines.append("  ALL PARAMETERS:")
        lines.append("  " + "-" * 40)
        lines.append(f"  {'Parameter':<25} {'Expected':>8} {'Actual':>8} {'Status':>8}")
        lines.append("  " + "-" * 40)

        for r in self.results:
            status = "OK" if r.match else ("CRIT!" if r.critical else "WARN")
            actual_str = f"{r.actual:.0f}" if r.actual is not None else "N/A"
            lines.append(f"  {r.name:<25} {r.expected:>8.0f} {actual_str:>8} {status:>8}")

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    def check_rc_options_bits(self) -> dict:
        """Decode and verify RC_OPTIONS bitmask."""
        val = self.mav.get_param("RC_OPTIONS", timeout=3)
        if val is None:
            return {"error": "Cannot read RC_OPTIONS"}

        rc_opt = int(val)
        bits = {
            "bit2_ignore_failsafe": bool(rc_opt & 4),
            "bit9_suppress_crsf": bool(rc_opt & 512),
            "bit13_420k_baud": bool(rc_opt & 8192),
        }
        expected_bits = {
            "bit2_ignore_failsafe": True,
            "bit9_suppress_crsf": True,
            "bit13_420k_baud": True,
        }

        result = {
            "raw_value": rc_opt,
            "bits": bits,
            "expected": expected_bits,
            "all_correct": bits == expected_bits,
        }
        return result
