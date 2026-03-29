"""
Telemetry data logger — records flight data to CSV files.
"""

import os
import csv
import time
import logging
from pathlib import Path
from typing import Optional

import config
from telemetry import TelemetryCollector

logger = logging.getLogger(__name__)


class DataLogger:
    """Logs telemetry data to CSV files for post-flight analysis."""

    def __init__(self, telemetry: TelemetryCollector, output_dir: Optional[str] = None):
        self.telem = telemetry
        self.output_dir = Path(output_dir or config.RECORD_DIR)
        self._writer: Optional[csv.DictWriter] = None
        self._file = None
        self._filename = ""
        self._rows_written = 0

    def start(self):
        """Create a new log file and start recording."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self._filename = str(self.output_dir / f"flight_{timestamp}.csv")

        sample = self.telem.to_dict()
        self._file = open(self._filename, "w", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=sample.keys())
        self._writer.writeheader()
        self._rows_written = 0

        logger.info("Logging telemetry to %s", self._filename)

    def record(self):
        """Write one row of telemetry data."""
        if not self._writer or not self._file:
            return
        try:
            data = self.telem.to_dict()
            self._writer.writerow(data)
            self._rows_written += 1
            if self._rows_written % 60 == 0:
                self._file.flush()
        except Exception as e:
            logger.error("Error writing telemetry log: %s", e)

    def stop(self):
        """Close the log file."""
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None
            self._writer = None
            logger.info("Telemetry log closed: %s (%d rows)", self._filename, self._rows_written)

    @property
    def is_recording(self) -> bool:
        return self._file is not None and not self._file.closed

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def rows_written(self) -> int:
        return self._rows_written
