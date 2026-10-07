# src/utils/logger.py
"""
Professional logging setup for FocusGuard
"""

import json
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class FocusGuardLogger:
    """Centralized logging for FocusGuard"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger("FocusGuard")
        self.logger.setLevel(logging.DEBUG)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%H:%M:%S",
            )
        )

        # Ensure utf-8 logging supports emoji characters in Windows console
        try:
            console.setStream(
                open(console.stream.fileno(), "w", encoding="utf-8", buffering=1)
            )
        except Exception:
            pass

        self.logger.addHandler(console)

        log_file = self.log_dir / f"focusguard_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10485760, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)

    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, extra=kwargs)

    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra=kwargs)

    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, extra=kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log error message."""
        exc_info = kwargs.pop('exc_info', False) if 'exc_info' in kwargs else False
        self.logger.error(msg, *args, exc_info=exc_info, **kwargs)

    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, extra=kwargs)

    def log_activity(self, action: str, details: Optional[Dict[str, Any]] = None):
        activity = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details or {},
        }

        activity_file = self.log_dir / "activity.json"
        activities = []

        if activity_file.exists():
            with open(activity_file, "r") as f:
                try:
                    activities = json.load(f)
                except Exception as e:
                    print(f"Warning: Failed to load activity log: {e}")
                    activities = []

        activities.append(activity)

        if len(activities) > 1000:
            activities = activities[-1000:]

        with open(activity_file, "w") as f:
            json.dump(activities, f, indent=2)

        self.info(f"Activity: {action}", details=details)


logger = FocusGuardLogger()
