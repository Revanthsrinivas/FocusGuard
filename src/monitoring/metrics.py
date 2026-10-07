# src/monitoring/metrics.py
"""
Professional metrics collection and alerting
"""

import json
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from src.utils.logger import logger


class MetricsCollector:
    """Collect and analyze system metrics"""

    def __init__(self):
        # Reduced buffer sizes to prevent memory leaks
        self.metrics = {
            "focus_scores": deque(maxlen=1000),  # Reduced from 10000
            "predictions": deque(maxlen=1000),  # Reduced from 10000
            "errors": deque(maxlen=100),  # Reduced from 1000
            "latencies": deque(maxlen=100),  # Reduced from 1000
            "model_accuracy": deque(maxlen=100),  # Reduced from 1000
        }

        self.alerts = []
        self.start_time = datetime.now()
        self.last_save = datetime.now()
        self.metrics_file = Path("data/metrics.json")
        self._lock = threading.Lock()  # Add thread safety
        self.lock = threading.Lock()

        # Load existing metrics
        self._load_metrics()

        # Start alert thread
        self.alert_thread = threading.Thread(target=self._check_alerts, daemon=True)
        self.alert_thread.start()

    def record_prediction(self, focus_score, latency_ms, model_accuracy):
        """Record a prediction event"""
        with self._lock:
            now = datetime.now()
            self.metrics["focus_scores"].append(
                {
                    "timestamp": now.isoformat(),
                    "score": focus_score,
                    "latency": latency_ms,
                }
            )
            self.metrics["predictions"].append(
                {"timestamp": now.isoformat(), "score": focus_score}
            )
            self.metrics["latencies"].append(latency_ms)
            self.metrics["model_accuracy"].append(model_accuracy)

            # Auto-save every hour
            if (now - self.last_save).seconds > 3600:
                self._save_metrics()
                self.last_save = now

    def record_error(self, error_type, details):
        """Record an error event"""
        self.metrics["errors"].append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": error_type,
                "details": str(details),
            }
        )

    def get_stats(self):
        """Get current statistics"""
        try:
            latencies = [
                l for l in self.metrics["latencies"] if isinstance(l, (int, float))
            ]
            accuracies = [
                a for a in self.metrics["model_accuracy"] if isinstance(a, (int, float))
            ]

            return {
                "uptime": (datetime.now() - self.start_time).total_seconds() / 3600,
                "total_predictions": len(self.metrics["predictions"]),
                "avg_focus": (
                    np.mean(
                        [
                            m["score"]
                            for m in self.metrics["focus_scores"]
                            if isinstance(m.get("score"), (int, float))
                        ]
                    )
                    if self.metrics["focus_scores"]
                    else 0
                ),
                "avg_latency": np.mean(latencies) if latencies else 0,
                "error_rate": len(self.metrics["errors"])
                / max(1, len(self.metrics["predictions"])),
                "model_accuracy": np.mean(accuracies) if accuracies else 0,
                "p95_latency": np.percentile(latencies, 95) if latencies else 0,
            }
        except Exception as e:
            logger.error(f"Metrics calculation error: {e}")
            return {
                "uptime": 0,
                "total_predictions": 0,
                "avg_focus": 0,
                "avg_latency": 0,
                "error_rate": 0,
                "model_accuracy": 0,
                "p95_latency": 0,
            }

    def _check_alerts(self):
        """Check for alert conditions"""
        while True:
            stats = self.get_stats()

            # Check conditions
            if stats["avg_latency"] > 100:  # >100ms latency
                self._trigger_alert(
                    "HIGH_LATENCY", f"Latency: {stats['avg_latency']:.0f}ms"
                )

            if stats["error_rate"] > 0.05:  # >5% error rate
                self._trigger_alert(
                    "HIGH_ERROR_RATE", f"Error rate: {stats['error_rate']:.1%}"
                )

            if stats["model_accuracy"] < 0.7:  # <70% accuracy
                self._trigger_alert(
                    "LOW_ACCURACY", f"Accuracy: {stats['model_accuracy']:.1%}"
                )

            time.sleep(60)  # Check every minute

    def _trigger_alert(self, alert_type, message):
        """Trigger an alert"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message,
        }
        self.alerts.append(alert)
        print(f"🚨 ALERT: {alert_type} - {message}")

        # Could also send email, webhook, etc.

    def _save_metrics(self):
        """Save metrics to disk"""
        try:
            data = {
                "stats": self.get_stats(),
                "alerts": self.alerts[-100:],
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.metrics_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save metrics: {e}")

    def _load_metrics(self):
        """Load existing metrics"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, "r") as f:
                    data = json.load(f)
                    # Could restore alerts, etc.
            except Exception as e:
                logger.warning(f"Failed to load metrics file: {e}")
                pass
