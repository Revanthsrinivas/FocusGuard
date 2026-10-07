"""
Configuration manager for FocusGuard
"""

import json
import os
from typing import Any, Dict


class ConfigManager:
    """Manages application configuration"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "app": {"name": "FocusGuard", "version": "1.0.0", "debug_mode": False},
            "monitoring": {
                "capture_interval": 2.0,
                "mouse_sampling_rate": 0.5,
                "keyboard_sampling_rate": 1.0,
                "analysis_window": 30,
            },
            "distraction_thresholds": {
                "low": 0.5,
                "medium": 0.7,
                "high": 0.85,
                "critical": 0.95,
            },
            "interventions": {
                "low_level": "notification",
                "medium_level": "gentle_blur",
                "high_level": "strong_blur",
                "critical_level": "full_block",
            },
            "work_patterns": {
                "work_keywords": [
                    "code",
                    "programming",
                    "python",
                    "javascript",
                    "java",
                    "document",
                    "report",
                    "analysis",
                    "research",
                    "spreadsheet",
                    "excel",
                    "data",
                    "database",
                ],
                "distraction_keywords": [
                    "entertainment",
                    "movie",
                    "tv",
                    "social",
                    "media",
                    "game",
                    "gaming",
                    "play",
                    "funny",
                    "meme",
                ],
            },
            "privacy": {
                "store_screenshots": False,
                "store_behavior_data": True,
                "data_retention_days": 7,
                "cloud_sync": False,
            },
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    loaded_config = json.load(f)
                    # Merge with default config
                    return self._merge_configs(default_config, loaded_config)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return default_config
        else:
            # Create config file with defaults
            self._save_config(default_config)
            return default_config

    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """Merge default and custom configurations"""
        result = default.copy()

        for key, value in custom.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation"""
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot notation"""
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        self._save_config(self.config)

    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self.config.copy()
