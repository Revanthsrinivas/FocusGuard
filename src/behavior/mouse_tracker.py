"""
Mouse tracking and behavior analysis
"""

import threading
import time
from collections import deque
from typing import Dict

import numpy as np
import pyautogui


class MouseTracker:
    """Tracks and analyzes mouse movement patterns"""

    def __init__(self, sampling_rate: float = 0.1):
        self.sampling_rate = sampling_rate
        self.mouse_data = deque(maxlen=100)
        self.is_tracking = False
        self.tracking_thread = None
        print("🖱️  Mouse tracker initialized")

    def start_tracking(self):
        """Start tracking mouse movements"""
        if self.is_tracking:
            return

        self.is_tracking = True
        self.tracking_thread = threading.Thread(target=self._tracking_loop)
        self.tracking_thread.daemon = True
        self.tracking_thread.start()
        print("🖱️  Mouse tracking started")

    def stop_tracking(self):
        """Stop tracking mouse movements"""
        self.is_tracking = False
        if self.tracking_thread:
            self.tracking_thread.join(timeout=1.0)
        print("🖱️  Mouse tracking stopped")

    def _tracking_loop(self):
        """Main tracking loop"""
        last_position = pyautogui.position()
        last_time = time.time()

        while self.is_tracking:
            try:
                current_time = time.time()
                current_position = pyautogui.position()

                # Calculate movement
                dx = current_position[0] - last_position[0]
                dy = current_position[1] - last_position[1]
                dt = current_time - last_time

                distance = np.sqrt(dx * dx + dy * dy)
                speed = distance / dt if dt > 0 else 0

                # Store data
                self.mouse_data.append(
                    {
                        "timestamp": current_time,
                        "x": current_position[0],
                        "y": current_position[1],
                        "dx": dx,
                        "dy": dy,
                        "distance": distance,
                        "speed": speed,
                    }
                )

                # Update last values
                last_position = current_position
                last_time = current_time

                time.sleep(self.sampling_rate)

            except Exception as e:
                print(f"Mouse tracking error: {e}")
                time.sleep(1)

    def get_movement_patterns(self) -> Dict[str, float]:
        """Analyze recent mouse movements"""
        if len(self.mouse_data) < 10:
            return {
                "movement_entropy": 0.5,
                "scrolling_pattern": 0.0,
                "mean_speed": 0.0,
                "is_stationary": True,
                "video_watching_pattern": False,
            }

        data = list(self.mouse_data)[-50:]  # Last 50 samples

        # Calculate features
        speeds = [d.get("speed", 0) for d in data]
        distances = [d.get("distance", 0) for d in data]

        # Detect scrolling (vertical movement dominance)
        vertical_movement = sum(abs(d.get("dy", 0)) for d in data)
        horizontal_movement = sum(abs(d.get("dx", 0)) for d in data)
        total_movement = vertical_movement + horizontal_movement

        if total_movement > 0:
            scrolling_pattern = vertical_movement / total_movement
        else:
            scrolling_pattern = 0.0

        # Detect if stationary (watching video)
        is_stationary = np.mean(speeds) < 5 and len([s for s in speeds if s > 10]) < 5

        # Movement entropy (randomness)
        if len(data) > 3:
            directions = []
            for i in range(1, len(data)):
                dx = data[i]["dx"]
                dy = data[i]["dy"]
                if abs(dx) > 2 or abs(dy) > 2:  # Significant movement
                    angle = np.arctan2(dy, dx)
                    directions.append(angle)

            if len(directions) > 1:
                # Simple entropy calculation
                bins = 8
                hist, _ = np.histogram(directions, bins=bins, range=(-np.pi, np.pi))
                hist = hist / hist.sum()
                hist = hist[hist > 0]
                entropy = -np.sum(hist * np.log2(hist))
                max_entropy = np.log2(bins)
                movement_entropy = entropy / max_entropy
            else:
                movement_entropy = 0.0
        else:
            movement_entropy = 0.0

        # Video watching pattern: stationary with occasional scrolling
        video_watching_pattern = is_stationary and scrolling_pattern > 0.6

        return {
            "movement_entropy": float(movement_entropy),
            "scrolling_pattern": float(scrolling_pattern),
            "mean_speed": float(np.mean(speeds) if speeds else 0),
            "total_distance": float(np.sum(distances) if distances else 0),
            "is_stationary": is_stationary,
            "video_watching_pattern": video_watching_pattern,
        }
