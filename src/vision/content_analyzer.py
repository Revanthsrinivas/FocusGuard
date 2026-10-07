"""
Content analysis for screen captures
"""

from typing import Any, Dict

import cv2
import numpy as np


class ContentAnalyzer:
    """Analyzes screen content for distraction detection"""

    def __init__(self):
        print("✅ Content analyzer initialized")

    def analyze_screen(self, screen: np.ndarray) -> Dict[str, Any]:
        """
        Analyze screen content for distraction indicators

        Returns:
            Dictionary containing analysis results
        """
        if screen is None:
            return {"distraction_score": 0.5, "content_type": "unknown"}

        try:
            # Simple analysis: check for video streaming sites
            # Convert to HSV for color analysis
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)

            # Check for Netflix/YouTube red
            # Netflix red: HSV(0°, 92%, 90%) or RGB(229, 9, 20)
            # YouTube red: HSV(0°, 100%, 100%) or RGB(255, 0, 0)

            # Define red color ranges (HSV)
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 100, 100])  # Red wraps around
            upper_red2 = np.array([180, 255, 255])

            # Create masks
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_mask = cv2.bitwise_or(mask1, mask2)

            # Calculate red ratio
            red_ratio = np.sum(red_mask > 0) / red_mask.size

            # Simple distraction score based on red detection
            distraction_score = min(1.0, red_ratio * 10)  # Scale up

            # Determine content type
            if red_ratio > 0.001:
                content_type = "video_streaming"
                print(f"🎥 Video content detected (red ratio: {red_ratio:.4f})")
            else:
                content_type = "unknown"

            return {
                "distraction_score": float(distraction_score),
                "content_type": content_type,
                "red_ratio": float(red_ratio),
                "is_video_content": red_ratio > 0.001,
            }

        except Exception as e:
            print(f"Content analysis error: {e}")
            return {"distraction_score": 0.5, "content_type": "error"}
