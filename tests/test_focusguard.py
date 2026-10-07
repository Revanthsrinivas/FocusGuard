# tests/test_focusguard.py
"""
Unit tests for FocusGuard components
"""

import pytest
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.blocker import SmartBlocker
from src.core.browser_detector import BrowserDetector
from src.core.mouse_tracker import MouseTracker
from src.models.feature_extractor import FeatureExtractor

class TestSmartBlocker:
    """Test SmartBlocker functionality"""
    
    def setup_method(self):
        self.blocker = SmartBlocker()
    
    def test_should_block(self):
        self.blocker.blocklist = ['test.exe']
        self.blocker.block_threshold = 30
        
        assert self.blocker.should_block('test.exe', 20) == True
        assert self.blocker.should_block('test.exe', 50) == False
        assert self.blocker.should_block('safe.exe', 10) == False
    
    def test_whitelist(self):
        self.blocker.whitelist = ['safe.exe']
        self.blocker.blocklist = ['test.exe']
        assert self.blocker.should_block('safe.exe', 10) == False

    def test_cooldown(self):
        self.blocker.blocklist = ['test.exe']
        self.blocker.block_threshold = 30

        assert self.blocker.should_block('test.exe', 20) == True
        self.blocker.last_block_time = None

class TestBrowserDetector:
    """Test browser detection"""
    
    def setup_method(self):
        self.detector = BrowserDetector()
    
    def test_browser_detection(self):
        assert self.detector is not None
    
    def test_url_extraction(self):
        url = self.detector._extract_url("YouTube - Google Chrome")
        assert url == "youtube.com"
        url = self.detector._extract_url("GitHub - FocusGuard")
        assert url == "github.com"
    
    def test_is_distracting(self):
        assert self.detector.is_distracting("youtube.com", "Funny Cats") == True
        assert self.detector.is_distracting("github.com", "Code") == False
    
    def test_is_productive(self):
        assert self.detector.is_productive("youtube.com", "Python Tutorial") == True
        assert self.detector.is_productive("youtube.com", "Funny Cats") == False

class TestFeatureExtractor:
    """Test feature extraction"""
    
    def setup_method(self):
        self.extractor = FeatureExtractor()
    
    def test_extract_features(self):
        sample = {
            'app_name': 'chrome.exe',
            'window_title': 'Python Tutorial - YouTube',
            'hour': 14,
            'minute': 30,
            'day_of_week': 3,
            'is_weekend': 0,
            'cpu_percent': 5,
            'memory_percent': 2
        }
        features = self.extractor.extract_single_sample_features(sample)
        assert len(features) > 0
        assert isinstance(features, (list, tuple, np.ndarray))

class TestMouseTracker:
    """Test mouse tracker"""

    def setup_method(self):
        self.tracker = MouseTracker(buffer_size=50)
        self.tracker.start()

    def teardown_method(self):
        self.tracker.stop()

    def test_get_stats(self):
        stats = self.tracker.get_stats()
        assert 'speed' in stats
        assert 'activity' in stats
        assert 'click_rate' in stats
        assert 'adjustment' in stats

if __name__ == "__main__":
    pytest.main(["-v"])