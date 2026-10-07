"""
Smart Content Analyzer - Simplified Working Version
"""

import time
from typing import Any, Dict

import cv2
import numpy as np
import pyautogui

from src.utils.logger import logger


class SmartAnalyzer:
    """Simplified smart analyzer that actually works"""

    def __init__(self):
        # Work apps
        self.work_apps = [
            "vs code",
            "visual studio",
            "pycharm",
            "intellij",
            "word",
            "excel",
            "powerpoint",
            "outlook",
            "figma",
            "photoshop",
            "illustrator",
            "github",
            "stack overflow",
            "terminal",
            "cmd",
        ]

        # Distraction apps
        self.distraction_apps = [
            "netflix",
            "youtube",
            "prime video",
            "disney+",
            "facebook",
            "twitter",
            "instagram",
            "tiktok",
            "whatsapp",
            "telegram",
            "discord",
            "game",
            "steam",
            "epic",
        ]

        # Educational keywords
        self.educational_keywords = [
            "tutorial",
            "course",
            "lecture",
            "education",
            "learning",
            "how to",
            "explained",
            "guide",
        ]

        print("✅ SMART analyzer initialized")

    def analyze_with_context(self, screen: np.ndarray) -> Dict[str, Any]:
        """Analyze screen with simple context awareness"""
        if screen is None:
            return self._default_result()

        try:
            # Get active window title (simplified)
            window_title = self._get_active_window_simple()

            # Analyze content
            has_video = self._detect_video_simple(screen)
            is_dark = self._is_dark_screen(screen)

            # Determine distraction score
            distraction_score = self._calculate_simple_score(
                window_title, has_video, is_dark
            )

            # Determine content type
            content_type = self._determine_simple_content_type(window_title, has_video)

            # Calculate intent
            intent_score = self._calculate_intent_score(window_title, content_type)

            return {
                "distraction_score": float(distraction_score),
                "content_type": content_type,
                "window_title": window_title,
                "intent_score": float(intent_score),
                "confidence": 0.7,
                "has_video": has_video,
                "is_dark": is_dark,
            }

        except Exception as e:
            print(f"Analysis error: {e}")
            return self._default_result()

    def _get_active_window_simple(self) -> str:
        """Simple window detection"""
        try:
            # Try to get window title
            import pygetwindow as gw

            window = gw.getActiveWindow()
            if window:
                return window.title.lower()
        except Exception as e:
            logger.warning(f"Window detection failed: {e}")
            pass

        return "unknown window"

    def _detect_video_simple(self, screen: np.ndarray) -> bool:
        """Simple video detection"""
        try:
            # Check for play button-like shapes
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

            # Look for horizontal lines (progress bars)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(
                edges, 1, np.pi / 180, 50, minLineLength=100, maxLineGap=10
            )

            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    if abs(y1 - y2) < 5 and abs(x1 - x2) > 200:
                        return True

            # Check for video streaming colors (reds)
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            lower_red = np.array([0, 100, 100])
            upper_red = np.array([10, 255, 255])
            mask = cv2.inRange(hsv, lower_red, upper_red)
            red_ratio = np.sum(mask > 0) / mask.size

            return red_ratio > 0.01

        except Exception as e:
            logger.warning(f"Video detection failed: {e}")
            return False

    def _is_dark_screen(self, screen: np.ndarray) -> bool:
        """Check if screen is dark (fullscreen video)"""
        try:
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            avg_brightness = np.mean(gray) / 255.0
            return avg_brightness < 0.3
        except Exception as e:
            logger.warning(f"Dark screen detection failed: {e}")
            return False

    def _calculate_simple_score(
        self, window_title: str, has_video: bool, is_dark: bool
    ) -> float:
        """Calculate simple distraction score"""
        score = 0.5

        # Window title analysis
        if any(app in window_title for app in self.distraction_apps):
            score = 0.8

        if any(app in window_title for app in self.work_apps):
            score = 0.2

        # Video content
        if has_video:
            # Check if educational
            if any(keyword in window_title for keyword in self.educational_keywords):
                score = min(score + 0.2, 0.6)  # Moderate penalty
            else:
                score = max(score, 0.7)  # High penalty

        # Fullscreen video
        if is_dark and has_video:
            score = max(score, 0.9)

        return min(1.0, max(0.0, score))

    def _determine_simple_content_type(self, window_title: str, has_video: bool) -> str:
        """Determine simple content type"""
        if "youtube" in window_title:
            if any(keyword in window_title for keyword in self.educational_keywords):
                return "educational_video"
            else:
                return "entertainment_video"
        elif "netflix" in window_title:
            return "streaming_entertainment"
        elif any(app in window_title for app in self.work_apps):
            return "work"
        elif has_video:
            return "video_content"
        else:
            return "unknown"

    def _calculate_intent_score(self, window_title: str, content_type: str) -> float:
        """Calculate intent score"""
        if content_type == "work":
            return 0.8
        elif content_type == "educational_video":
            return 0.6
        elif (
            content_type == "entertainment_video"
            or content_type == "streaming_entertainment"
        ):
            return 0.2
        else:
            return 0.5

    def _default_result(self) -> Dict[str, Any]:
        return {
            "distraction_score": 0.5,
            "content_type": "unknown",
            "window_title": "unknown",
            "intent_score": 0.5,
            "confidence": 0.3,
            "has_video": False,
            "is_dark": False,
        }
