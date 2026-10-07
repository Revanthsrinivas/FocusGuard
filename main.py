# main.py - Complete Working Integration
"""
FocusGuard Pro - Professional AI/ML System
"""

import time
import threading
import numpy as np
from pathlib import Path
from datetime import datetime
import joblib
from typing import Dict, Any, Optional, Tuple

from src.ml.user_manager import UserManager
from src.ml.online_learner import OnlineLearner
from src.ml.feedback import FeedbackHandler
from src.ml.registry import ModelRegistry
from src.ml.ensemble_model import EnsembleModel
from src.models.feature_extractor import FeatureExtractor
from src.core.detector import ActivityDetector
from src.core.ocr_analyzer import OCRAnalyzer
from src.core.mouse_tracker import MouseTracker
from src.core.keyboard_tracker import KeyboardTracker
from src.core.blocker import SmartBlocker
from src.data.collector import DataCollector
from src.config.settings import FocusGuardConfig
from src.monitoring.metrics import MetricsCollector
from src.utils.logger import logger
from src.config.constants import MODEL_PATHS, MONITOR_INTERVAL_SECONDS, FEEDBACK_FREQUENCY, FOCUS_DEFAULT, FOCUS_MIN, FOCUS_MAX
from src.monitor_mediator import MonitorMediator


