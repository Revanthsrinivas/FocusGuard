# src/models/advanced_trainer.py
"""
Advanced ML model trainer with XGBoost and Neural Networks
"""

import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import xgboost as xgb
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.neural_network import MLPRegressor

from src.models.feature_extractor import FeatureExtractor
from src.utils.logger import logger


class AdvancedModelTrainer:
    """Train multiple models and pick the best"""

    def __init__(self):
        self.models = {
            "RandomForest": RandomForestRegressor(
                n_estimators=100, max_depth=10, random_state=42
            ),
            "GradientBoosting": GradientBoostingRegressor(
                n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
            ),
            "XGBoost": xgb.XGBRegressor(
                n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42
            ),
            "NeuralNetwork": MLPRegressor(
                hidden_layer_sizes=(64, 32),
                activation="relu",
                solver="adam",
                max_iter=500,
                random_state=42,
            ),
        }

        self.best_model = None
        self.best_score = -999
        self.best_name = None
        self.results = {}

    def train_all(self, data_path="data/training_data.json"):
        """Train all models and find the best"""
        logger.info(f"Loading data from {data_path}")
        data_file = Path(data_path)
        if not data_file.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")

        with open(data_file, "r") as f:
            samples = json.load(f)

        if len(samples) == 0:
            raise ValueError("No training samples found")

        logger.info(f"Loaded {len(samples)} samples")

        extractor = FeatureExtractor()
        X = extractor.extract_batch(samples)
        y = np.array([s.get("focus_score", 50) for s in samples])

        logger.info(f"Extracted {X.shape[1]} features from {X.shape[0]} samples")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        for name, model in self.models.items():
            logger.info(f"Training {name}...")
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)

                cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="r2")

                self.results[name] = {
                    "mae": mae,
                    "r2": r2,
                    "cv_mean": cv_scores.mean(),
                    "cv_std": cv_scores.std(),
                    "model": model,
                }

                logger.info(
                    f"  {name}: R²={r2:.4f}, MAE={mae:.4f}, CV={cv_scores.mean():.4f}"
                )

                if r2 > self.best_score:
                    self.best_score = r2
                    self.best_model = model
                    self.best_name = name

            except Exception as e:
                logger.error(f"  {name} failed: {e}")

        if self.best_model is None:
            raise RuntimeError("No model was successfully trained")

        Path("models").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = f"models/best_model_{self.best_name}_{timestamp}.pkl"
        joblib.dump(self.best_model, model_path)

        results_path = f"models/training_results_{timestamp}.json"
        with open(results_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.info(f"✅ Best model: {self.best_name} (R²={self.best_score:.4f})")
        logger.info(f"💾 Model saved to {model_path}")

        return self.best_model, self.results

    def get_recommendations(self):
        """Get recommendations based on model performance"""
        recommendations = []
        for name, metrics in self.results.items():
            if metrics["r2"] < 0.7:
                recommendations.append(f"Consider collecting more data for {name}")
            elif metrics["cv_std"] > 0.1:
                recommendations.append(
                    f"{name} shows high variance - consider more regularization"
                )
        return recommendations


if __name__ == "__main__":
    trainer = AdvancedModelTrainer()
    best_model, results = trainer.train_all()

    print("\n📊 Model Comparison:")
    print("-" * 50)
    for name, metrics in results.items():
        print(
            f"{name:15} | R²={metrics['r2']:.4f} | MAE={metrics['mae']:.4f} | CV={metrics['cv_mean']:.4f}"
        )

    recs = trainer.get_recommendations()
    if recs:
        print("\n💡 Recommendations:")
        for rec in recs:
            print(f"  • {rec}")
