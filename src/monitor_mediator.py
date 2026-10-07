from typing import Dict, Any, Optional
import time
import numpy as np
import logging
from pathlib import Path
from src.core.detector import ActivityDetector
from src.core.ocr_analyzer import OCRAnalyzer
from src.core.mouse_tracker import MouseTracker
from src.core.keyboard_tracker import KeyboardTracker
from src.core.blocker import SmartBlocker
from src.models.feature_extractor import FeatureExtractor
from src.ml.ensemble_model import EnsembleModel
from src.ml.online_learner import OnlineLearner
from src.data.collector import DataCollector
from src.monitoring.metrics import MetricsCollector
from src.utils.logger import logger


class MonitorMediator:
    """Extracted monitoring logic from main.py with DI"""
    
    def __init__(
        self,
        detector: ActivityDetector,
        ocr: OCRAnalyzer,
        mouse: MouseTracker,
        keyboard: KeyboardTracker,
        blocker: SmartBlocker,
        extractor: FeatureExtractor,
        ensemble: EnsembleModel,
        learner: OnlineLearner,
        collector: DataCollector,
        metrics: MetricsCollector
    ):
        self.detector = detector
        self.ocr = ocr
        self.mouse = mouse
        self.keyboard = keyboard
        self.blocker = blocker
        self.extractor = extractor
        self.ensemble = ensemble
        self.learner = learner
        self.collector = collector
        self.metrics = metrics
        
        self.prediction_count = 0
        self.current_focus = 50.0
        
    def _detect_activity(self) -> Dict[str, Any]:
        """Extracted activity detection"""
        activity = self.detector.get_active_window()
        
        # OCR Analysis
        ocr_result = None
        if 'hwnd' in activity and activity['hwnd'] and activity['hwnd'] != 0:
            try:
                ocr_result = self.ocr.analyze(activity['hwnd'])
            except Exception as e:
                logger.debug(f"OCR analysis failed: {e}")
        
        # Get input stats
        mouse_stats = self.mouse.get_stats()
        keyboard_stats = self.keyboard.get_stats()
        
        return {
            'activity': activity,
            'mouse_stats': mouse_stats,
            'keyboard_stats': keyboard_stats,
            'ocr_result': ocr_result
        }
    
    def _predict_focus(self, sample: Dict[str, Any]) -> float:
        """Extracted focus prediction with fallbacks"""
        try:
            features = self.extractor.extract(sample)
            focus_score = 50.0
            
            # Priority 1: Trained ensemble
            if hasattr(self.ensemble, 'is_trained') and self.ensemble.is_trained():
                focus_score = self.ensemble.predict_single(features)
            
            # Priority 2: Legacy dict ensemble
            elif isinstance(self.ensemble, dict) and 'meta_model' in self.ensemble:
                features_scaled = self.ensemble['scaler'].transform([features])
                predictions = []
                for model_name in ['deep_model', 'rf', 'xgb', 'lgb', 'ridge']:
                    try:
                        pred = self.ensemble['traditional_models'][model_name].predict(features_scaled)[0]
                        predictions.append(pred)
                    except Exception as e:
                        logger.error(str(e), exc_info=True)
                        predictions.append(50.0)
                meta_features = np.array([list(features_scaled[0]) + predictions])
                focus_score = self.ensemble['meta_model'].predict(meta_features)[0]
            
            # Fallback
            else:
                focus_score = self.learner.predict(sample)
            
            return max(0.0, min(100.0, focus_score))
            
        except Exception as e:
            logger.warning(f"Prediction error: {e}", exc_info=True)
            return 50.0
    
    def _maybe_block(self, activity: Dict[str, Any], focus_score: float) -> bool:
        """Extracted blocking logic"""
        if self.blocker.should_block(activity['app'], focus_score):
            self.blocker.block_app(activity['app'])
            logger.info(f"BLOCKED: {activity['app']}")
            return True
        return False
    
    def _update_stats(self, sample: Dict[str, Any], focus_score: float, actual_focus: float, latency: float):
        """Extracted stats updating"""
        self.current_focus = focus_score
        self.prediction_count += 1
        self.metrics.record_prediction(focus_score, latency, self.learner.get_accuracy())
        self.collector.add_sample(sample, focus_score)
        self.learner.update(sample, actual_focus)
    
    def run_cycle(self) -> Dict[str, Any]:
        """Single monitoring cycle - returns stats"""
        start_time = time.time()
        
        # 1. Detect
        detection = self._detect_activity()
        activity = detection['activity']
        mouse_stats = detection['mouse_stats']
        keyboard_stats = detection['keyboard_stats']
        ocr_result = detection['ocr_result']
        
        # 2. Prepare sample
        sample = {
            'app': activity['app'],
            'title': activity['title'],
            'hour': time.localtime().tm_hour,
            'day_of_week': time.localtime().tm_wday,
            'is_weekend': 1 if time.localtime().tm_wday >= 5 else 0,
            'mouse_speed': mouse_stats.get('speed', 0),
            'mouse_activity': mouse_stats.get('activity', 0),
            'click_rate': mouse_stats.get('click_rate', 0),
            'typing_speed': keyboard_stats.get('speed', 0),
            'is_typing': keyboard_stats.get('is_typing', False)
        }
        
        if ocr_result:
            sample.update({
                'text_length': ocr_result.get('word_count', 0),
                'reading_difficulty': ocr_result.get('focus_adjustment', 0)
            })
        
        # 3. Predict
        focus_score = self._predict_focus(sample)
        
        # 4. Block
        blocked = self._maybe_block(activity, focus_score)
        
        # 5. Update (estimate actual for training)
        actual_focus = self._estimate_actual_focus(activity, mouse_stats, ocr_result)
        latency = (time.time() - start_time) * 1000
        self._update_stats(sample, focus_score, actual_focus, latency)
        
        return {
            'focus_score': focus_score,
            'blocked': blocked,
            'latency_ms': latency,
            'prediction_count': self.prediction_count
        }
    
    def _estimate_actual_focus(self, activity: Dict[str, Any], mouse_stats: Dict[str, Any], ocr_result: Optional[Dict] = None) -> float:
        """Rule-based actual focus estimate for training"""
        score = 50.0
        
        # App rules
        if any(p in activity['app'].lower() for p in ['code', 'vscode', 'excel']):
            score += 30
        if any(d in activity['app'].lower() for d in ['youtube', 'netflix']):
            score -= 40
        
        # Mouse rules
        if mouse_stats.get('activity', 0) < 10:
            score += 10
        if mouse_stats.get('activity', 0) > 50:
            score -= 20
        
        # OCR rules
        if ocr_result and ocr_result.get('content_type') == 'social':
            score -= 25
        
        return max(0, min(100, score))

