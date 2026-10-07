"""
Keyboard activity tracking
"""

import threading
import time
from collections import deque
from typing import Deque, Dict, List, Optional

import keyboard as kb  # Note: This is the 'keyboard' library


class KeyboardTracker:
    """Tracks and analyzes keyboard activity"""

    def __init__(self, sampling_rate: float = 1.0):
        """
        Initialize keyboard tracker

        Args:
            sampling_rate: How often to sample keyboard activity (seconds)
        """
        self.sampling_rate = sampling_rate

        # Data storage
        self.key_events: Deque[Dict] = deque(maxlen=1000)
        self.activity_windows: Deque[Dict] = deque(maxlen=100)

        # Tracking state
        self.is_tracking = False
        self.tracking_thread: Optional[threading.Thread] = None

        # Statistics
        self.keystrokes_last_minute = 0
        self.last_keystroke_time = 0

        print("Keyboard tracker initialized")

    def start_tracking(self) -> None:
        """Start tracking keyboard activity"""
        if self.is_tracking:
            return

        self.is_tracking = True

        # Start event listener
        kb.on_press(self._on_key_press)

        # Start analysis thread
        self.tracking_thread = threading.Thread(target=self._analysis_loop)
        self.tracking_thread.daemon = True
        self.tracking_thread.start()

        print("Keyboard tracking started")

    def stop_tracking(self) -> None:
        """Stop tracking keyboard activity"""
        self.is_tracking = False

        # Remove event listener
        kb.unhook_all()

        if self.tracking_thread:
            self.tracking_thread.join(timeout=1.0)

        print("Keyboard tracking stopped")

    def _on_key_press(self, event: kb.KeyboardEvent) -> None:
        """Handle key press events"""
        if not self.is_tracking:
            return

        current_time = time.time()

        key_event = {
            "timestamp": current_time,
            "key": event.name,
            "scan_code": event.scan_code,
            "is_modifier": event.event_type == "down"
            and event.name in ["shift", "ctrl", "alt", "cmd", "windows"],
        }

        self.key_events.append(key_event)
        self.last_keystroke_time = current_time

        # Update keystrokes per minute
        self._update_keystroke_count()

    def _update_keystroke_count(self) -> None:
        """Update keystrokes per minute count"""
        current_time = time.time()
        one_minute_ago = current_time - 60

        # Count keystrokes in last minute
        count = 0
        for event in self.key_events:
            if event["timestamp"] > one_minute_ago:
                count += 1

        self.keystrokes_last_minute = count

    def _analysis_loop(self) -> None:
        """Main analysis loop"""
        last_analysis_time = time.time()

        while self.is_tracking:
            try:
                current_time = time.time()

                # Analyze activity every sampling interval
                if current_time - last_analysis_time >= self.sampling_rate:
                    self._analyze_activity_window()
                    last_analysis_time = current_time

                time.sleep(0.1)

            except Exception as e:
                print(f"Keyboard analysis error: {e}")
                time.sleep(1)

    def _analyze_activity_window(self) -> None:
        """Analyze keyboard activity in the current time window"""
        current_time = time.time()
        window_start = current_time - self.sampling_rate

        # Filter events in current window
        window_events = [
            event for event in self.key_events if event["timestamp"] >= window_start
        ]

        # Calculate statistics
        total_keys = len(window_events)
        modifier_keys = sum(1 for event in window_events if event["is_modifier"])
        regular_keys = total_keys - modifier_keys

        # Calculate typing speed (keys per minute)
        if self.sampling_rate > 0:
            keys_per_minute = (regular_keys / self.sampling_rate) * 60
        else:
            keys_per_minute = 0

        # Detect patterns
        patterns = self._detect_typing_patterns(window_events)

        # Create activity window record
        activity_window = {
            "timestamp": current_time,
            "total_keys": total_keys,
            "regular_keys": regular_keys,
            "modifier_keys": modifier_keys,
            "keys_per_minute": keys_per_minute,
            "patterns": patterns,
            "inactivity_duration": current_time - self.last_keystroke_time,
        }

        self.activity_windows.append(activity_window)

    def _detect_typing_patterns(self, events: List[Dict]) -> Dict[str, float]:
        """Detect specific typing patterns"""
        patterns = {
            "coding_pattern": 0.0,
            "writing_pattern": 0.0,
            "short_burst_pattern": 0.0,
            "inactive_pattern": 0.0,
        }

        if len(events) < 5:
            patterns["inactive_pattern"] = 1.0
            return patterns

        # Analyze key sequences for patterns

        # Coding pattern: lots of special characters, brackets, semicolons
        coding_keys = {
            "[",
            "]",
            "{",
            "}",
            ";",
            ":",
            "'",
            '"',
            "\\",
            "|",
            "<",
            ">",
            "/",
            "?",
        }
        coding_count = sum(1 for event in events if event["key"] in coding_keys)

        if len(events) > 0:
            coding_ratio = coding_count / len(events)
            if coding_ratio > 0.1:
                patterns["coding_pattern"] = min(1.0, coding_ratio * 3)

        # Writing pattern: mostly letters, spaces, punctuation
        letter_keys = set("abcdefghijklmnopqrstuvwxyz")
        writing_count = sum(
            1
            for event in events
            if event["key"] in letter_keys
            or event["key"] in {"space", "enter", ",", ".", "!"}
        )

        if len(events) > 0:
            writing_ratio = writing_count / len(events)
            if writing_ratio > 0.7:
                patterns["writing_pattern"] = min(1.0, writing_ratio)

        # Short burst pattern: rapid typing followed by pauses
        if len(events) > 10:
            # Calculate time between keystrokes
            timestamps = [event["timestamp"] for event in events]
            intervals = [
                timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)
            ]

            if intervals:
                mean_interval = sum(intervals) / len(intervals)
                burst_threshold = 0.1  # 100ms

                if mean_interval < burst_threshold:
                    patterns["short_burst_pattern"] = 1.0 - (
                        mean_interval / burst_threshold
                    )

        # Inactivity pattern
        current_time = time.time()
        inactivity = current_time - self.last_keystroke_time

        if inactivity > 10:  # 10 seconds
            patterns["inactive_pattern"] = min(
                1.0, inactivity / 60
            )  # Normalize to 1 at 60 seconds

        return patterns

    def get_activity_patterns(self) -> Dict[str, float]:
        """Get recent keyboard activity patterns"""
        if len(self.activity_windows) == 0:
            return {"error": "No activity data"}

        recent_windows = list(self.activity_windows)[-10:]  # Last 10 windows

        try:
            # Aggregate statistics
            total_keys = sum(w["total_keys"] for w in recent_windows)
            regular_keys = sum(w["regular_keys"] for w in recent_windows)
            kpm_values = [
                w["keys_per_minute"] for w in recent_windows if w["keys_per_minute"] > 0
            ]

            if len(kpm_values) > 0:
                avg_kpm = sum(kpm_values) / len(kpm_values)
                max_kpm = max(kpm_values)
            else:
                avg_kpm = 0.0
                max_kpm = 0.0

            # Aggregate patterns
            pattern_sums = {}
            for pattern in [
                "coding_pattern",
                "writing_pattern",
                "short_burst_pattern",
                "inactive_pattern",
            ]:
                values = [w["patterns"].get(pattern, 0.0) for w in recent_windows]
                if values:
                    pattern_sums[pattern] = sum(values) / len(values)
                else:
                    pattern_sums[pattern] = 0.0

            # Calculate overall activity level
            total_time_covered = len(recent_windows) * self.sampling_rate
            if total_time_covered > 0:
                activity_level = regular_keys / (
                    total_time_covered / 60
                )  # Keys per minute
                normalized_activity = min(
                    1.0, activity_level / 200
                )  # Normalize, assuming 200 KPM is max
            else:
                normalized_activity = 0.0

            result = {
                "typing_speed": avg_kpm,
                "max_typing_speed": max_kpm,
                "activity_level": normalized_activity,
                "total_keystrokes": total_keys,
                "regular_keystrokes": regular_keys,
                "inactivity_duration": (
                    recent_windows[-1]["inactivity_duration"] if recent_windows else 0
                ),
            }

            # Add pattern scores
            result.update(pattern_sums)

            return result

        except Exception as e:
            return {"error": str(e)}

    def get_recent_events(self, n_events: int = 50) -> List[Dict]:
        """Get the most recent n key events"""
        if len(self.key_events) == 0:
            return []

        return list(self.key_events)[-n_events:]

    def clear_data(self) -> None:
        """Clear all stored keyboard data"""
        self.key_events.clear()
        self.activity_windows.clear()
