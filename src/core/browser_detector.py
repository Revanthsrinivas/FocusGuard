# src/core/browser_detector.py
"""
Detect browser tabs and URLs for intelligent blocking
"""

import re
from typing import Dict, Optional

import psutil
import win32gui
import win32process

from src.utils.logger import logger


class BrowserDetector:
    """Detect active browser tabs and URLs"""

    BROWSERS = {
        "chrome.exe": "Chrome",
        "firefox.exe": "Firefox",
        "msedge.exe": "Edge",
        "brave.exe": "Brave",
        "opera.exe": "Opera",
    }

    def __init__(self):
        self.current_browser = None
        self.current_url = None
        self.current_title = None

    def get_active_tab(self) -> Optional[Dict]:
        """Get currently active browser tab"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            proc = psutil.Process(pid)
            proc_name = proc.name().lower()

            if proc_name in self.BROWSERS:
                window_title = win32gui.GetWindowText(hwnd)
                self.current_title = window_title
                self.current_browser = self.BROWSERS[proc_name]
                self.current_url = self._extract_url(window_title)

                return {
                    "browser": self.current_browser,
                    "title": window_title,
                    "url": self.current_url,
                    "process": proc_name,
                }
        except Exception as e:
            logger.error(f"Browser detection failed: {e}")
            pass
        return None

    def _extract_url(self, title: str) -> str:
        """Extract URL from browser window title"""
        patterns = [
            (r"YouTube", "youtube.com"),
            (r"Facebook", "facebook.com"),
            (r"Twitter", "twitter.com"),
            (r"Instagram", "instagram.com"),
            (r"Reddit", "reddit.com"),
            (r"Netflix", "netflix.com"),
            (r"Twitch", "twitch.tv"),
            (r"Spotify", "spotify.com"),
            (r"GitHub", "github.com"),
            (r"Stack Overflow", "stackoverflow.com"),
            (r"Gmail", "gmail.com"),
            (r"Docs", "docs.google.com"),
        ]

        for pattern, domain in patterns:
            if pattern in title:
                return domain
        return "unknown.com"

    def is_distracting(self, url: str, title: str) -> bool:
        """Check if content is distracting"""
        distracting_sites = [
            "youtube.com",
            "youtu.be",
            "facebook.com",
            "fb.com",
            "twitter.com",
            "x.com",
            "instagram.com",
            "reddit.com",
            "netflix.com",
            "twitch.tv",
            "tiktok.com",
            "spotify.com",
        ]

        for site in distracting_sites:
            if site in url.lower():
                return True

        distracting_keywords = [
            "funny",
            "comedy",
            "meme",
            "game",
            "play",
            "music",
            "song",
            "video",
            "movie",
            "series",
        ]
        for kw in distracting_keywords:
            if kw in title.lower():
                return True

        return False

    def is_productive(self, url: str, title: str) -> bool:
        """Check if content is productive"""
        productive_keywords = [
            "tutorial",
            "course",
            "learn",
            "education",
            "documentation",
            "docs",
            "github",
            "stackoverflow",
            "code",
            "programming",
            "python",
            "javascript",
            "react",
            "vue",
            "angular",
        ]

        for kw in productive_keywords:
            if kw in title.lower() or kw in url.lower():
                return True

        productive_sites = [
            "github.com",
            "stackoverflow.com",
            "docs.python.org",
            "developer.mozilla.org",
            "w3schools.com",
            "coursera.org",
            "udemy.com",
            "kaggle.com",
            "chat.openai.com",
        ]

        for site in productive_sites:
            if site in url.lower():
                return True

        return False

    def get_focus_adjustment(self, url: str, title: str) -> int:
        """Get focus score adjustment based on browser content"""
        if self.is_productive(url, title):
            return 20
        elif self.is_distracting(url, title):
            return -30
        return 0
