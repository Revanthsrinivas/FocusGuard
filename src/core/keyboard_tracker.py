# src/core/keyboard_tracker.py
import threading
import time
from collections import deque

import keyboard

from src.utils.logger import logger


class KeyboardTracker:
    """Track keyboard activity patterns"""

    def __init__(self):
        self.keypresses = deque(maxlen=1000)
        self.is_tracking = False
        self.tracker_thread = None
        self.key_count = 0
        self.last_key_time = None

    def start(self):
        self.is_tracking = True
        keyboard.hook(self._on_key)
        self.tracker_thread = threading.Thread(target=self._track_loop, daemon=True)
        self.tracker_thread.start()

    def _on_key(self, event):
        if event.event_type == "down":
            self.keypresses.append({"key": event.name, "timestamp": time.time()})
            self.key_count += 1
            self.last_key_time = time.time()

    def _track_loop(self):
        while self.is_tracking:
            time.sleep(0.1)

    def get_typing_speed(self) -> float:
        """Get keys per minute"""
        now = time.time()
        recent = [k for k in self.keypresses if now - k["timestamp"] < 60]
        return len(recent)

    def is_typing(self) -> bool:
        """Check if user is typing"""
        return self.last_key_time and (time.time() - self.last_key_time) < 2

    def get_focus_adjustment(self) -> int:
        """Adjust focus based on typing patterns"""
        speed = self.get_typing_speed()

        if speed > 200:  # Very fast typing
            return -15  # Gaming/chatting
        elif speed > 100:  # Fast typing
            return -5
        elif speed > 30:  # Productive typing
            return +5
        elif speed > 0:  # Occasional typing
            return 0
        return 0

    def stop(self):
        """Stop keyboard tracking safely"""
        self.is_tracking = False
        try:
            keyboard.unhook_all()
        except Exception as e:
            logger.error(f"Error unhooking keyboard: {e}")

        if self.tracker_thread and self.tracker_thread.is_alive():
            self.tracker_thread.join(timeout=2)

    def get_stats(self):
        """Get keyboard activity statistics"""
        return {
            "speed": self.get_typing_speed(),
            "is_typing": self.is_typing(),
            "total_keys": self.key_count,
            "recent_keys": len(self.keypresses),
        }
