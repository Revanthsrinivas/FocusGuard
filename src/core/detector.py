# src/core/detector.py
"""
Real activity detection for Windows
"""

from typing import Dict, Optional, Tuple

import psutil
import win32gui
import win32process

from src.utils.logger import logger


class ActivityDetector:
    """Detect current window and browser activity"""

    def __init__(self):
        self.last_window = None
        self.last_app = None

    def get_active_window(self) -> Dict[str, str]:
        """Get currently active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return self._get_default()

            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            # Skip our own app
            try:
                proc = psutil.Process(pid)
                proc_name = proc.name().lower()
                if "python" in proc_name or "focusguard" in proc_name:
                    # Try to get the window behind
                    return self._get_window_behind()
            except Exception as e:
                logger.warning(f"Process check failed for PID {pid}: {e}")
                pass

            window_title = win32gui.GetWindowText(hwnd)
            app_name = (
                proc.name() if "proc" in locals() else self._get_process_name(pid)
            )

            result = {
                "app": app_name,
                "title": window_title[:100] if window_title else "",
                "pid": pid,
                "hwnd": hwnd,
            }

            self.last_window = result
            self.last_app = app_name

            return result

        except Exception as e:
            logger.debug(f"Detection error: {e}")
            return self._get_default()

    def _get_process_name(self, pid):
        """Get process name from PID"""
        try:
            return psutil.Process(pid).name()
        except Exception as e:
            logger.warning(f"Failed to get process name for PID {pid}: {e}")
            return "Unknown"

    def _get_window_behind(self):
        """Try to get the window behind ours"""
        try:
            import pygetwindow as gw

            windows = gw.getAllWindows()
            for w in windows:
                if w.title and "FocusGuard" not in w.title:
                    return {
                        "app": (
                            w.title.split(" - ")[-1] if " - " in w.title else w.title
                        ),
                        "title": w.title[:100],
                        "pid": 0,
                        "hwnd": 0,
                    }
        except Exception as e:
            logger.warning(f"Failed to get window behind: {e}")
            pass
        return self._get_default()

    def _get_default(self):
        """Return default activity"""
        return {"app": "Desktop", "title": "No active window", "pid": 0, "hwnd": 0}

    def get_browser_tab(self) -> Optional[Dict[str, str]]:
        """Get browser tab info if browser is active"""
        active = self.get_active_window()
        app = active["app"].lower()

        # Check if it's a browser
        browsers = ["chrome", "firefox", "edge", "brave", "opera"]
        is_browser = any(b in app for b in browsers)

        if not is_browser:
            return None

        # Try to extract URL from title
        title = active["title"].lower()

        # Common patterns
        patterns = {
            "youtube.com": "youtube",
            "github.com": "github",
            "stackoverflow.com": "stackoverflow",
            "facebook.com": "facebook",
            "twitter.com": "twitter",
            "reddit.com": "reddit",
        }

        for url, name in patterns.items():
            if url in title or name in title:
                return {
                    "browser": app,
                    "url": url,
                    "title": title[:100],
                    "is_productive": self._is_productive_tab(title),
                }

        return {
            "browser": app,
            "url": "unknown",
            "title": title[:100],
            "is_productive": self._is_productive_tab(title),
        }

    def _is_productive_tab(self, title):
        """Determine if browser tab is productive"""
        productive = [
            "tutorial",
            "course",
            "learn",
            "documentation",
            "docs",
            "github",
            "stackoverflow",
            "code",
            "python",
            "javascript",
        ]
        distracting = [
            "youtube",
            "netflix",
            "funny",
            "meme",
            "game",
            "music",
            "facebook",
            "instagram",
            "twitter",
            "reddit",
        ]

        for word in productive:
            if word in title:
                return True
        for word in distracting:
            if word in title:
                return False

        return None  # Unknown
