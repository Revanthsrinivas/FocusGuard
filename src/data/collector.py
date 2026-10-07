# src/data/collector.py
"""
Data collection pipeline for FocusGuard
Collects user activity for ML training
"""

import base64
import json
import os
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.config.settings import FocusGuardConfig
from src.core.keyboard_tracker import KeyboardTracker  # NEW
from src.core.mouse_tracker import MouseTracker
from src.utils.logger import logger
from src.config.constants import MAX_SAMPLES_IN_MEMORY, MONITOR_INTERVAL_SECONDS, BATCH_SAVE_SIZE, DEFAULT_FOCUS_FALLBACK


class DataCollector:
    """Collects user activity data for ML training"""

    def __init__(
        self,
        config: FocusGuardConfig,
        model=None,
        feature_extractor=None,
        mouse_tracker: MouseTracker = None,
        keyboard_tracker: KeyboardTracker = None,
    ):
        self.config = config
        self.is_collecting = False
        self.collector_thread = None
        self.data_queue = queue.Queue()
        self.lock = threading.Lock()
        self.samples = []
        self.data_file = Path("data/training_data.json")
        self.data_file.parent.mkdir(exist_ok=True)

        self.model = model
        self.feature_extractor = feature_extractor
        self.app = None
        self.last_sample = None

        # Initialize mouse tracker
        self.mouse_tracker = mouse_tracker or MouseTracker()
        self.mouse_tracker.start()

        # Initialize keyboard tracker
        self.keyboard_tracker = keyboard_tracker or KeyboardTracker()
        self.keyboard_tracker.start()

        # Initialize encryption
        self._init_encryption()

        self.load_data()

    def _init_encryption(self):
        """Initialize encryption for sensitive data"""
        try:
            # Use machine-specific key derived from username + salt
            username = os.getenv("USERNAME", "default_user")
            salt = b"focusguard_salt_2024"  # Fixed salt for consistency

            # Derive key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(username.encode()))
            self.cipher = Fernet(key)

        except Exception as e:
            logger.warning(f"Encryption initialization failed: {e}")
            self.cipher = None

    def _encrypt_sensitive_data(self, data: dict) -> dict:
        """Encrypt sensitive fields in data"""
        if not self.cipher:
            return data

        encrypted_data = data.copy()

        # Fields that contain sensitive information
        sensitive_fields = ["window_title", "app_name"]

        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                try:
                    # Encrypt the field value
                    value_bytes = str(encrypted_data[field]).encode("utf-8")
                    encrypted_bytes = self.cipher.encrypt(value_bytes)
                    encrypted_data[field] = base64.b64encode(encrypted_bytes).decode(
                        "utf-8"
                    )
                    encrypted_data[f"{field}_encrypted"] = True
                except Exception as e:
                    logger.debug(f"Failed to encrypt {field}: {e}")

        return encrypted_data

    def _decrypt_sensitive_data(self, data: dict) -> dict:
        """Decrypt sensitive fields in data"""
        if not self.cipher:
            return data

        decrypted_data = data.copy()

        # Fields that might be encrypted
        sensitive_fields = ["window_title", "app_name"]

        for field in sensitive_fields:
            encrypted_flag = f"{field}_encrypted"
            if encrypted_flag in decrypted_data and decrypted_data[encrypted_flag]:
                try:
                    # Decrypt the field value
                    encrypted_b64 = decrypted_data[field]
                    encrypted_bytes = base64.b64decode(encrypted_b64)
                    decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
                    decrypted_data[field] = decrypted_bytes.decode("utf-8")
                    del decrypted_data[encrypted_flag]
                except Exception as e:
                    logger.debug(f"Failed to decrypt {field}: {e}")
                    # Keep original value if decryption fails

        return decrypted_data

    def start(self):
        if self.is_collecting:
            return

        self.is_collecting = True
        self.collector_thread = threading.Thread(
            target=self._collection_loop, daemon=True
        )
        self.collector_thread.start()
        logger.info("Data collection started")

    def stop(self):
        self.is_collecting = False
        if self.collector_thread:
            self.collector_thread.join(timeout=2)

        if self.mouse_tracker:
            self.mouse_tracker.stop()

        if self.keyboard_tracker:
            self.keyboard_tracker.stop()

        self.save_data()
        logger.info("Data collection stopped")

    def _collection_loop(self):
        while self.is_collecting:
            try:
                sample = self.collect_sample()
                if sample:
                    with self.lock:
                        self.data_queue.put(sample)

                if self.data_queue.qsize() >= MAX_SAMPLES_IN_MEMORY:
                    self._process_queue()

                time.sleep(MONITOR_INTERVAL_SECONDS)
            except Exception as e:
                logger.error(f"Collection error: {e}")


    def collect_sample(self) -> Optional[Dict[str, Any]]:
        try:
            import psutil
            import win32gui
            import win32process

            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            if pid <= 0:
                return None

            try:
                proc = psutil.Process(pid)
                proc_name = proc.name()
                cpu_percent = proc.cpu_percent()
                memory_percent = proc.memory_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None

            window_title = win32gui.GetWindowText(hwnd)

            now = datetime.now()
            sample = {
                "timestamp": now.isoformat(),
                "app_name": proc_name,
                "window_title": window_title,
                "pid": pid,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "hour": now.hour,
                "minute": now.minute,
                "day_of_week": now.weekday(),
                "is_weekend": 1 if now.weekday() >= 5 else 0,
            }

            # Add mouse stats
            if self.mouse_tracker:
                try:
                    mouse_stats = self.mouse_tracker.get_stats()
                    sample.update(
                        {
                            "mouse_speed": mouse_stats.get("speed", 0),
                            "mouse_activity": mouse_stats.get("activity", 0),
                            "click_rate": mouse_stats.get("click_rate", 0),
                            "mouse_idle": mouse_stats.get("is_idle", False),
                            "mouse_scroll_rate": mouse_stats.get("scroll_rate", 0),
                        }
                    )
                except Exception as e:
                    logger.debug(f"Mouse stats error: {e}")
                    sample.update(
                        {
                            "mouse_speed": 0,
                            "mouse_activity": 0,
                            "click_rate": 0,
                            "mouse_idle": True,
                            "mouse_scroll_rate": 0,
                        }
                    )

            # Add keyboard stats
            if self.keyboard_tracker:
                try:
                    keyboard_stats = {
                        "typing_speed": self.keyboard_tracker.get_typing_speed(),
                        "is_typing": self.keyboard_tracker.is_typing(),
                        "keyboard_adjustment": self.keyboard_tracker.get_focus_adjustment(),
                    }
                    sample.update(keyboard_stats)
                except Exception as e:
                    logger.debug(f"Keyboard stats error: {e}")
                    sample.update(
                        {
                            "typing_speed": 0,
                            "is_typing": False,
                            "keyboard_adjustment": 0,
                        }
                    )

            return sample

        except Exception as e:
            logger.debug(f"Sample collection error: {e}")
            return None

    def _process_queue(self):
        while not self.data_queue.empty():
            sample = self.data_queue.get()
            if sample:
                self.last_sample = sample

                # AI Prediction if model available
                if self.model and self.feature_extractor:
                    try:
                        features = (
                            self.feature_extractor.extract_single_sample_features(
                                sample
                            )
                        )
                        focus_score = self.model.predict([features])[0] * 100

                        # Apply keyboard adjustment
                        if sample.get("keyboard_adjustment", 0):
                            focus_score = max(
                                0, min(100, focus_score + sample["keyboard_adjustment"])
                            )

                        sample["focus_score"] = float(focus_score)
                        self.last_sample = sample
                    except Exception as e:
                        logger.debug(f"Prediction failed: {e}")
                        sample["focus_score"] = 50.0

                self.samples.append(sample)

            if len(self.samples) >= 100:
                self.save_data()

    def add_sample(self, sample_data: Dict[str, Any], focus_score: float):
        """Add a sample with focus score for training"""
        sample = {
            "timestamp": time.time(),
            "focus_score": float(focus_score),
            "features": sample_data.copy(),  # Store a copy to avoid circular references
        }

        self.samples.append(sample)

        # Auto-save periodically
        if len(self.samples) >= 50:
            self.save_data()

    def save_data(self):
        try:
            # Only save new samples, not all data
            if not self.samples:
                return

            # Encrypt sensitive data before saving
            encrypted_samples = [
                self._encrypt_sensitive_data(sample) for sample in self.samples
            ]

            # Append mode for new data (JSON lines format)
            with open(self.data_file, "a", encoding="utf-8") as f:
                for sample in encrypted_samples:
                    f.write(json.dumps(sample, ensure_ascii=False) + "\n")

            logger.info(f"Saved {len(self.samples)} new encrypted samples")
            self.samples = []

            # Periodically check and trim file size (every 1000 samples)
            if hasattr(self, "_save_counter"):
                self._save_counter += len(self.samples)
            else:
                self._save_counter = len(self.samples)

            if self._save_counter > 1000:
                self._trim_data_file()
                self._save_counter = 0

        except Exception as e:
            logger.error(f"Error saving data: {e}")

    def _trim_data_file(self):
        """Trim data file to keep only recent samples"""
        try:
            if not self.data_file.exists():
                return

            # Read all lines
            with open(self.data_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Keep only last 200,000 lines
            if len(lines) > 200000:
                lines = lines[-200000:]

                # Rewrite file
                with open(self.data_file, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                logger.info(f"Trimmed data file to {len(lines)} samples")

        except Exception as e:
            logger.error(f"Error trimming data file: {e}")

    def load_data(self):
        try:
            if self.data_file.exists():
                with open(self.data_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()

                if not content:
                    self.samples = []
                    return

                # Try loading as JSON array first
                try:
                    self.samples = json.loads(content)
                    # Decrypt sensitive data
                    self.samples = [
                        self._decrypt_sensitive_data(sample) for sample in self.samples
                    ]
                    logger.info(
                        f"Loaded {len(self.samples)} existing samples (JSON array)"
                    )
                except json.JSONDecodeError:
                    # Try loading as JSON lines
                    lines = content.split("\n")
                    self.samples = []
                    for line in lines:
                        line = line.strip()
                        if line:
                            try:
                                obj = json.loads(line)
                                # Decrypt sensitive data
                                obj = self._decrypt_sensitive_data(obj)
                                self.samples.append(obj)
                            except json.JSONDecodeError:
                                continue
                    logger.info(
                        f"Loaded {len(self.samples)} existing samples (JSON lines)"
                    )
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.samples = []

    def export_csv(self, path: str = "data/training_data.csv"):
        try:
            import pandas as pd

            df = pd.DataFrame(self.samples)
            df.to_csv(path, index=False, encoding="utf-8")
            logger.info(f"Data exported to {path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return False

    def add_sample(self, sample_data: Dict[str, Any], focus_score: float):
        """Add a sample with focus score for training"""
        sample = {
            "timestamp": time.time(),
            "focus_score": float(focus_score),
            "features": sample_data.copy(),
        }

        self.samples.append(sample)

        # Auto-save periodically
        if len(self.samples) >= 50:
            self.save_data()

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_samples": len(self.samples),
            "unique_apps": len(set(s["app_name"] for s in self.samples if s)),
            "date_range": {
                "start": self.samples[0]["timestamp"] if self.samples else None,
                "end": self.samples[-1]["timestamp"] if self.samples else None,
            },
        }

    def get_training_data(self, min_samples: int = 50) -> List[Dict[str, Any]]:
        """Get training data for ML models"""
        if len(self.samples) < min_samples:
            return []

        # Convert samples to training format
        training_data = []
        for sample in self.samples[-min_samples:]:  # Use most recent samples
            if sample and "features" in sample and "focus_score" in sample:
                training_data.append(
                    {"features": sample["features"], "target": sample["focus_score"]}
                )

        return training_data
