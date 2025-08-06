from unittest.mock import patch

import pytest

from blockassist.episode import EpisodeRunner


class TestEpisodeRunnerUtils:
    def test_get_last_goal_percentage_min_empty_dict(self):
        runner = EpisodeRunner("dummy_address_eoa", "dummy_checkpoint_dir")
        result = {}
        assert runner.get_last_goal_percentage_min(result) == 0.0

    def test_get_last_goal_percentage_min_multiple_keys(self):
        runner = EpisodeRunner("dummy_address_eoa", "dummy_checkpoint_dir")
        result = {
            "goal_percentage_1_min": 0.25,
            "goal_percentage_5_min": 0.75,
            "goal_percentage_10_min": 0.90,
        }
        assert runner.get_last_goal_percentage_min(result) == 0.90

    def test_get_last_goal_percentage_min_mixed_keys(self):
        runner = EpisodeRunner("dummy_address_eoa", "dummy_checkpoint_dir")
        result = {
            "goal_percentage_3_min": 0.50,
            "other_metric": 1.0,
            "goal_percentage_15_min": 0.85,
            "goal_percentage_1_min": 0.20,
        }
        assert runner.get_last_goal_percentage_min(result) == 0.85

    def test_get_last_goal_percentage_min_zero_minute(self):
        runner = EpisodeRunner("dummy_address_eoa", "dummy_checkpoint_dir")
        result = {"goal_percentage_0_min": 0.10, "goal_percentage_5_min": 0.60}
        assert runner.get_last_goal_percentage_min(result) == 0.60


class TestEpisodeRunnerTelemetry:
    @pytest.fixture
    def common_patches(self):
        """Common patches used across multiple test methods."""
        with patch("blockassist.episode.telemetry.push_telemetry_event_session") as mock_telemetry_session, \
             patch("blockassist.episode.get_identifier") as mock_get_identifier, \
             patch("blockassist.episode.run_main") as mock_main, \
             patch("time.time") as mock_time:
            yield {
                "mock_telemetry_session": mock_telemetry_session,
                "mock_get_identifier": mock_get_identifier,
                "mock_main": mock_main,
                "mock_time": mock_time
            }

    def setup_mocks(self, common_patches, time_values=None, user_id="test_user",
                   main_return_value=None, main_side_effect=None, episode_count=None):
        """Setup common mock configurations."""
        if time_values is None:
            time_values = [1000.0, 1005.0, 1006.0]

        common_patches["mock_time"].side_effect = time_values
        common_patches["mock_get_identifier"].return_value = user_id

        if main_return_value is not None:
            common_patches["mock_main"].return_value = main_return_value
        elif main_side_effect is not None:
            common_patches["mock_main"].side_effect = main_side_effect

    def test_start_calls_session_telemetry_on_success(self, common_patches):
        """Test that start() calls session telemetry when episode completes successfully."""
        mock_telemetry_session = common_patches["mock_telemetry_session"]

        self.setup_mocks(
            common_patches,
            time_values=[1000.0, 1005.5, 1006.0],
            user_id="test_user_123",
            main_return_value={
                "goal_percentage_1_min": 0.25,
                "goal_percentage_5_min": 0.75,
                "goal_percentage_10_min": 0.90,
                "other_metric": 1.0,
            }
        )

        runner = EpisodeRunner("dummy_address_eoa", "dummy_checkpoint_dir")
        runner.start()

        # Note: mock_backup is accessed via common_patches in assertions
        common_patches["mock_main"].assert_called_once()
        mock_telemetry_session.assert_called_once_with(
            5500,  # duration_ms: (1005.5 - 1000.0) * 1000
            "test_user_123",  # user_id
            0.90,  # goal_pct: highest goal_percentage_x_min value
        )

    def test_start_calls_session_telemetry_with_zero_goal_percentage(self, common_patches):
        """Test that start() calls session telemetry with 0.0 when no goal percentages in result."""
        mock_telemetry_session = common_patches["mock_telemetry_session"]

        self.setup_mocks(
            common_patches,
            time_values=[2000.0, 2003.2, 2004.0],
            user_id="test_user_456",
            main_return_value={"other_metric": 1.0, "success": True}
        )

        runner = EpisodeRunner("dummy_address_eoa", "dummy_checkpoint_dir")
        runner.start()

        mock_telemetry_session.assert_called_once_with(
            3200,  # duration_ms: (2003.2 - 2000.0) * 1000
            "test_user_456",  # user_id
            0.0,  # goal_pct: 0.0 when no goal percentages found
        )

    def test_start_handles_keyboard_interrupt_gracefully(self, common_patches):
        """Test that start() handles KeyboardInterrupt and still calls telemetry if episode completed."""
        mock_telemetry_session = common_patches["mock_telemetry_session"]

        # Create a mock main function that raises KeyboardInterrupt after first call
        call_count = 0
        def mock_main_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"goal_percentage_5_min": 0.50}
            else:
                raise KeyboardInterrupt("User stopped episode")

        self.setup_mocks(
            common_patches,
            time_values=[3000.0, 3001.5, 3002.0],
            user_id="test_user_789",
            main_side_effect=mock_main_side_effect
        )

        runner = EpisodeRunner("dummy_address_eoa", "dummy_checkpoint_dir")
        runner.start()

        common_patches["mock_main"].assert_called_once()
        mock_telemetry_session.assert_called_once_with(
            1500,  # duration_ms: (3001.5 - 3000.0) * 1000
            "test_user_789",  # user_id
            0.50,  # goal_pct
        )

    def test_start_with_multiple_episodes(self, common_patches):
        """Test that start() calls session telemetry for each completed episode."""
        mock_telemetry_session = common_patches["mock_telemetry_session"]

        self.setup_mocks(
            common_patches,
            time_values=[4000.0, 4001.0, 4002.0, 4003.0, 4004.0, 4005.0],
            user_id="test_user_multi",
            main_side_effect=[{"goal_percentage_3_min": 0.30}, {"goal_percentage_7_min": 0.70}]
        )

        runner = EpisodeRunner("dummy_address_eoa", "dummy_checkpoint_dir")
        runner.episode_count = 2  # Set to run 2 episodes
        runner.start()

        assert common_patches["mock_main"].call_count == 2

        expected_calls = [
            (
                1000,
                "test_user_multi",
                0.30,
            ),  # Episode 1: (4001.0 - 4000.0) * 1000, goal 0.30
            (
                2000,
                "test_user_multi",
                0.70,
            ),  # Episode 2: (4002.0 - 4000.0) * 1000, goal 0.70
        ]
        assert mock_telemetry_session.call_count == 2
        actual_calls = [call.args for call in mock_telemetry_session.call_args_list]
        assert actual_calls == expected_calls

    def test_start_no_telemetry_if_no_episodes_complete(self, common_patches):
        """Test that start() does not call session telemetry if no episodes complete."""
        mock_telemetry_session = common_patches["mock_telemetry_session"]

        self.setup_mocks(
            common_patches,
            time_values=[5000.0, 5005.0],
            user_id="test_user_none",
            main_side_effect=KeyboardInterrupt("Immediate stop")
        )

        runner = EpisodeRunner("dummy_address_eoa", "dummy_checkpoint_dir")
        runner.start()

        common_patches["mock_main"].assert_called_once()
        mock_telemetry_session.assert_not_called()
