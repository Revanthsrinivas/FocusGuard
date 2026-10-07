import pytest
import numpy as np
from src.models.feature_extractor import FeatureExtractor

def test_feature_extractor_shape():
    """Test feature extractor returns 29 features"""
    extractor = FeatureExtractor()
    
    # Mock sample with all fields
    sample = {
        'hour': 12,
        'day_of_week': 1,
        'app': 'vscode',
        'title': 'test code editor',
        'cpu_percent': 5.0,
        'memory_percent': 10.0,
        'mouse_speed': 100.0,
        'mouse_activity': 20.0,
        'click_rate': 5.0,
        'typing_speed': 50.0,
        'is_typing': True,
        'text_length': 200,
        'reading_difficulty': 0,
        'window_switches': 2,
        'session_duration': 30,
        'productivity_ratio': 0.8,
        'distractions': 1,
        'prev_mouse_speed': 90.0,
        'is_weekend': 0,
    }
    
    features = extractor.extract(sample)
    
    # Assert shape
    assert isinstance(features, np.ndarray)
    assert len(features) == 29
    assert features.dtype == np.float64
    
    # Assert valid range (generally 0-1, sin/cos -1 to 1)
    assert np.all(np.isfinite(features))
    assert np.min(features) >= -1.0
    assert np.max(features) <= 1.0
    
    print(f"Features shape: {features.shape}, min: {np.min(features):.3f}, max: {np.max(features):.3f}")

def test_feature_extractor_zero_speeds():
    """Test safe handling when mouse_speed and typing_speed are zero"""
    extractor = FeatureExtractor()
    
    sample = {
        'hour': 9,
        'day_of_week': 0,
        'app': 'desktop',
        'mouse_speed': 0.0,
        'typing_speed': 0.0,
    }
    
    features = extractor.extract(sample)
    
    # Mouse-typing ratio should be 0.0 (26th feature ~index 25)
    assert features[25] == 0.0
    
    print("Zero speeds test passed")

def test_data_collector_add_sample():
    """Test DataCollector add_sample"""
    from src.data.collector import DataCollector
    from src.config.settings import FocusGuardConfig

    config = FocusGuardConfig()
    collector = DataCollector(config)

    # Clear any samples loaded from previous runs
    collector.samples = []   # clear any pre-loaded samples

    sample_data = {'app': 'test'}
    focus_score = 75.5

    collector.add_sample(sample_data, focus_score)

    assert len(collector.samples) == 1
    assert collector.samples[0]['focus_score'] == focus_score
    assert collector.samples[0]['features'] == sample_data

if __name__ == "__main__":
    pytest.main([__file__, '-v'])

