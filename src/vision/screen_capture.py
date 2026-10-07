"""
Screen capture module for FocusGuard
"""

import threading
import time
from typing import Optional

import cv2
import numpy as np
import pyautogui


class ScreenCapture:
    """Captures and manages screen content"""

    def __init__(self, interval: float = 2.0):
        """
        Initialize screen capture

        Args:
            interval: Capture interval in seconds
        """
        self.interval = interval
        self.is_capturing = False
        self.last_capture = None
        self.capture_thread: Optional[threading.Thread] = None

        # Get screen size
        try:
            self.screen_width, self.screen_height = pyautogui.size()
            print(
                f"✅ Screen capture initialized ({self.screen_width}x{self.screen_height})"
            )
        except Exception as e:
            print(f"⚠️  Could not get screen size: {e}")
            self.screen_width, self.screen_height = 1920, 1080  # Default

    def start_capture(self) -> None:
        """Start continuous screen capture"""
        if self.is_capturing:
            return

        self.is_capturing = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()

        print("📸 Screen capture started")

    def stop_capture(self) -> None:
        """Stop screen capture"""
        self.is_capturing = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
        print("📸 Screen capture stopped")

    def _capture_loop(self) -> None:
        """Main capture loop"""
        while self.is_capturing:
            try:
                # Capture screenshot
                screenshot = pyautogui.screenshot()

                # Convert to OpenCV format
                frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                self.last_capture = frame

                # Wait for next capture
                time.sleep(self.interval)

            except Exception as e:
                print(f"Screen capture error: {e}")
                time.sleep(1)

    def capture_single(self) -> Optional[np.ndarray]:
        """Capture a single screenshot immediately"""
        try:
            screenshot = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            self.last_capture = frame
            return frame
        except Exception as e:
            print(f"Error capturing single screenshot: {e}")
            return None

    def get_current_screen(self) -> Optional[np.ndarray]:
        """Get the most recent screen capture"""
        return self.last_capture
