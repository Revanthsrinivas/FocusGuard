# src/ml/ensemble_model.py
"""
Advanced ensemble model with multiple algorithms
"""

import threading
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import xgboost as xgb
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score
from sklearn.neural_network import MLPRegressor


class EnsembleModel:
    """Advanced ensemble of multiple models with voting"""

    def __init__(self):
        self.models = {
            "random_forest": RandomForestRegressor(
                n_estimators=50,
                max_depth=10,
                min_samples_split=5,
                n_jobs=-1,
                random_state=42,
            ),
            "xgboost": xgb.XGBRegressor(
                n_estimators=50,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            ),
            "lightgbm": lgb.LGBMRegressor(
                n_estimators=50,
                max_depth=8,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            ),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=50, max_depth=6, learning_rate=0.1, random_state=42
            ),
            # 'neural_network': MLPRegressor(
            #     hidden_layer_sizes=(64, 32),
            #     activation='relu',
            #     solver='adam',
            #     max_iter=100,
            #     random_state=42
            # ),
            "ridge": Ridge(alpha=1.0),
        }

        self.weights = {name: 1.0 for name in self.models}
        self.cv_scores = {}
        self._is_trained = False
        self.training_lock = threading.Lock()

    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train all models and calculate optimal weights"""
        if not isinstance(X, np.ndarray) or X.ndim != 2 or len(y) != len(X):
            raise ValueError("X must be a 2D numpy array and y must have same length as X")
        
        with self.training_lock:
            print("Training ensemble models...")

            for name, model in self.models.items():
                print(f"  Training {name}...")
                model.fit(X, y)

                # Cross-validation score
                scores = cross_val_score(model, X, y, cv=5, scoring="r2")
                self.cv_scores[name] = scores.mean()

                # Weight based on CV score
                self.weights[name] = max(0, scores.mean())

            # Normalize weights
            total = sum(self.weights.values())
            for name in self.weights:
                self.weights[name] /= total

            self._is_trained = True
            print(f"✅ Ensemble trained with {len(self.models)} models")
            self._print_weights()

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Ensemble prediction with weighted voting"""
        if not isinstance(X, np.ndarray) or X.ndim != 2 or X.shape[1] != 29:
            raise ValueError("Input must be 2D numpy array with 29 features")
        
        if not self._is_trained:
            return np.zeros(len(X))

        predictions = np.zeros((len(X), len(self.models)))

        for i, (name, model) in enumerate(self.models.items()):
            pred = model.predict(X)
            predictions[:, i] = pred * self.weights[name]

        return np.sum(predictions, axis=1)

    def predict_single(self, X: np.ndarray) -> float:
        """Predict single sample with proper scaling"""
        raw_prediction = self.predict(X.reshape(1, -1))[0]
        return max(0, min(100, raw_prediction))  # Clamp to 0-100

    def _print_weights(self):
        """Print model weights"""
        print("\n📊 Model Weights:")
        for name, weight in sorted(
            self.weights.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {name}: {weight:.3f} (CV: {self.cv_scores[name]:.3f})")

    def save(self, path: Path) -> None:
        """Save ensemble model"""
        joblib.dump(
            {
                "models": self.models,
                "weights": self.weights,
                "cv_scores": self.cv_scores,
                "is_trained": self._is_trained,
            },
            path,
        )

    def load(self, path: Path) -> None:
        """Load ensemble model"""
        data = joblib.load(path)
        self.models = data["models"]
        self.weights = data["weights"]
        self.cv_scores = data["cv_scores"]
        self._is_trained = data["is_trained"]

    def is_trained(self):
        """Check if ensemble is trained"""
        return self._is_trained and len(self.models) > 0
