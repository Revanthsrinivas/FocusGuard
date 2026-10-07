# src/core/blocker.py
"""
Professional distraction blocker with auto-blocking and whitelist
"""

import json
import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import psutil

from src.utils.logger import logger


class SmartBlocker:
    """Advanced distraction blocker with learning capabilities"""

    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.blocklist = self.config.get("blocklist", [])
        self.whitelist = self.config.get(
            "whitelist",
            [
                "vscode.exe",
                "code.exe",
                "python.exe",
                "pycharm.exe",
                "excel.exe",
                "word.exe",
                "outlook.exe",
                "slack.exe",
                "teams.exe",
                "zoom.exe",
                "notion.exe",
            ],
        )
        self.block_threshold = self.config.get("block_threshold", 30)
        self.recovery_threshold = self.config.get("recovery_threshold", 50)
        self.blocks_today = 0
        self.blocks_total = 0
        self.last_block_time = None
        self._load_stats()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration"""
        if Path(config_path).exists():
            with open(config_path, "r") as f:
                return json.load(f)
        return {}

    def _load_stats(self):
        """Load block statistics"""
        stats_file = Path("data/blocks.json")
        if stats_file.exists():
            with open(stats_file, "r") as f:
                data = json.load(f)
                self.blocks_today = data.get("blocks_today", 0)
                self.blocks_total = data.get("blocks_total", 0)

    def _save_stats(self):
        """Save block statistics"""
        stats_file = Path("data/blocks.json")
        stats_file.parent.mkdir(exist_ok=True)
        with open(stats_file, "w") as f:
            json.dump(
                {
                    "blocks_today": self.blocks_today,
                    "blocks_total": self.blocks_total,
                    "last_updated": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

    def should_block(self, app_name: str, focus_score: float) -> bool:
        """Determine if app should be blocked"""
        # Never block whitelisted apps
        for allowed in self.whitelist:
            if allowed.lower() in app_name.lower():
                return False

        # Check if in blocklist
        is_blocked = False
        for blocked in self.blocklist:
            if blocked.lower() in app_name.lower():
                is_blocked = True
                break

        # Block if focus score below threshold
        if is_blocked and focus_score < self.block_threshold:
            # Cooldown to prevent rapid blocking
            if self.last_block_time:
                elapsed = (datetime.now() - self.last_block_time).seconds
                if elapsed < 5:  # 5 second cooldown
                    return False
            return True

        return False

    def block_app(self, app_name: str, focus_score: float) -> bool:
        """Block a distracting app"""
        try:
            # Multiple methods to kill process
            killed = False

            # Method 1: taskkill (Windows) - SECURE VERSION
            try:
                # Validate app_name to prevent command injection
                if not self._is_valid_app_name(app_name):
                    logger.error(f"Invalid app name for blocking: {app_name}")
                    return False

                # Use list format to prevent shell injection
                result = subprocess.run(
                    ["taskkill", "/f", "/im", app_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    killed = True
                    logger.info(f"Successfully terminated {app_name} via taskkill")
                else:
                    logger.warning(f"Taskkill failed for {app_name}: {result.stderr}")

            except subprocess.TimeoutExpired:
                logger.error(f"Taskkill timed out for {app_name}")
            except Exception as e:
                logger.warning(f"Taskkill method failed for {app_name}: {e}")

            # Method 2: psutil
            if not killed:
                for proc in psutil.process_iter(["pid", "name"]):
                    if app_name.lower() in proc.info["name"].lower():
                        proc.kill()
                        killed = True

            if killed:
                self.blocks_today += 1
                self.blocks_total += 1
                self.last_block_time = datetime.now()
                self._save_stats()

                logger.info(f"🚫 BLOCKED: {app_name} (focus={focus_score:.0f}%)")
                return True
            else:
                logger.warning(f"⚠️ Could not block {app_name}")
                return False

        except Exception as e:
            logger.error(f"Block error: {e}")
            return False

    def add_to_blocklist(self, app_name: str):
        """Add app to blocklist"""
        if app_name not in self.blocklist:
            self.blocklist.append(app_name)
            self._save_config()
            logger.info(f"✅ Added to blocklist: {app_name}")

    def remove_from_blocklist(self, app_name: str):
        """Remove app from blocklist"""
        if app_name in self.blocklist:
            self.blocklist.remove(app_name)
            self._save_config()
            logger.info(f"❌ Removed from blocklist: {app_name}")

    def add_to_whitelist(self, app_name: str):
        """Add app to whitelist (never block)"""
        if app_name not in self.whitelist:
            self.whitelist.append(app_name)
            self._save_config()

    def remove_from_whitelist(self, app_name: str):
        """Remove app from whitelist"""
        if app_name in self.whitelist:
            self.whitelist.remove(app_name)
            self._save_config()

    def _save_config(self):
        """Save configuration"""
        config = {
            "blocklist": self.blocklist,
            "whitelist": self.whitelist,
            "block_threshold": self.block_threshold,
            "recovery_threshold": self.recovery_threshold,
        }
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)

    def _is_valid_app_name(self, app_name: str) -> bool:
        """Validate app name to prevent command injection and ensure safety"""
        if not app_name or not isinstance(app_name, str):
            return False

        # Check length constraints
        if len(app_name) < 1 or len(app_name) > 255:
            return False

        # Only allow alphanumeric, dots, hyphens, underscores
        # This prevents shell metacharacters and path traversal
        import re

        if not re.match(r"^[a-zA-Z0-9._-]+$", app_name):
            return False

        # Prevent common system processes from being blocked accidentally
        system_processes = {
            "explorer.exe",
            "svchost.exe",
            "csrss.exe",
            "winlogon.exe",
            "lsass.exe",
            "services.exe",
            "smss.exe",
            "system",
        }

        if app_name.lower() in system_processes:
            logger.warning(f"Refusing to block system process: {app_name}")
            return False

        return True

    def get_stats(self) -> Dict:
        """Get blocking statistics"""
        return {
            "today": self.blocks_today,
            "total": self.blocks_total,
            "last_block": (
                self.last_block_time.isoformat() if self.last_block_time else None
            ),
        }
