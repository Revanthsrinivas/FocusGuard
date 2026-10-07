import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.data.collector import DataCollector
from src.config.settings import FocusGuardConfig
from src.core.mouse_tracker import MouseTracker
from src.core.keyboard_tracker import KeyboardTracker

@pytest.fixture
def mock_config():
    config = MagicMock(spec=FocusGuardConfig)
    return config

@pytest.fixture
def mock_mouse():
    mouse = MagicMock(spec=MouseTracker)
    mouse.get_stats.return_value = {'speed': 10, 'activity': 20, 'click_rate': 0.5}
    return mouse

@pytest.fixture
def collector(mock_config, mock_mouse):
    collector = DataCollector(
        config=mock_config,
        mouse_tracker=mock_mouse,
        keyboard_tracker=KeyboardTracker()
    )
    return collector

def test_add_sample(collector):
    """Test DataCollector add_sample"""
    sample_data = {'app': 'notepad', 'focus_score': 80.0}
    collector.add_sample(sample_data, 85.0)

    assert len(collector.samples) == 1
    assert collector.samples[0]['features'] == sample_data
    assert collector.samples[0]['focus_score'] == 85.0

def test_add_sample_batch_save(collector, monkeypatch):
    """Test batch saving after 50 samples"""
    def mock_save(self):
        pass
    monkeypatch.setattr(collector, 'save_data', mock_save)

    for i in range(51):
        collector.add_sample({'test': i}, float(i))

    assert len(collector.samples) == 1  # Should save at 50

def test_collect_sample_structure(collector):
    """Test collect_sample returns expected structure"""
    with patch('src.data.collector.win32gui.GetForegroundWindow', return_value=1234), \
         patch('src.data.collector.win32process.GetWindowThreadProcessId', return_value=(0, 1234)):
        sample = collector.collect_sample()
    
    expected_keys = ['app_name', 'window_title', 'pid', 'hour', 'mouse_speed']
    for key in expected_keys:
        assert key in sample

def test_encryption_roundtrip(collector):
    """Test encryption/decryption works"""
    sample = {'window_title': 'Test Window', 'app_name': 'notepad.exe'}
    encrypted = collector._encrypt_sensitive_data(sample)
    decrypted = collector._decrypt_sensitive_data(encrypted)
    
    assert decrypted == sample

