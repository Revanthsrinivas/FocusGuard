"""
Tests for security improvements in blocker
"""
import pytest
import subprocess
from unittest.mock import patch, MagicMock
from src.core.blocker import SmartBlocker


class TestBlockerSecurity:
    """Test security improvements in SmartBlocker"""

    @pytest.fixture
    def blocker(self):
        """Create blocker instance"""
        return SmartBlocker()

    def test_valid_app_name_validation(self, blocker):
        """Test app name validation"""
        # Valid app names
        assert blocker._is_valid_app_name('chrome.exe') == True
        assert blocker._is_valid_app_name('notepad.exe') == True
        assert blocker._is_valid_app_name('my_app.exe') == True

        # Invalid app names (command injection attempts)
        assert blocker._is_valid_app_name('chrome.exe; rm -rf /') == False
        assert blocker._is_valid_app_name('chrome.exe && del *') == False
        assert blocker._is_valid_app_name('chrome.exe | netstat') == False

        # Invalid app names (path traversal)
        assert blocker._is_valid_app_name('../../../system32/cmd.exe') == False
        assert blocker._is_valid_app_name('C:\\Windows\\System32\\cmd.exe') == False

        # Invalid app names (system processes)
        assert blocker._is_valid_app_name('explorer.exe') == False
        assert blocker._is_valid_app_name('svchost.exe') == False

        # Invalid app names (length)
        assert blocker._is_valid_app_name('') == False
        assert blocker._is_valid_app_name('a' * 256) == False

    @patch('subprocess.run')
    def test_secure_process_termination(self, mock_subprocess, blocker):
        """Test that process termination uses secure methods"""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout='', stderr='')

        # Should succeed with valid app name
        result = blocker._block_app_secure('chrome.exe')
        assert result == True

        # Check that subprocess.run was called with list format (secure)
        mock_subprocess.assert_called_with(
            ['taskkill', '/f', '/im', 'chrome.exe'],
            capture_output=True, text=True, timeout=10
        )

    @patch('subprocess.run')
    def test_process_termination_timeout(self, mock_subprocess, blocker):
        """Test timeout handling in process termination"""
        from subprocess import TimeoutExpired
        mock_subprocess.side_effect = TimeoutExpired(['taskkill'], 10)

        # Should handle timeout gracefully
        result = blocker._block_app_secure('chrome.exe')
        assert result == False

    def test_blocklist_validation(self, blocker):
        """Test that blocklist operations are validated"""
        # Add valid app
        blocker.add_to_blocklist('valid_app.exe')
        assert 'valid_app.exe' in blocker.blocklist

        # Try to add invalid app (should not add)
        blocker.add_to_blocklist('../../../system32/cmd.exe')
        assert '../../../system32/cmd.exe' not in blocker.blocklist

    @patch('psutil.process_iter')
    def test_fallback_process_termination(self, mock_process_iter, blocker):
        """Test fallback process termination method"""
        # Mock psutil process
        mock_proc = MagicMock()
        mock_proc.info = {'name': 'chrome.exe'}
        mock_proc.kill = MagicMock()
        mock_process_iter.return_value = [mock_proc]

        with patch('subprocess.run') as mock_subprocess:
            # Make taskkill fail
            mock_subprocess.return_value = MagicMock(returncode=1)

            result = blocker._block_app_secure('chrome.exe')

            # Should try psutil fallback
            mock_proc.kill.assert_called_once()

    def test_error_handling(self, blocker):
        """Test error handling in blocking operations"""
        # Test with invalid app name
        result = blocker._block_app_secure('../../../invalid.exe')
        assert result == False

        # Test blocking non-existent app
        result = blocker._block_app_secure('nonexistent_app.exe')
        # Should return False but not crash
        assert isinstance(result, bool)