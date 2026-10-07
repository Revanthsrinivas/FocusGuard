# src/models/trainer.py
"""
ML Model training pipeline for FocusGuard
"""

import json
from datetime import datetime
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from src.models.base_model import BaseFocusModel
from src.models.feature_extractor import FeatureExtractor
from src.utils.logger import logger


class FocusPredictor(BaseFocusModel):
    """Random Forest model for focus score prediction"""

    def __init__(self, model_path=None):
        super().__init__(model_path)
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        )
        self.feature_extractor = FeatureExtractor()
        self.feature_names = self.feature_extractor.get_feature_names()

    def extract_features(self, data):
        """Extract features from raw data"""
        return self.feature_extractor.extract_single_sample_features(data)

    def train(self, X, y):
        """Train the model"""
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)

        metrics = {
            "mae": mean_absolute_error(y_test, y_pred),
            "r2": r2_score(y_test, y_pred),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

        # Feature importance
        if hasattr(self.model, "feature_importances_"):
            self.feature_importances_ = self.model.feature_importances_

        self.log_training(metrics)
        return metrics

    def predict(self, features):
        """Predict focus score (0-100)"""
        if self.model is None:
            return 50.0

        pred = self.model.predict(features)[0]
        return float(pred * 100)

    def predict_proba(self, features):
        """Get probability of being focused"""
        return self.predict(features) / 100


def train_from_data(data_path="data/training_data.json"):
    """Train model from collected data"""

    # Load data
    logger.info(f"Loading data from {data_path}")
    # Try JSON array first, fallback to JSON lines
    try:
        with open(data_path, "r", encoding='utf-8') as f:
            content = f.read().strip()
        if not content:
            samples = []
        else:
            samples = json.loads(content)
    except json.JSONDecodeError:
        # Fallback to JSON lines
        samples = []
        with open(data_path, "r", encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        samples.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue


    logger.info(f"Loaded {len(samples)} samples")

    if len(samples) < 100:
        logger.warning(f"Only {len(samples)} samples. Need at least 100 for training.")
        return None

    # Extract features
    extractor = FeatureExtractor()
    X = extractor.extract_batch(samples)
    y = np.array([s.get("focus_score", 50) for s in samples])

    logger.info(f"Extracted {X.shape[1]} features from {X.shape[0]} samples")

    # Train model
    model = FocusPredictor()
    metrics = model.train(X, y)

    logger.info(
        f"✅ Training complete: MAE={metrics['mae']:.3f}, R²={metrics['r2']:.3f}"
    )

    # Save model
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = f"models/focus_model_{timestamp}.pkl"
    Path("models").mkdir(exist_ok=True)
    model.save(model_path)

    # Plot feature importance
    try:
        import matplotlib.pyplot as plt

        if hasattr(model, "feature_importances_"):
            plt.figure(figsize=(10, 6))
            indices = np.argsort(model.feature_importances_)[::-1]

            plt.title("Feature Importance")
            plt.bar(
                range(len(model.feature_importances_)),
                model.feature_importances_[indices],
            )
            plt.xticks(
                range(len(model.feature_importances_)),
                [model.feature_names[i] for i in indices],
                rotation=45,
                ha="right",
            )
            plt.tight_layout()
            plt.savefig(f"models/feature_importance_{timestamp}.png")
            logger.info(f"📊 Feature importance plot saved")
    except Exception as e:
        logger.warning(f"Could not plot: {e}")

    return model


if __name__ == "__main__":
    print("🚀 Training FocusGuard AI Model...")
    train_from_data()
