# src/models/feature_extractor.py
"""
Extract 16 features for ML model
"""

from datetime import datetime

import numpy as np


class FeatureExtractor:
    """Extract features from activity data"""

    def __init__(self):
        # Keywords for feature extraction
        self.productive_keywords = [
            "code",
            "programming",
            "python",
            "javascript",
            "java",
            "document",
            "report",
            "analysis",
            "research",
            "study",
            "tutorial",
            "course",
            "lecture",
            "learning",
            "education",
            "github",
            "stackoverflow",
            "docs",
            "excel",
            "spreadsheet",
            "project",
            "work",
            "office",
        ]

        self.distracting_keywords = [
            "youtube",
            "netflix",
            "video",
            "movie",
            "series",
            "game",
            "gaming",
            "play",
            "funny",
            "memes",
            "facebook",
            "instagram",
            "twitter",
            "reddit",
            "music",
            "spotify",
            "song",
            "news",
            "sports",
        ]

        self.cache = {}  # LRU cache for features

    def extract(self, data):
        """
        Extract 16 features from raw data
        Returns numpy array of features
        """
        # Input validation
        if not isinstance(data, dict):
            print(f"Warning: Invalid data type: {type(data)}, expected dict")
            return np.zeros(16)  # Return default features

        key = tuple(sorted(data.items()))
        if key in self.cache:
            return self.cache[key]

        # Validate required fields and provide defaults
        required_fields = ["hour", "day_of_week", "app"]
        for field in required_fields:
            if field not in data:
                print(f"Warning: Missing field '{field}', using default")
                if field == "hour":
                    data[field] = datetime.now().hour
                elif field == "day_of_week":
                    data[field] = datetime.now().weekday()
                elif field == "app":
                    data[field] = "unknown"

        features = []

        # 1-2: Time features (sin/cos of hour)
        hour = data.get("hour", datetime.now().hour)
        features.append(np.sin(2 * np.pi * hour / 24))
        features.append(np.cos(2 * np.pi * hour / 24))

        # 3: Day of week (normalized)
        day = data.get("day_of_week", datetime.now().weekday())
        features.append(day / 6)

        # 4: Is weekend
        is_weekend = data.get("is_weekend", 1 if day >= 5 else 0)
        features.append(1.0 if is_weekend else 0.0)

        # 5-6: App category
        app = data.get("app", "").lower()
        is_productive_app = any(kw in app for kw in self.productive_keywords)
        is_distracting_app = any(kw in app for kw in self.distracting_keywords)
        features.append(1.0 if is_productive_app else 0.0)
        features.append(1.0 if is_distracting_app else 0.0)

        # 7-9: Title features
        title = data.get("title", "").lower()
        features.append(min(len(title) / 100, 1.0))  # Title length

        prod_matches = sum(1 for kw in self.productive_keywords if kw in title)
        dist_matches = sum(1 for kw in self.distracting_keywords if kw in title)
        features.append(min(prod_matches / 10, 1.0))
        features.append(min(dist_matches / 10, 1.0))

        # 10-11: System features
        features.append(data.get("cpu_percent", 0) / 100)
        features.append(data.get("memory_percent", 0) / 100)

        # 12-14: Mouse features
        features.append(min(data.get("mouse_speed", 0) / 1000, 1.0))
        features.append(data.get("mouse_activity", 0) / 100)
        features.append(min(data.get("click_rate", 0) / 100, 1.0))

        # 15-16: Keyboard features
        features.append(min(data.get("typing_speed", 0) / 200, 1.0))
        features.append(1.0 if data.get("is_typing", False) else 0.0)

        # 17-18: OCR features (enterprise)
        features.append(
            min(data.get("text_length", 0) / 1000, 1.0)
        )  # Normalized text length
        features.append(
            data.get("reading_difficulty", 0) / 20.0
        )  # Normalized difficulty (-1 to 1)

        # 19-28: Advanced features for better accuracy
        # 19: Time since last break (normalized)
        current_hour = data.get("hour", datetime.now().hour)
        work_start = 9
        hours_working = max(0, current_hour - work_start)
        features.append(min(hours_working / 8, 1.0))

        # 20: Mouse acceleration (change in speed)
        mouse_speed = data.get("mouse_speed", 0)
        prev_mouse = data.get("prev_mouse_speed", 0)
        acceleration = mouse_speed - prev_mouse
        features.append(min(abs(acceleration) / 500, 1.0))

        # 21: Window switching frequency
        window_switches = data.get("window_switches", 0)
        features.append(min(window_switches / 10, 1.0))

        # 22: Session duration (normalized)
        session_minutes = data.get("session_duration", 0)
        features.append(min(session_minutes / 120, 1.0))

        # 23: Productivity ratio
        features.append(data.get("productivity_ratio", 0.5))

        # 24: Distraction count (normalized)
        features.append(min(data.get("distractions", 0) / 10, 1.0))

        # 25: Time of day category (one-hot encoded as single feature)
        hour = data.get("hour", 12)
        if 6 <= hour < 12:
            time_category = 0.25  # Morning
        elif 12 <= hour < 18:
            time_category = 0.5  # Afternoon
        elif 18 <= hour < 24:
            time_category = 0.75  # Evening
        else:
            time_category = 1.0  # Night
        features.append(time_category)

        # 26: Mouse-to-typing ratio (gaming vs work indicator)
        mouse_speed = data.get("mouse_speed", 0.0)
        typing_speed = max(data.get("typing_speed", 0.0), 1e-8)
        if mouse_speed == 0.0 and typing_speed == 0.0:
            mouse_typing_ratio = 0.0
        else:
            mouse_typing_ratio = mouse_speed / typing_speed
        features.append(min(abs(mouse_typing_ratio) / 10.0, 1.0))  # abs for safety
        
        # Validate final features
        while len(features) < 29:
            features.append(0.0)
        features = features[:29]

        # 27: Weekend hour interaction (no append after array)
        # ... (comment only, already appended before)

        # 28: App productivity score
        app_score = 0.5  # Neutral default
        if is_productive_app:
            app_score = 1.0
        elif is_distracting_app:
            app_score = 0.0
        features.append(app_score)

        # Pad or truncate to consistent 29 features for model compatibility
        while len(features) < 29:
            features.append(0.0)
        features = features[:29]

        result = np.nan_to_num(np.array(features, dtype=np.float64), nan=0.0, posinf=1.0, neginf=0.0)
        self.cache[key] = result
        return result

    def extract_batch(self, samples):
        """Extract features from multiple samples"""
        features = []
        for sample in samples:
            features.append(self.extract(sample))
        return np.array(features)

    def get_feature_names(self):
        """Return names of all 18 features"""
        return [
            "hour_sin",
            "hour_cos",
            "day_norm",
            "is_weekend",
            "is_productive_app",
            "is_distracting_app",
            "title_len",
            "productive_keywords",
            "distracting_keywords",
            "cpu_usage",
            "memory_usage",
            "mouse_speed",
            "mouse_activity",
            "click_rate",
            "typing_speed",
            "is_typing",
            "text_length",
            "reading_difficulty",
        ]
