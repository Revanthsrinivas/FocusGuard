# tests/test_core.py
import pytest
from src.core.blocker import SmartBlocker
from src.core.browser_detector import BrowserDetector


def test_blocker_initialization():
    blocker = SmartBlocker()
    assert blocker is not None


def test_blocker_should_block():
    blocker = SmartBlocker()
    blocker.blocklist = ['test.exe']
    blocker.block_threshold = 30

    assert blocker.should_block('test.exe', 20) is True
    assert blocker.should_block('test.exe', 50) is False
    assert blocker.should_block('safe.exe', 10) is False


def test_browser_detection():
    detector = BrowserDetector()
    assert detector is not None
