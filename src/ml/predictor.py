"""
FocusPredictor - Extracted from main.py _predict_focus
"""

import numpy as np
from typing import Dict, Any
from src.ml.ensemble_model import EnsembleModel
from src.ml.online_learner import OnlineLearner
from src.models.feature_extractor import FeatureExtractor
from src.config.constants import FOCUS_DEFAULT, FOCUS_MIN, FOCUS_MAX
from src.utils.logger import logger


class FocusPredictor:
    """Handles all focus prediction logic"""
    
    def __init__(self, ensemble: EnsembleModel, learner: OnlineLearner, extractor: FeatureExtractor):
        self.ensemble = ensemble
        self.learner = learner
        self.extractor = extractor
    
    def predict(self, sample: Dict[str, Any]) -> float:
        """Predict focus score from sample"""
        try:
            features = self.extractor.extract(sample)
            focus_score = FOCUS_DEFAULT  # default
            
            if hasattr(self.ensemble, 'is_trained') and self.ensemble.is_trained():
                focus_score = self.ensemble.predict_single(features)
            elif isinstance(self.ensemble, dict) and 'meta_model' in self.ensemble and 'scaler' in self.ensemble:
                try:
                    features_scaled = self.ensemble['scaler'].transform([features])
                    
                    try:
                        dl_pred = self.ensemble['deep_model'].predict(features_scaled).flatten()[0]
                    except Exception as e:
                        logger.error(str(e), exc_info=True)
                        dl_pred = 50.0
                    rf_pred = self.ensemble['traditional_models']['rf'].predict(features_scaled)[0]
                    xgb_pred = self.ensemble['traditional_models']['xgb'].predict(features_scaled)[0]
                    lgb_pred = self.ensemble['traditional_models']['lgb'].predict(features_scaled)[0]
                    ridge_pred = self.ensemble['traditional_models']['ridge'].predict(features_scaled)[0]
                    
                    meta_features = np.array([list(features_scaled[0]) + [dl_pred, rf_pred, xgb_pred, lgb_pred, ridge_pred]])
                    focus_score = self.ensemble['meta_model'].predict(meta_features)[0]
                except Exception as legacy_err:
                    logger.debug(f"Legacy ensemble failed: {legacy_err}")
                    focus_score = self.learner.predict(sample)
            else:
                focus_score = self.learner.predict(sample)
            
            return max(FOCUS_MIN, min(FOCUS_MAX, focus_score))
            
        except Exception as pred_err:
            logger.warning(f"Prediction failed: {pred_err}, using fallback {FOCUS_DEFAULT}")
            return FOCUS_DEFAULT

