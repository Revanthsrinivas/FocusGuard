# src/ml/online_learner.py
"""
Online learning with proper feature handling
"""

from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import SGDRegressor

from src.models.feature_extractor import FeatureExtractor
from src.utils.logger import logger


class OnlineLearner:
    """Continuous learning model"""

    def __init__(self, user_manager):
        self.user = user_manager
        self.model_path = self.user.get_model_path()
        self.feature_extractor = FeatureExtractor()
        self.model = self._load_or_create()

        # Track performance
        self.predictions = []
        self.errors = []

    def _load_or_create(self):
        """Load existing model or create new one"""
        if self.user.has_model() and self.model_path.exists():
            try:
                return joblib.load(self.model_path)
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")

        # Create new model
        return SGDRegressor(
            loss="huber",
            penalty="l2",
            alpha=0.0001,
            learning_rate="adaptive",
            eta0=0.01,
            max_iter=1000,
            random_state=42,
        )

    def predict(self, raw_data):
        """Predict focus score from raw data"""
        # Extract features
        features = self.feature_extractor.extract(raw_data)
        features = features.reshape(1, -1)

        if not hasattr(self.model, "coef_"):
            return 50.0  # Not trained yet

        try:
            prediction = self.model.predict(features)[0]
            score = np.clip(prediction * 100, 0, 100)
            return score
        except Exception as e:
            logger.debug(f"Prediction error: {e}")
            return 50.0

    def update(self, raw_data, actual_focus):
        """Update model with actual focus value"""
        # Extract features
        features = self.feature_extractor.extract(raw_data)
        features = features.reshape(1, -1)

        # Normalize actual focus (0-1)
        actual = actual_focus / 100.0
        actual = np.clip(actual, 0, 1)

        try:
            # Partial fit
            self.model.partial_fit(features, np.array([actual]))

            # Track error
            predicted = self.predict(raw_data)
            error = abs(predicted - actual_focus)
            self.errors.append(error)

            # Keep last 1000 errors
            if len(self.errors) > 1000:
                self.errors = self.errors[-1000:]

            # Save model periodically
            if len(self.errors) % 100 == 0:
                joblib.dump(self.model, self.model_path)
                logger.debug(f"Model saved after {len(self.errors)} updates")

        except Exception as e:
            logger.debug(f"Update error: {e}")

    def get_accuracy(self):
        """Get current model accuracy"""
        if not self.errors:
            return 0.85  # Default guess
        return 1 - (sum(self.errors) / len(self.errors) / 100)

    def save(self):
        """Force save model"""
        try:
            joblib.dump(self.model, self.model_path)
            return True
        except Exception as e:
            logger.error(f"Save failed: {e}")
            return False
