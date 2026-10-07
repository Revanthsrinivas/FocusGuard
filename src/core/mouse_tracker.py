"""
Advanced mouse tracking for behavior analysis
"""

import math
import threading
import time
from collections import deque
from datetime import datetime
from typing import Dict

import win32api
import win32con

from src.utils.logger import logger


class MouseTracker:
    """Track mouse movements and patterns"""

    def __init__(self, buffer_size=200):
        self.buffer_size = buffer_size
        self.positions = deque(maxlen=buffer_size)
        self.clicks = deque(maxlen=buffer_size)
        self.scrolls = deque(maxlen=buffer_size)
        self.is_tracking = False
        self.tracker_thread = None

        self.total_distance = 0.0
        self.click_count = 0
        self.scroll_count = 0
        self.last_position = None
        self.last_time = None

    def start(self):
        """Start mouse tracking thread"""
        if self.is_tracking:
            return
        self.is_tracking = True
        self.tracker_thread = threading.Thread(target=self._track_loop, daemon=True)
        self.tracker_thread.start()

    def stop(self):
        """Stop tracking safely"""
        self.is_tracking = False
        if self.tracker_thread and self.tracker_thread.is_alive():
            self.tracker_thread.join(timeout=2)

    def _track_loop(self):
        """Main tracking loop"""
        while self.is_tracking:
            try:
                x, y = win32api.GetCursorPos()
                current_time = time.time()

                self.positions.append({"x": x, "y": y, "timestamp": current_time})

                if self.last_position:
                    dx = x - self.last_position[0]
                    dy = y - self.last_position[1]
                    distance = math.sqrt(dx * dx + dy * dy)
                    self.total_distance += distance

                    if self.last_time:
                        dt = current_time - self.last_time
                        if dt > 0:
                            speed = distance / dt
                            self.positions[-1]["speed"] = speed

                self.last_position = (x, y)
                self.last_time = current_time

                for button in ["left", "right", "middle"]:
                    key_code = self._get_button_code(button)
                    if win32api.GetAsyncKeyState(key_code) & 0x8000:
                        self.clicks.append(
                            {
                                "button": button,
                                "x": x,
                                "y": y,
                                "timestamp": current_time,
                            }
                        )
                        self.click_count += 1

                time.sleep(0.1)
            except Exception as e:
                # keep tracking alive on transient errors
                logger.debug(f"Mouse tracking error: {e}")
                time.sleep(0.1)

    def _get_button_code(self, button):
        codes = {
            "left": win32con.VK_LBUTTON,
            "right": win32con.VK_RBUTTON,
            "middle": win32con.VK_MBUTTON,
        }
        return codes.get(button, 0)

    def get_mouse_speed(self) -> float:
        if len(self.positions) < 2:
            return 0.0

        now = time.time()
        recent = [p for p in self.positions if now - p["timestamp"] < 1.0]
        if len(recent) < 2:
            return 0.0

        speeds = [p.get("speed", 0.0) for p in recent if "speed" in p]
        return sum(speeds) / len(speeds) if speeds else 0.0

    def get_mouse_activity(self) -> float:
        now = time.time()
        recent = [p for p in self.positions if now - p["timestamp"] < 2.0]
        if not recent:
            return 0.0

        if len(recent) >= 2:
            first = recent[0]
            last = recent[-1]
            dx = last["x"] - first["x"]
            dy = last["y"] - first["y"]
            distance = math.sqrt(dx * dx + dy * dy)
            activity = min(100.0, distance / 5.0)
            return activity

        return 0.0

    def get_click_rate(self) -> float:
        now = time.time()
        recent_clicks = [c for c in self.clicks if now - c["timestamp"] < 60]
        return len(recent_clicks)

    def get_scroll_rate(self) -> float:
        now = time.time()
        recent_scrolls = [s for s in self.scrolls if now - s["timestamp"] < 60]
        return len(recent_scrolls)

    def is_idle(self, threshold=2.0) -> bool:
        if not self.positions:
            return True
        last_move = self.positions[-1]["timestamp"]
        return (time.time() - last_move) > threshold

    def get_focus_adjustment(self) -> int:
        speed = self.get_mouse_speed()
        activity = self.get_mouse_activity()
        click_rate = self.get_click_rate()

        adjustment = 0
        if speed > 500:
            adjustment -= 15
        elif speed > 200:
            adjustment -= 5

        if activity > 50:
            adjustment -= 10
        elif activity < 10:
            adjustment += 5

        if click_rate > 60:
            adjustment -= 20
        elif click_rate > 30:
            adjustment -= 10
        elif click_rate < 5:
            adjustment += 5

        return adjustment

    def get_stats(self) -> Dict:
        return {
            "speed": self.get_mouse_speed(),
            "activity": self.get_mouse_activity(),
            "click_rate": self.get_click_rate(),
            "scroll_rate": self.get_scroll_rate(),
            "is_idle": self.is_idle(),
            "total_distance": self.total_distance,
            "clicks_total": self.click_count,
            "adjustment": self.get_focus_adjustment(),
        }
