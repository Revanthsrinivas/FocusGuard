"""
Configuration management for FocusGuard
Uses Pydantic v2 for validation and type safety
"""

from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import List
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Thresholds(BaseModel):
    """Distraction thresholds configuration"""
    low: float = Field(0.5, ge=0.0, le=1.0)
    medium: float = Field(0.7, ge=0.0, le=1.0)
    high: float = Field(0.85, ge=0.0, le=1.0)
    critical: float = Field(0.95, ge=0.0, le=1.0)

    @field_validator("medium", mode="after")
    @classmethod
    def check_medium_greater_than_low(cls, v: float, info: ValidationInfo) -> float:
        if info.data.get("low") and v <= info.data["low"]:
            raise ValueError("medium must be greater than low")
        return v

    @field_validator("high", mode="after")
    @classmethod
    def check_high_greater_than_medium(cls, v: float, info: ValidationInfo) -> float:
        if info.data.get("medium") and v <= info.data["medium"]:
            raise ValueError("high must be greater than medium")
        return v

    @field_validator("critical", mode="after")
    @classmethod
    def check_critical_greater_than_high(cls, v: float, info: ValidationInfo) -> float:
        if info.data.get("high") and v <= info.data["high"]:
            raise ValueError("critical must be greater than high")
        return v


class MonitoringConfig(BaseModel):
    """Monitoring settings"""
    capture_interval: float = Field(0.3, ge=0.1, le=5.0)
    mouse_sampling_rate: float = Field(0.5, ge=0.1, le=2.0)
    keyboard_sampling_rate: float = Field(1.0, ge=0.1, le=2.0)
    analysis_window: int = Field(30, ge=5, le=300)


class WorkPatterns(BaseModel):
    """Keyword patterns for work/distraction detection"""
    work_keywords: List[str] = [
        "code", "programming", "python", "javascript", "java", "c++",
        "document", "report", "analysis", "research", "study", "spreadsheet",
        "excel", "data", "database", "sql", "design", "figma", "photoshop",
        "writing", "article", "blog", "content", "github", "stackoverflow",
        "tutorial", "course", "lecture", "learning", "education", "academic",
        "thesis", "assignment", "homework", "project", "deadline", "work"
    ]

    distraction_keywords: List[str] = [
        "youtube", "netflix", "prime", "hotstar", "disney+", "hulu",
        "facebook", "instagram", "twitter", "reddit", "discord", "telegram",
        "whatsapp", "snapchat", "tiktok", "twitch", "spotify", "music",
        "game", "gaming", "play", "steam", "epic", "battlenet", "origin",
        "sports", "cricket", "football", "news", "entertainment", "funny",
        "memes", "comedy", "movie", "series", "anime", "cartoon"
    ]


class PrivacyConfig(BaseModel):
    """Privacy settings"""
    store_screenshots: bool = False
    store_behavior_data: bool = True
    data_retention_days: int = Field(7, ge=1, le=365)
    cloud_sync: bool = False
    encrypt_logs: bool = Field(False, description="Encrypt local log files")


class FocusGuardConfig(BaseModel):
    """Main configuration model"""
    app_name: str = "FocusGuard Pro"
    version: str = "3.0.0"
    debug_mode: bool = False

    monitoring: MonitoringConfig = MonitoringConfig()
    thresholds: Thresholds = Thresholds()
    work_patterns: WorkPatterns = WorkPatterns()
    privacy: PrivacyConfig = PrivacyConfig()

    blocked_apps: List[str] = []
    blocked_websites: List[str] = []
    productive_apps: List[str] = []
    productive_websites: List[str] = []

    @classmethod
    def load(cls, config_path: str = "config.json") -> "FocusGuardConfig":
        """Load configuration from JSON file"""
        try:
            path = Path(config_path)
            if path.exists():
                with open(path, "r") as f:
                    data = json.load(f)
                return cls.model_validate(data)
            else:
                logger.warning(f"Config file {config_path} not found, using defaults")
                return cls()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return cls()

    def save(self, config_path: str = "config.json") -> bool:
        """Save configuration to JSON file"""
        try:
            with open(config_path, "w") as f:
                json.dump(self.model_dump(), f, indent=2)
            logger.info(f"Configuration saved to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

    def validate_all(self) -> List[str]:
        """Validate all settings and return list of issues"""
        issues = []
        try:
            _ = self.model_dump()
        except Exception as e:
            issues.append(str(e))
        return issues

