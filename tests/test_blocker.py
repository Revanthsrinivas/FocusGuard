import pytest
from src.core.blocker import SmartBlocker
from unittest.mock import patch, MagicMock

@pytest.fixture
def blocker():
    b = SmartBlocker()
    b.blocklist = ['youtube.exe', 'netflix.exe']
    b.whitelist = ['vscode.exe', 'python.exe']
    b.block_threshold = 30
    return b

def test_should_block_distracting_low_focus(blocker):
    """Test blocking distracting app with low focus"""
    assert blocker.should_block('youtube.exe', 20) == True

def test_should_block_whitelisted(blocker):
    """Test never block whitelisted apps"""
    assert blocker.should_block('vscode.exe', 10) == False

def test_should_not_block_normal(blocker):
    """Test high focus productive app not blocked"""
    assert blocker.should_block('notepad.exe', 80) == False

def test_blocklist_high_focus(blocker):
    """Test blocklist app with high focus not blocked"""
    assert blocker.should_block('netflix.exe', 60) == False

def test_block_app_success(mocker):
    """Test block_app calls taskkill correctly"""
    b = SmartBlocker()
    
    mocker.patch('subprocess.run', return_value=MagicMock(returncode=0))
    mocker.patch('psutil.process_iter', return_value=[])
    
    success = b.block_app('youtube.exe', 20)
    assert success == True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
