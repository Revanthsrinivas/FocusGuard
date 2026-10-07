# src/utils/json_storage.py
"""
Safe JSON storage with error handling
"""

import json
from pathlib import Path
from typing import Any, Optional

from src.utils.logger import logger


class JSONStorage:
    """Safe JSON file operations"""

    @staticmethod
    def load(file_path: Path, default: Any = None) -> Any:
        """Load JSON with error handling"""
        if not file_path.exists():
            return default

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            # Backup corrupted file
            backup = file_path.with_suffix(".json.corrupt")
            file_path.rename(backup)
            logger.info(f"Backed up corrupted file to {backup}")
            return default
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return default

    @staticmethod
    def save(file_path: Path, data: Any, indent: int = 2) -> bool:
        """Save JSON with error handling"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save {file_path}: {e}")
            return False

    @staticmethod
    def append_line(file_path: Path, data: Any) -> bool:
        """Append JSON line to file (for streaming)"""
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data) + "\n")
            return True
        except Exception as e:
            logger.error(f"Failed to append to {file_path}: {e}")
            return False
