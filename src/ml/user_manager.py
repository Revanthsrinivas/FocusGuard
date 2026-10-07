# src/ml/user_manager.py
"""
User-specific model management
Each user gets their own personalized model
"""

import getpass
import hashlib
import json
from datetime import datetime
from pathlib import Path


class UserManager:
    """Manage user-specific models and data"""

    def __init__(self):
        self.user_id = self._get_user_id()
        self.user_dir = Path(f"data/users/{self.user_id}")
        self.user_dir.mkdir(parents=True, exist_ok=True)

        # User profile
        self.profile = self._load_profile()

    def _get_user_id(self):
        """Create unique user ID from system username"""
        username = getpass.getuser()
        return hashlib.md5(username.encode()).hexdigest()[:12]

    def _load_profile(self):
        """Load user profile"""
        profile_file = self.user_dir / "profile.json"
        if profile_file.exists():
            with open(profile_file, "r") as f:
                return json.load(f)

        # New user profile
        profile = {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "total_focus_time": 0,
            "streak": 0,
            "preferences": {
                "work_hours_start": 9,
                "work_hours_end": 17,
                "block_threshold": 30,
                "productive_keywords": [],
                "distracting_keywords": [],
            },
            "stats": {
                "total_sessions": 0,
                "total_blocks": 0,
                "avg_focus": 50,
                "best_focus": 0,
            },
        }
        self._save_profile(profile)
        return profile

    def _save_profile(self, profile):
        """Save user profile"""
        with open(self.user_dir / "profile.json", "w") as f:
            json.dump(profile, f, indent=2)

    def update_profile(self, **kwargs):
        """Update user profile"""
        for key, value in kwargs.items():
            if key in self.profile:
                self.profile[key] = value
        self._save_profile(self.profile)

    def get_model_path(self):
        """Get path to user's model"""
        return self.user_dir / "model.pkl"

    def has_model(self):
        """Check if user has a trained model"""
        return self.get_model_path().exists()

    def get_stats(self):
        """Get user statistics"""
        return {
            "user_id": self.user_id,
            "total_focus_time": self.profile["total_focus_time"],
            "streak": self.profile["streak"],
            "avg_focus": self.profile["stats"]["avg_focus"],
            "total_blocks": self.profile["stats"]["total_blocks"],
        }
