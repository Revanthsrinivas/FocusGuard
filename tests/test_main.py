# tests/test_main.py
"""
Unit tests for main.py FocusGuardPro class
"""

import pytest
from unittest.mock import Mock, patch
from main import FocusGuardPro


class TestFocusGuardPro:
    """Test cases for FocusGuardPro"""
    
    @patch('main.FocusGuardConfig')
    @patch('main.UserManager')
    def test_init(self, mock_user, mock_config):
        """Test initialization"""
        mock_config.load.return_value.app_name = "TestApp"
        mock_user.return_value.user_id = "test_user"
        
        app = FocusGuardPro()
        
        assert app.config == mock_config.load.return_value
        assert app.user == mock_user.return_value
        assert hasattr(app, '_lock')
    
    def test_start_validation_missing_components(self):
        """Test start with missing components"""
        app = FocusGuardPro()
        # Don't initialize components
        
        with pytest.raises(ValueError, match="Missing required components"):
            app.start()
    
    @patch('main.DataCollector')
    @patch('main.MetricsCollector')
    @patch('main.OnlineLearner')
    @patch('main.EnsembleModel')
    @patch('main.FeatureExtractor')
    @patch('main.SmartBlocker')
    @patch('main.KeyboardTracker')
    @patch('main.MouseTracker')
    @patch('main.OCRAnalyzer')
    @patch('main.ActivityDetector')
    @patch('main.MonitorMediator')
    def test_start_success(self, mock_mediator, mock_detector, mock_ocr, mock_mouse, mock_keyboard, mock_blocker, mock_extractor, mock_ensemble, mock_learner, mock_metrics, mock_collector):
        """Test successful start"""
        app = FocusGuardPro()
        app.detector = mock_detector
        app.ocr = mock_ocr
        app.mouse = mock_mouse
        app.keyboard = mock_keyboard
        app.blocker = mock_blocker
        app.extractor = mock_extractor
        app.ensemble = mock_ensemble
        app.learner = mock_learner
        app.collector = mock_collector
        app.metrics = mock_metrics
        
        app.start()
        
        assert app.is_running is True
        mock_collector.start.assert_called_once()
        mock_mediator.assert_called_once()
    
    def test_get_stats_safe(self):
        """Test get_stats with missing components"""
        app = FocusGuardPro()
        
        stats = app.get_stats()
        
        assert 'user' in stats
        assert 'model_accuracy' in stats
        assert 'predictions' in stats
        assert 'current_focus' in stats
        assert 'feedback' in stats
        assert 'ocr_stats' in stats
        assert 'metrics' in stats
        assert 'ensemble_trained' in stats