# tests/test_config.py
import pytest
from src.config.settings import FocusGuardConfig, Thresholds


def test_config_loading():
    config = FocusGuardConfig.load()
    assert config.app_name == 'FocusGuard Pro'
    assert config.version == '2.0.0'


def test_threshold_validation():
    with pytest.raises(ValueError):
        Thresholds(low=0.8, medium=0.5)


def test_config_save_load(tmp_path):
    config = FocusGuardConfig()
    config.app_name = 'Test App'

    test_file = tmp_path / 'test_config.json'
    config.save(str(test_file))

    loaded = FocusGuardConfig.load(str(test_file))
    assert loaded.app_name == 'Test App'
