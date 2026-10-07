"""
Smart Behavior Tracker - Simplified Working Version
"""

import time
from collections import deque
from typing import Any, Dict

import numpy as np
import pyautogui


class SmartTracker:
    """Simplified smart tracker that actually works"""

    def __init__(self):
        self.mouse_positions = deque(maxlen=50)
        self.window_changes = deque(maxlen=20)
        self.last_mouse_time = time.time()
        self.last_window_check = time.time()
        self.current_window = ""

        print("✅ SMART tracker initialized")

    def update(self) -> Dict[str, Any]:
        """Update tracking and return analysis"""
        current_time = time.time()

        # Track mouse
        mouse_data = self._track_mouse_simple(current_time)

        # Track window changes
        window_data = self._track_window_simple(current_time)

        # Analyze patterns
        behavior_patterns = self._analyze_patterns_simple(mouse_data, window_data)

        # Calculate focus score
        focus_score = self._calculate_focus_simple(behavior_patterns)

        # Detect task switching
        task_switching = self._detect_switching_simple(window_data)

        return {
            "focus_score": float(focus_score),
            "behavior_patterns": behavior_patterns,
            "task_switching": task_switching,
            "mouse_activity": mouse_data.get("activity", 0),
            "current_window": self.current_window,
            "is_productive_session": focus_score > 0.6
            and not task_switching.get("is_rapid", False),
        }

    def _track_mouse_simple(self, current_time: float) -> Dict[str, float]:
        """Simple mouse tracking"""
        try:
            pos = pyautogui.position()

            if self.mouse_positions:
                last_pos = self.mouse_positions[-1]["position"]
                dx = pos.x - last_pos[0]
                dy = pos.y - last_pos[1]
                distance = np.sqrt(dx * dx + dy * dy)
                time_diff = current_time - self.mouse_positions[-1]["timestamp"]
                speed = distance / time_diff if time_diff > 0 else 0
            else:
                distance = 0
                speed = 0

            self.mouse_positions.append(
                {
                    "position": (pos.x, pos.y),
                    "timestamp": current_time,
                    "distance": distance,
                    "speed": speed,
                }
            )

            # Calculate activity
            if len(self.mouse_positions) > 5:
                recent_speeds = [m["speed"] for m in list(self.mouse_positions)[-5:]]
                avg_speed = np.mean(recent_speeds)
                activity = min(1.0, avg_speed / 500)  # Normalize
            else:
                activity = 0.0

            self.last_mouse_time = current_time

            return {
                "activity": float(activity),
                "avg_speed": float(avg_speed) if "avg_speed" in locals() else 0.0,
                "is_stationary": activity < 0.1,
            }

        except Exception as e:
            return {"activity": 0.0, "is_stationary": True}

    def _track_window_simple(self, current_time: float) -> Dict[str, Any]:
        """Simple window tracking"""
        try:
            import pygetwindow as gw

            window = gw.getActiveWindow()
            if window:
                current_title = window.title

                if current_title != self.current_window:
                    time_since_last = current_time - self.last_window_check

                    self.window_changes.append(
                        {
                            "from": self.current_window,
                            "to": current_title,
                            "timestamp": current_time,
                            "duration": time_since_last,
                        }
                    )

                    self.current_window = current_title
                    self.last_window_check = current_time

                    return {
                        "changed": True,
                        "time_since_last": time_since_last,
                        "new_window": current_title,
                    }

        except Exception as e:
            # If pygetwindow fails, just return no change
            pass

        return {"changed": False, "time_since_last": 0}

    def _analyze_patterns_simple(
        self, mouse_data: Dict, window_data: Dict
    ) -> Dict[str, bool]:
        """Analyze simple behavior patterns"""
        patterns = {}

        # Reading/working pattern
        patterns["working_pattern"] = mouse_data.get(
            "activity", 0
        ) < 0.3 and not window_data.get("changed", False)

        # Scrolling pattern
        patterns["scrolling_pattern"] = 0.1 < mouse_data.get("activity", 0) < 0.5

        # Video watching
        patterns["video_watching"] = mouse_data.get(
            "activity", 0
        ) < 0.1 and mouse_data.get("is_stationary", True)

        return patterns

    def _calculate_focus_simple(self, patterns: Dict[str, bool]) -> float:
        """Calculate simple focus score"""
        score = 0.5

        if patterns.get("working_pattern", False):
            score += 0.3

        if patterns.get("video_watching", False):
            score -= 0.3

        return max(0.0, min(1.0, score))

    def _detect_switching_simple(self, window_data: Dict) -> Dict[str, Any]:
        """Detect window switching patterns"""
        if len(self.window_changes) < 2:
            return {"is_rapid": False, "frequency": 0}

        recent = list(self.window_changes)[-5:]

        if len(recent) >= 2:
            time_span = recent[-1]["timestamp"] - recent[0]["timestamp"]
            frequency = len(recent) / max(1, time_span)
        else:
            frequency = 0

        is_rapid = frequency > 0.5  # More than 0.5 changes per second
        is_bouncing = len(set([c["to"] for c in recent])) > 3

        return {
            "is_rapid": is_rapid or is_bouncing,
            "frequency": frequency,
            "is_bouncing": is_bouncing,
        }
