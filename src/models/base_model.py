# src/models/base_model.py
"""
Base ML model class for FocusGuard
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np

from src.utils.logger import logger


class BaseFocusModel(ABC):
    """Abstract base class for all focus prediction models"""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path
        self.feature_names = []
        self.training_history = []

    @abstractmethod
    def extract_features(self, data: Dict[str, Any]) -> np.ndarray:
        pass

    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        pass

    @abstractmethod
    def predict(self, features: np.ndarray) -> float:
        pass

    @abstractmethod
    def predict_proba(self, features: np.ndarray) -> float:
        pass

    def save(self, path: Optional[str] = None) -> bool:
        try:
            save_path = path or self.model_path
            if not save_path:
                save_path = (
                    f"models/model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                )

            Path(save_path).parent.mkdir(exist_ok=True)
            joblib.dump(self.model, save_path)
            logger.info(f"Model saved to {save_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    def load(self, path: str) -> bool:
        try:
            self.model = joblib.load(path)
            self.model_path = path
            logger.info(f"Model loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def log_training(self, metrics: Dict[str, float]):
        record = {"timestamp": datetime.now().isoformat(), "metrics": metrics}
        self.training_history.append(record)

        history_dir = Path("models")
        history_dir.mkdir(parents=True, exist_ok=True)

        history_file = history_dir / "training_history.json"
        history = []
        if history_file.exists():
            with open(history_file, "r") as f:
                try:
                    history = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load training history: {e}")
                    history = []

        history.append(record)
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
