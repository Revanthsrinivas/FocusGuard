import pytest
from unittest.mock import patch, MagicMock
from src.core.mouse_tracker import MouseTracker

def test_mouse_tracker_get_stats():
    """Test mouse tracker returns expected dict structure"""
    tracker = MouseTracker()
    
    # Mock win32api
    with patch('win32api.GetCursorPos', return_value=(100, 200)):
        tracker.start()
        time.sleep(0.1)  # Let thread start
        tracker.stop()
        
    stats = tracker.get_stats()
    
    expected_keys = ['speed', 'activity', 'click_rate', 'scroll_rate', 'is_idle', 'total_distance', 'clicks_total', 'adjustment']
    
    assert isinstance(stats, dict)
    for key in expected_keys:
        assert key in stats
    
    assert isinstance(stats['speed'], (int, float))
    assert 0 <= stats['activity'] <= 100
    
    print("MouseTracker get_stats test passed")

def test_mouse_tracker_idle():
    """Test idle detection"""
    tracker = MouseTracker()
    
    assert tracker.is_idle() == True  # No positions yet
    
    print("MouseTracker idle test passed")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
