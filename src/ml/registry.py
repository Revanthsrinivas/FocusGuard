# src/ml/registry.py
"""
Model version control and A/B testing
"""

import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np


class ModelRegistry:
    """Track all model versions with performance metrics"""

    def __init__(self, user_manager):
        self.user = user_manager
        self.registry_file = self.user.user_dir / "registry.json"
        self.registry = self._load_registry()
        self.current_version = self.registry.get("current_version")

    def _load_registry(self):
        """Load model registry"""
        if self.registry_file.exists():
            with open(self.registry_file, "r") as f:
                return json.load(f)
        return {"versions": [], "current_version": None}

    def _save_registry(self):
        """Save registry"""
        with open(self.registry_file, "w") as f:
            json.dump(self.registry, f, indent=2)

    def register_model(self, model, metrics, description=""):
        """
        Register a new model version
        Returns version number
        """
        version = len(self.registry["versions"]) + 1
        version_name = f"v{version}"

        # Save model file
        model_path = self.user.user_dir / f"model_{version_name}.pkl"
        joblib.dump(model, model_path)

        # Record in registry
        version_info = {
            "version": version,
            "name": version_name,
            "path": str(model_path),
            "created_at": datetime.now().isoformat(),
            "metrics": metrics,
            "description": description,
            "is_active": False,
        }

        self.registry["versions"].append(version_info)
        self._save_registry()

        return version

    def set_active_version(self, version):
        """Set a version as active"""
        for v in self.registry["versions"]:
            v["is_active"] = v["version"] == version

        self.registry["current_version"] = version
        self._save_registry()

        # Load the model
        active = self.get_active_version()
        if active:
            return joblib.load(active["path"])
        return None

    def get_active_version(self):
        """Get active version info"""
        for v in self.registry["versions"]:
            if v["is_active"]:
                return v
        return None

    def get_best_version(self, metric="accuracy"):
        """Get best performing version"""
        best = None
        best_score = -1

        for v in self.registry["versions"]:
            score = v["metrics"].get(metric, 0)
            if score > best_score:
                best_score = score
                best = v

        return best

    def compare_versions(self, v1, v2, metric="accuracy"):
        """Compare two versions"""
        v1_score = self.registry["versions"][v1 - 1]["metrics"].get(metric, 0)
        v2_score = self.registry["versions"][v2 - 1]["metrics"].get(metric, 0)

        return {
            "v1": v1_score,
            "v2": v2_score,
            "improvement": (
                ((v2_score - v1_score) / v1_score * 100) if v1_score > 0 else 0
            ),
            "better": "v2" if v2_score > v1_score else "v1",
        }
