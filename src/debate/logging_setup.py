from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from debate.config import LoggingConfig


class RotatingJsonlHandler(logging.Handler):
    """Structured JSONL logs: up to N files, M lines each."""

    def __init__(self, config: LoggingConfig, base_name: str = "debate") -> None:
        super().__init__()

        self._config = config
        self._base_name = f"{base_name}_pid{os.getpid()}"
        self._log_dir = Path(config.log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)

        self._file_index = 0
        self._line_count = 0
        self._current_path = self._next_path()
        self._file = self._current_path.open("a", encoding="utf-8")

    def _next_path(self) -> Path:
        path = self._log_dir / f"{self._base_name}_{self._file_index:03d}.jsonl"
        self._file_index = (self._file_index + 1) % self._config.max_files
        return path

    def _rotate_if_needed(self) -> None:
        if self._line_count < self._config.max_lines_per_file:
            return

        self._file.close()
        self._line_count = 0
        self._current_path = self._next_path()
        self._file = self._current_path.open("a", encoding="utf-8")

    def emit(self, record: logging.LogRecord) -> None:
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "pid": os.getpid(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_data"):
            entry["data"] = record.extra_data  # type: ignore[attr-defined]

        self._file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._file.flush()

        self._line_count += 1
        self._rotate_if_needed()

    def close(self) -> None:
        try:
            self._file.close()
        finally:
            super().close()


def setup_logging(config: LoggingConfig) -> logging.Logger:
    """Configure both JSONL file logs and readable terminal logs."""

    logger = logging.getLogger("debate")
    logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    logger.propagate = False

    has_json_handler = any(isinstance(h, RotatingJsonlHandler) for h in logger.handlers)
    has_console_handler = any(getattr(h, "_debate_console", False) for h in logger.handlers)

    if not has_json_handler:
        json_handler = RotatingJsonlHandler(config)
        json_handler.setLevel(getattr(logging, config.level.upper(), logging.INFO))
        logger.addHandler(json_handler)

    if not has_console_handler:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler._debate_console = True  # type: ignore[attr-defined]
        console_handler.setLevel(getattr(logging, config.level.upper(), logging.INFO))
        console_handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] pid=%(process)d %(levelname)s: %(message)s",
                "%H:%M:%S",
            )
        )
        logger.addHandler(console_handler)

    return logger