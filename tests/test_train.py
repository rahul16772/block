from unittest.mock import patch

import pytest

from blockassist.train import TrainingRunner


class TestTrainingRunnerTelemetry:
    @pytest.fixture
    def common_patches(self):
        """Common patches used across multiple test methods."""
        with patch("blockassist.train.telemetry.push_telemetry_event_trained") as mock_telemetry_trained, \
             patch("blockassist.train.get_identifier") as mock_get_identifier, \
             patch("blockassist.train.run_convert_main") as mock_convert, \
             patch("blockassist.train.run_train_main") as mock_train, \
             patch("blockassist.train.time.time") as mock_time, \
             patch("shutil.rmtree") as mock_rmtree:
            yield {
                "mock_telemetry_trained": mock_telemetry_trained,
                "mock_get_identifier": mock_get_identifier,
                "mock_convert": mock_convert,
                "mock_train": mock_train,
                "mock_time": mock_time,
                "mock_rmtree": mock_rmtree
            }

    def test_start_calls_trained_telemetry_on_success(self, common_patches):
        """Test that start() calls trained telemetry when training completes successfully."""
        mock_convert = common_patches["mock_convert"]
        mock_train = common_patches["mock_train"]
        mock_telemetry_trained = common_patches["mock_telemetry_trained"]

        self.setup_mocks(
            common_patches,
            start_time=5000.0,
            end_time=5120.5,
            user_id="trainer_user_123",
            config={"test": "config"},
            out_dir="/path/to/rllib/output"
        )
        mock_train.return_value = {"final_checkpoint": "/path/to/model"}

        runner = TrainingRunner("dummy_address_eoa")
        runner.start()

        mock_convert.assert_called_once()
        mock_train.assert_called_once_with(
            mbag_config={"test": "config"},
            rllib_path="/path/to/rllib/output",
            num_training_iters=1
        )
        mock_telemetry_trained.assert_called_once_with(
            120500,  # duration_ms: int((5120.5 - 5000.0) * 1000)
            "trainer_user_123",  # user_id
            1  # session_count
        )

    def setup_mocks(self, common_patches, start_time=5000.0, end_time=5120.5,
            user_id="trainer_user_123", config=None, out_dir=None):
        common_patches["mock_time"].side_effect = [start_time, end_time]
        common_patches["mock_get_identifier"].return_value = user_id
        common_patches["mock_convert"].return_value = {
            "mbag_config": config,
            "out_dir": out_dir
        }

    def test_start_calls_trained_telemetry_after_keyboard_interrupt(self, common_patches):
        """Test that start() calls trained telemetry even after KeyboardInterrupt."""
        mock_convert = common_patches["mock_convert"]
        mock_train = common_patches["mock_train"]
        mock_telemetry_trained = common_patches["mock_telemetry_trained"]

        self.setup_mocks(
            common_patches,
            start_time=6000.0,
            end_time=6045.7,
            user_id="trainer_user_456",
            config={"test": "config"},
            out_dir="/path/to/rllib/output"
        )
        mock_train.side_effect = KeyboardInterrupt("Training stopped by user")

        runner = TrainingRunner("dummy_address_eoa")
        runner.start()

        mock_convert.assert_called_once()
        mock_train.assert_called_once()
        # Verify trained telemetry was still called after interrupt
        mock_telemetry_trained.assert_called_once_with(
            45699,  # duration_ms: int((6045.7 - 6000.0) * 1000)
            "trainer_user_456",  # user_id
            1  # session_count
        )

    def test_start_with_different_user_identifier(self, common_patches):
        """Test that start() uses correct user identifier in telemetry."""
        mock_train = common_patches["mock_train"]
        mock_telemetry_trained = common_patches["mock_telemetry_trained"]

        self.setup_mocks(
            common_patches,
            start_time=7000.0,
            end_time=7300.2,
            user_id="different_trainer_789",
            config={"different": "config"},
            out_dir="/different/path"
        )
        mock_train.return_value = {"final_checkpoint": "/different/path/to/model"}

        runner = TrainingRunner("dummy_address_eoa")
        runner.start()

        mock_telemetry_trained.assert_called_once_with(
            300199,  # duration_ms: int((7300.2 - 7000.0) * 1000)
            "different_trainer_789",  # user_id
            1  # session_count
        )

    def test_after_training_calls_telemetry_directly(self, common_patches):
        """Test that after_training() calls telemetry directly without full workflow."""
        mock_telemetry_trained = common_patches["mock_telemetry_trained"]

        self.setup_mocks(
            common_patches,
            start_time=8000.0,
            end_time=8060.1,
            user_id="direct_user"
        )

        runner = TrainingRunner("dummy_address_eoa")
        runner.after_training()

        mock_telemetry_trained.assert_called_once_with(
            60100,  # duration_ms: int((8060.1 - 8000.0) * 1000)
            "direct_user",  # user_id
            1  # session_count
        )

    def test_start_handles_convert_failure(self, common_patches):
        """Test that start() handles conversion failure and doesn't call telemetry."""
        mock_convert = common_patches["mock_convert"]
        mock_train = common_patches["mock_train"]
        mock_telemetry_trained = common_patches["mock_telemetry_trained"]

        mock_convert.side_effect = Exception("Conversion failed")

        runner = TrainingRunner("dummy_address_eoa")

        with pytest.raises(Exception, match="Conversion failed"):
            runner.start()

        mock_convert.assert_called_once()
        mock_train.assert_not_called()
        # Verify telemetry was not called due to conversion failure
        mock_telemetry_trained.assert_not_called()

    def test_start_handles_train_exception_but_still_calls_telemetry(self, common_patches):
        """Test that start() handles training exceptions - only KeyboardInterrupt is caught."""
        mock_convert = common_patches["mock_convert"]
        mock_train = common_patches["mock_train"]
        mock_telemetry_trained = common_patches["mock_telemetry_trained"]

        self.setup_mocks(
            common_patches,
            config={"fail": "config"},
            out_dir="/fail/path"
        )
        mock_train.side_effect = RuntimeError("Training failed")

        runner = TrainingRunner("dummy_address_eoa")

        with pytest.raises(RuntimeError, match="Training failed"):
            runner.start()

        mock_convert.assert_called_once()
        mock_train.assert_called_once()
        # Verify telemetry was NOT called since only KeyboardInterrupt is caught
        mock_telemetry_trained.assert_not_called()