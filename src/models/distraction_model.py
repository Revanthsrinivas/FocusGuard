"""
Distraction Model for FocusGuard
"""

from typing import Any, Dict, Optional

import numpy as np


class DistractionModel:
    """Main distraction detection model"""

    def __init__(self):
        self.is_trained = False

    def predict(
        self,
        vision_features: Dict[str, float],
        behavior_features: Dict[str, float],
        temporal_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Predict distraction probability

        Args:
            vision_features: Features from visual analysis
            behavior_features: Features from behavior analysis
            temporal_context: Time-based context

        Returns:
            Dictionary with prediction results
        """

        # Default distraction score
        distraction_score = 0.5

        # Visual features contribution (40% weight)
        if "distraction_score" in vision_features:
            visual_score = vision_features["distraction_score"]
            distraction_score = visual_score * 0.4

        # Behavioral features contribution (60% weight)
        if "movement_entropy" in behavior_features:
            entropy = behavior_features["movement_entropy"]
            distraction_score += entropy * 0.3

        if "scrolling_pattern" in behavior_features:
            scrolling = behavior_features["scrolling_pattern"]
            distraction_score += scrolling * 0.2

        if (
            "video_watching_pattern" in behavior_features
            and behavior_features["video_watching_pattern"]
        ):
            distraction_score += 0.2

        # Adjust based on temporal context
        if temporal_context and "hour" in temporal_context:
            hour = temporal_context["hour"]
            if 9 <= hour <= 17:  # Work hours
                distraction_score *= 1.1  # Stricter
            else:
                distraction_score *= 0.9  # More lenient

        # Ensure score is between 0 and 1
        distraction_score = min(1.0, max(0.0, distraction_score))

        # Determine distraction level
        if distraction_score >= 0.95:
            level = "critical"
        elif distraction_score >= 0.85:
            level = "high"
        elif distraction_score >= 0.7:
            level = "medium"
        elif distraction_score >= 0.5:
            level = "low"
        else:
            level = "none"

        return {
            "probability": float(distraction_score),
            "level": level,
            "vision_contribution": vision_features.get("distraction_score", 0.5) * 0.4,
            "behavior_contribution": (
                behavior_features.get("movement_entropy", 0.5) * 0.3
            )
            + (behavior_features.get("scrolling_pattern", 0.0) * 0.2),
            "confidence": 0.8,
            "factors": self._analyze_factors(vision_features, behavior_features),
        }

    def _analyze_factors(
        self, vision_features: Dict, behavior_features: Dict
    ) -> Dict[str, float]:
        """Analyze contributing factors"""
        factors = {}

        if (
            "distraction_score" in vision_features
            and vision_features["distraction_score"] > 0.7
        ):
            factors["visual_distraction"] = vision_features["distraction_score"]

        if (
            "movement_entropy" in behavior_features
            and behavior_features["movement_entropy"] > 0.6
        ):
            factors["random_movements"] = behavior_features["movement_entropy"]

        if (
            "scrolling_pattern" in behavior_features
            and behavior_features["scrolling_pattern"] > 0.5
        ):
            factors["excessive_scrolling"] = behavior_features["scrolling_pattern"]

        if (
            "video_watching_pattern" in behavior_features
            and behavior_features["video_watching_pattern"]
        ):
            factors["video_watching"] = 0.8

        return factors

    def save(self, path: str = "models/focusguard_model.pkl"):
        """Save model (placeholder)"""
        print(f"Model saved to {path}")

    def load(self, path: str = "models/focusguard_model.pkl"):
        """Load model (placeholder)"""
        print(f"Model loaded from {path}")
        self.is_trained = True
