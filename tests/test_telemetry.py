import datetime
import json
import os
from unittest.mock import Mock, patch

import pytest
import requests

from blockassist.telemetry import (
    BLOCKASSIST_VERSION,
    TELEMETRY_API_EVENT_SESSION,
    get_accelerator_info,
    get_ip,
    push_telemetry_event_session,
    push_telemetry_event_trained,
)


def default_telemetry_args():
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    hardware_dict = '{"gpu": "RTX 4090"}'
    return {
        "timestamp": timestamp,
        "duration_ms": 120000,
        "session_count": 5,
        "user_id": "test_user",
            "ip_addr": "192.168.1.1",
            "hardware_dict": hardware_dict,
            "blockassist_version": "1.0.0"
        }

class TestUtilityFunctions:
    """Test utility functions for gathering system information."""

    @patch('requests.get')
    def test_get_ip_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = "203.0.113.1\n"
        mock_get.return_value = mock_response

        ip = get_ip()

        assert ip == "203.0.113.1\n"
        mock_get.assert_called_once_with("https://icanhazip.com/")

    @patch('requests.get')
    def test_get_ip_failure(self, mock_get):
        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(requests.RequestException):
            get_ip()

    @patch('torch.cuda.is_available')
    @patch('torch.cuda.device_count')
    @patch('torch.cuda.get_device_properties')
    def test_get_accelerator_info_with_cuda(self, mock_get_props, mock_device_count, mock_cuda_available):
        mock_cuda_available.return_value = True
        mock_device_count.return_value = 2

        # Mock device properties
        mock_props_0 = Mock()
        mock_props_0.name = "NVIDIA RTX 4090"
        mock_props_0.major = 8
        mock_props_0.minor = 9
        mock_props_0.total_memory = 24576000000
        mock_props_0.multi_processor_count = 128
        mock_props_0.max_threads_per_multi_processor = 2048

        mock_props_1 = Mock()
        mock_props_1.name = "NVIDIA RTX 3080"
        mock_props_1.major = 8
        mock_props_1.minor = 6
        mock_props_1.total_memory = 10240000000
        mock_props_1.multi_processor_count = 68
        mock_props_1.max_threads_per_multi_processor = 2048

        mock_get_props.side_effect = [mock_props_0, mock_props_1]

        devices = get_accelerator_info()

        assert len(devices) == 2
        assert devices[0]["name"] == "NVIDIA RTX 4090"
        assert devices[0]["total_memory"] == 24576000000
        assert devices[1]["name"] == "NVIDIA RTX 3080"
        assert devices[1]["total_memory"] == 10240000000

    @patch('torch.cuda.is_available')
    def test_get_accelerator_info_no_cuda(self, mock_cuda_available):
        mock_cuda_available.return_value = False

        devices = get_accelerator_info()
        assert devices == []

class TestTelemetryPushFunctions:
    """Test telemetry event pushing functions."""

    def test_push_telemetry_event_session_disabled(self):
        """Test that telemetry is disabled when environment variable is set."""
        with patch.dict(os.environ, {"DISABLE_TELEMETRY": "true"}):
            with patch('requests.post') as mock_post:
                push_telemetry_event_session(5000, "test_user", 0.85)
                mock_post.assert_not_called()

    @patch('blockassist.telemetry.get_ip')
    @patch('requests.post')
    @patch.dict(os.environ, {}, clear=True)
    def test_push_telemetry_event_session_enabled(self, mock_post, mock_get_ip):
        """Test telemetry session event when enabled."""
        mock_get_ip.return_value = "203.0.113.1"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        push_telemetry_event_session(5000, "test_user", 0.85)

        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Check URL
        assert call_args[1]['json'] is not None
        assert TELEMETRY_API_EVENT_SESSION in str(call_args)

        # Check payload structure
        payload = call_args[1]['json']
        assert payload['duration_ms'] == 5000
        assert payload['user_id'] == "test_user"
        assert payload['goal_pct'] == 0.85
        assert payload['ip_addr'] == "203.0.113.1"
        assert payload['blockassist_version'] == BLOCKASSIST_VERSION

    def test_push_telemetry_event_trained_disabled(self):
        """Test that training telemetry is disabled when environment variable is set."""
        with patch.dict(os.environ, {"DISABLE_TELEMETRY": "true"}):
            with patch('requests.post') as mock_post:
                push_telemetry_event_trained(120000, "test_user", 5)
                mock_post.assert_not_called()