class FocusGuardPro:
    """Complete working FocusGuard system"""
    
    def __init__(self) -> None:
        logger.info("Starting FocusGuard initialization...")

        # Threading lock for shared state
        self._lock = threading.Lock()

        # Load configuration
        logger.debug("Loading configuration...")
        self.config = FocusGuardConfig.load()
        logger.info(f"Config loaded: {self.config.app_name}")

        # Initialize user system
        logger.debug("Initializing user system...")
        self.user = UserManager()
        logger.info(f"User: {self.user.user_id}")
        logger.debug(f"User initialized: {self.user.user_id}")
        
        # Initialize ML components
        self.ensemble = None
        self.learner = OnlineLearner(self.user)
        self.feedback = FeedbackHandler(self.user)
        self.registry = ModelRegistry(self.user)
        self.extractor = FeatureExtractor()  # Add feature extractor
        
        from src.ml.predictor import FocusPredictor
        self.predictor = FocusPredictor(self.ensemble, self.learner, self.extractor)
        
        # Enterprise components
        self.ocr = OCRAnalyzer()
        self.metrics = MetricsCollector()
        
        # Load ensemble if exists (try hybrid first, then optimized, then regular)
        model_paths = MODEL_PATHS
        
        self.ensemble = None
        for model_path in model_paths:
            if model_path.exists():
                try:
                    if model_path.name == 'hybrid_ensemble.pkl':
                        model = joblib.load(model_path)
                        if hasattr(model, 'predict'):
                            self.ensemble = model
                            logger.info("✅ Hybrid AI ensemble model loaded (state-of-the-art)")
                        else:
                            logger.error(f"Loaded object from {model_path} does not have predict method")
                            self.ensemble = None
                    elif model_path.suffix == '.joblib':
                        model = joblib.load(model_path)
                        if hasattr(model, 'predict'):
                            self.ensemble = model
                            logger.info("✅ Optimized ensemble model loaded (joblib)")
                        else:
                            logger.error(f"Loaded object from {model_path} does not have predict method")
                            self.ensemble = None
                    else:
                        self.ensemble.load(model_path)
                        logger.info("✅ Ensemble model loaded (pickle)")
                    break
                except Exception as e:
                    logger.error(f"Failed to load {model_path}: {e}")
                    self.ensemble = None
                    continue
        
        if self.ensemble is None:
            logger.info("⚠️  No trained model found, using untrained ensemble")
            self.ensemble = EnsembleModel()
        
        # Initialize core components
        self.detector = ActivityDetector()
        self.mouse = MouseTracker()
        self.keyboard = KeyboardTracker()
        self.blocker = SmartBlocker()
        self.collector = DataCollector(self.config)
        
        # State
        self.is_running = False
        self.prediction_count = 0
        self.current_focus = 50
        
        # Start trackers
        self.mouse.start()
        self.keyboard.start()
        
        logger.info("Enterprise FocusGuard Pro initialized")
    
    def start(self) -> None:
        """Start monitoring"""
        if self.is_running:
            logger.info("Monitoring already running")
            return
        
        # Validate required components
        required_attrs = ['detector', 'ocr', 'mouse', 'keyboard', 'blocker', 'extractor', 'ensemble', 'learner', 'collector', 'metrics']
        missing = [attr for attr in required_attrs if not hasattr(self, attr) or getattr(self, attr) is None]
        if missing:
            raise ValueError(f"Missing required components: {missing}")
        
        self.is_running = True
        self.collector.start()
        
        self.monitor_mediator = MonitorMediator(
            detector=self.detector,
            ocr=self.ocr,
            mouse=self.mouse,
            keyboard=self.keyboard,
            blocker=self.blocker,
            extractor=self.extractor,
            ensemble=self.ensemble,
            learner=self.learner,
            collector=self.collector,
            metrics=self.metrics
        )
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Monitoring started")
    
    def stop(self):
        """Stop monitoring"""
        self.is_running = False
        self.collector.stop()
        self.mouse.stop()
        self.keyboard.stop()
        logger.info("Monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop with enterprise features"""
        while self.is_running:
            try:
                activity, mouse_stats, keyboard_stats, ocr_result = self._get_activity()
                sample = self._prepare_sample(activity, mouse_stats, keyboard_stats, ocr_result)
                
                start_time = time.time()
                focus_score = self._predict_focus(sample)
                latency = (time.time() - start_time) * 1000  # Convert to ms
                
                self._handle_prediction(focus_score, latency, sample, activity)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}", exc_info=True)
            
            time.sleep(MONITOR_INTERVAL_SECONDS)
    
    def _estimate_actual_focus(self, activity: Dict[str, Any], mouse_stats: Dict[str, Any], ocr_result: Optional[Dict[str, Any]] = None) -> int:
        """Estimate actual focus for model training"""
        # Simple rule-based estimation
        score = int(FOCUS_DEFAULT)
        
        # Productive apps get higher score
        productive = ['code', 'vscode', 'excel', 'word', 'notion']
        if any(p in activity['app'].lower() for p in productive):
            score += 30
        
        # Distracting apps get lower
        distracting = ['youtube', 'netflix', 'facebook', 'game']
        if any(d in activity['app'].lower() for d in distracting):
            score -= 40
        
        # Mouse activity adjustments
        if mouse_stats['activity'] < 10:
            score += 10  # Still/reading
        elif mouse_stats['activity'] > 50:
            score -= 20  # Rapid movement
        
        # OCR-based adjustments (enterprise feature)
        if ocr_result:
            if ocr_result['content_type'] == 'reading':
                score += 15  # Reading content = focused
            elif ocr_result['content_type'] == 'social':
                score -= 25  # Social media = distracted
            elif ocr_result['content_type'] == 'entertainment':
                score -= 30  # Entertainment = very distracted
        
        return max(int(FOCUS_MIN), min(int(FOCUS_MAX), score))
    
    def _get_activity(self) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Optional[Dict[str, Any]]]:
        """Get current activity data"""
        activity = self.detector.get_active_window()
        browser_tab = self.detector.get_browser_tab()
        
        mouse_stats = self.mouse.get_stats()
        keyboard_stats = self.keyboard.get_stats()
        
        ocr_result = None
        try:
            if 'hwnd' in activity and activity['hwnd'] and activity['hwnd'] != 0:
                ocr_result = self.ocr.analyze(activity['hwnd'])
        except Exception as e:
            logger.debug(f"OCR analysis failed: {e}")
        
        return activity, mouse_stats, keyboard_stats, ocr_result
    
    def _prepare_sample(self, activity: Dict[str, Any], mouse_stats: Dict[str, Any], keyboard_stats: Dict[str, Any], ocr_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare sample dict for ML"""
        try:
            now = datetime.now()
            sample = {
                'app': activity.get('app', 'unknown'),
                'title': activity.get('title', ''),
                'hour': now.hour,
                'day_of_week': now.weekday(),
                'is_weekend': 1 if now.weekday() >= 5 else 0,
                'mouse_speed': mouse_stats.get('speed', 0.0),
                'mouse_activity': mouse_stats.get('activity', 0.0),
                'click_rate': mouse_stats.get('click_rate', 0.0),
                'typing_speed': keyboard_stats.get('speed', 0.0),
                'is_typing': keyboard_stats.get('is_typing', False)
            }
            
            if ocr_result:
                sample.update({
                    'text_length': ocr_result.get('word_count', 0),
                    'reading_difficulty': ocr_result.get('focus_adjustment', 0)
                })
            
            return sample
        except Exception as e:
            logger.error(f"Error preparing sample: {e}")
            # Return minimal sample
            return {
                'app': 'unknown',
                'title': '',
                'hour': datetime.now().hour,
                'day_of_week': datetime.now().weekday(),
                'is_weekend': 0,
                'mouse_speed': 0.0,
                'mouse_activity': 0.0,
                'click_rate': 0.0,
                'typing_speed': 0.0,
                'is_typing': False
            }
    
    def _predict_focus(self, sample: Dict[str, Any]) -> float:
        """Predict focus score from sample"""
        return self.predictor.predict(sample)
    
    def _handle_prediction(self, focus_score: float, latency: float, sample: Dict[str, Any], activity: Dict[str, Any]) -> None:
        """Handle prediction results: update state, metrics, blocking, logging"""
        with self._lock:
            self.current_focus = focus_score
            self.prediction_count += 1
        
        self.metrics.record_prediction(focus_score, latency, self.learner.get_accuracy())
        self.collector.add_sample(sample, focus_score)
        
        if self.blocker.should_block(activity['app'], focus_score):
            self.blocker.block_app(activity['app'])
            logger.info(f"BLOCKED: {activity['app']}")
        
        if self.prediction_count % FEEDBACK_FREQUENCY == 0:
            logger.info(f"Would ask feedback: {focus_score:.0f}% focus")
        
        actual_focus = self._estimate_actual_focus(activity, self.mouse.get_stats(), None)  # ocr_result not passed
        self.learner.update(sample, actual_focus)
        
        logger.debug(f"Focus: {focus_score:.0f}% | App: {activity['app']}")
    
    def train_ensemble(self) -> bool:
        """Train the ensemble model using collected data"""
        if not hasattr(self, 'collector') or self.collector is None:
            logger.error("Data collector not initialized")
            return False
        
        if not hasattr(self.collector, 'get_training_data'):
            logger.error("Collector missing get_training_data method")
            return False
        
        try:
            # Get training data from collector
            training_data = self.collector.get_training_data(min_samples=MIN_TRAINING_SAMPLES)
            
            if len(training_data) < MIN_TRAINING_SAMPLES:
                logger.warning(f"Not enough training data: {len(training_data)} samples")
                return False
            
            # Train ensemble
            self.ensemble.train(training_data)
            
            # Save ensemble (use optimized path)
            ensemble_path = Path("models/optimized_ensemble.joblib")
            ensemble_path.parent.mkdir(exist_ok=True)
            
            joblib.dump(self.ensemble, ensemble_path)
            logger.info(f"✅ Ensemble saved to {ensemble_path}")
            
            logger.info("✅ Ensemble model trained and saved")
            return True
            
        except Exception as e:
            logger.error(f"Ensemble training failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        stats = {}
        
        # Safely get stats from each component
        if hasattr(self, 'user') and self.user and hasattr(self.user, 'get_stats'):
            stats['user'] = self.user.get_stats()
        else:
            stats['user'] = {}
        
        if hasattr(self, 'learner') and self.learner and hasattr(self.learner, 'get_accuracy'):
            stats['model_accuracy'] = self.learner.get_accuracy()
        else:
            stats['model_accuracy'] = 0.0
        
        stats['predictions'] = getattr(self, 'prediction_count', 0)
        stats['current_focus'] = getattr(self, 'current_focus', FOCUS_DEFAULT)
        
        if hasattr(self, 'feedback') and self.feedback and hasattr(self.feedback, 'get_stats'):
            stats['feedback'] = self.feedback.get_stats()
        else:
            stats['feedback'] = {}
        
        if hasattr(self, 'ocr') and self.ocr and hasattr(self.ocr, 'get_stats'):
            stats['ocr_stats'] = self.ocr.get_stats()
        else:
            stats['ocr_stats'] = {}
        
        if hasattr(self, 'metrics') and self.metrics and hasattr(self.metrics, 'get_stats'):
            stats['metrics'] = self.metrics.get_stats()
        else:
            stats['metrics'] = {}
        
        if hasattr(self, 'ensemble') and self.ensemble and hasattr(self.ensemble, 'is_trained'):
            stats['ensemble_trained'] = self.ensemble.is_trained()
        else:
            stats['ensemble_trained'] = False
        
        return stats


def main() -> None:
    """Main entry point"""
    logger.info("FocusGuard Pro v3.0 - Professional AI/ML Focus System")
    
    app = FocusGuardPro()
    app.start()
    
    try:
        # Keep running
        while True:
            time.sleep(10)
            stats = app.get_stats()
            logger.info(f"Stats: Focus={stats['current_focus']:.0f}%, "
                       f"Accuracy={stats['model_accuracy']:.1%}, "
                       f"Predictions={stats['predictions']}")
    except KeyboardInterrupt:
        app.stop()
        logger.info("Shutting down...")


if __name__ == "__main__":
    main()
