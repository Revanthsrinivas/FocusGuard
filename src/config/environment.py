# src/config/environment.py
"""
Environment configuration with fallbacks
"""

import os
from pathlib import Path


class Environment:
    """Get configuration from environment variables"""

    @staticmethod
    def get_tesseract_path() -> str:
        """Get Tesseract path from env or default"""
        return os.environ.get(
            "TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )

    @staticmethod
    def get_data_dir() -> Path:
        """Get data directory from env or default"""
        return Path(os.environ.get("FOCUSGUARD_DATA", "data"))

    @staticmethod
    def is_debug() -> bool:
        """Check if debug mode is enabled"""
        return os.environ.get("FOCUSGUARD_DEBUG", "false").lower() == "true"