class TestIntegration:
    """Integration tests for telemetry system."""

    @patch('blockassist.telemetry.get_ip')
    @patch('blockassist.telemetry.get_system_info')
    @patch('requests.post')
    @patch.dict(os.environ, {}, clear=True)
    def test_end_to_end_session_flow(self, mock_post, mock_get_system_info, mock_get_ip):
        """Test complete session telemetry flow."""
        # Setup mocks
        mock_get_ip.return_value = "203.0.113.1"
        mock_get_system_info.return_value = {"gpu": "RTX 4090"}
        mock_post.return_value = Mock(status_code=200)

        # Simulate session
        duration_ms = 300000  # 5 minutes
        user_id = "integration_test_user"
        goal_pct = 0.92

        push_telemetry_event_session(duration_ms, user_id, goal_pct)

        # Verify call was made
        mock_post.assert_called_once()

        # Verify payload
        payload = mock_post.call_args[1]['json']
        assert payload['duration_ms'] == duration_ms
        assert payload['user_id'] == user_id
        assert payload['goal_pct'] == goal_pct
        assert 'timestamp' in payload
        assert payload['blockassist_version'] == BLOCKASSIST_VERSION

    @patch('blockassist.telemetry.get_ip')
    @patch('blockassist.telemetry.get_system_info')
    @patch('requests.post')
    @patch.dict(os.environ, {}, clear=True)
    def test_end_to_end_training_flow(self, mock_post, mock_get_system_info, mock_get_ip):
        """Test complete training telemetry flow."""
        # Setup mocks
        mock_get_ip.return_value = "203.0.113.1"
        mock_get_system_info.return_value = {
            "uname": json.dumps({"system": "Linux"}),
            "arch": "x86_64",
            "os": "Linux",
            "accelerators": [{"name": "RTX 4090"}],
            "ip": "203.0.113.1"
        }
        mock_post.return_value = Mock(status_code=200)

        # Simulate training
        duration_ms = 7200000  # 2 hours
        user_id = "integration_test_user"
        session_count = 10

        push_telemetry_event_trained(duration_ms, user_id, session_count)

        # Verify call was made
        mock_post.assert_called_once()

        # Verify payload
        payload = mock_post.call_args[1]['json']
        assert payload['duration_ms'] == duration_ms
        assert payload['user_id'] == user_id
        assert payload['session_count'] == session_count
        assert 'timestamp' in payload
        assert payload['blockassist_version'] == BLOCKASSIST_VERSION

        # Verify hardware_dict is a JSON string
        hardware_dict = json.loads(payload['hardware_dict'])
        assert isinstance(hardware_dict, dict)

    def test_telemetry_disable_variations(self):
        """Test various ways to disable telemetry."""
        disable_values = ["true", "TRUE", "True", "1", "yes", "YES"]

        for disable_value in disable_values:
            with patch.dict(os.environ, {"DISABLE_TELEMETRY": disable_value}):
                with patch('requests.post') as mock_post:
                    push_telemetry_event_session(5000, "test", 0.5)
                    mock_post.assert_not_called()

    def test_telemetry_enable_variations(self):
        """Test that telemetry is enabled for various values."""
        enable_values = ["false", "FALSE", "False", "0", "no", ""]

        for enable_value in enable_values:
            with patch.dict(os.environ, {"DISABLE_TELEMETRY": enable_value}, clear=True):
                with patch('requests.post') as mock_post:
                    with patch('blockassist.telemetry.get_ip', return_value="203.0.113.1"):
                        mock_post.return_value = Mock(status_code=200)
                        push_telemetry_event_session(5000, "test", 0.5)
                        mock_post.assert_called_once()

        # Test with no environment variable set (should be enabled)
        with patch.dict(os.environ, {}, clear=True):
            with patch('requests.post') as mock_post:
                with patch('blockassist.telemetry.get_ip', return_value="203.0.113.1"):
                    mock_post.return_value = Mock(status_code=200)
                    push_telemetry_event_session(5000, "test", 0.5)
                    mock_post.assert_called_once()
