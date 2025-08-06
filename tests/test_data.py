import tempfile
from pathlib import Path

import pytest

from blockassist.data import (
    backup_evaluate_dirs,
    get_all_evaluate_dirs,
    get_total_episodes,
)


class TestGetEvaluationDirs:
    def test_get_evaluation_dirs_empty_directory(self):
        """Test that get_evaluation_dirs returns empty list for directory with no evaluate_ dirs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            # Create the base_checkpoint subdirectory that the function expects
            checkpoint_dir = data_dir / "base_checkpoint"
            checkpoint_dir.mkdir()

            result = get_all_evaluate_dirs(checkpoint_dir)
            assert result == []

    def test_get_evaluation_dirs_with_evaluate_dirs(self):
        """Test that get_evaluation_dirs returns only directories starting with 'evaluate_'."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            checkpoint_dir = data_dir / "base_checkpoint"
            checkpoint_dir.mkdir()

            # Create some directories in the base_checkpoint directory
            (checkpoint_dir / "evaluate_20250101_120000").mkdir()
            (checkpoint_dir / "evaluate_20250102_130000").mkdir()
            (checkpoint_dir / "other_dir").mkdir()
            (checkpoint_dir / "not_evaluate").mkdir()

            # Create a file that starts with evaluate_ (should be ignored)
            (checkpoint_dir / "evaluate_file.txt").touch()

            result = get_all_evaluate_dirs(checkpoint_dir)
            result_names = [d.name for d in result]

            assert len(result) == 2
            assert "evaluate_20250101_120000" in result_names
            assert "evaluate_20250102_130000" in result_names
            assert "other_dir" not in result_names
            assert "not_evaluate" not in result_names

    def test_get_evaluation_dirs_mixed_content(self):
        """Test get_evaluation_dirs with mixed files and directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            checkpoint_dir = data_dir / "base_checkpoint"
            checkpoint_dir.mkdir()

            # Create evaluate directories
            (checkpoint_dir / "evaluate_test1").mkdir()
            (checkpoint_dir / "evaluate_test2").mkdir()

            # Create non-evaluate directories
            (checkpoint_dir / "some_other_dir").mkdir()

            # Create files (should be ignored)
            (checkpoint_dir / "evaluate_file.txt").touch()
            (checkpoint_dir / "regular_file.txt").touch()

            result = get_all_evaluate_dirs(checkpoint_dir)
            result_names = [d.name for d in result]

            assert len(result) == 2
            assert all(name.startswith("evaluate_") for name in result_names)
            assert all(d.is_dir() for d in result)


class TestBackupExistingEvaluateDirs:
    def test_backup_existing_evaluate_dirs_success(self):
        """Test successful backup of evaluate directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            checkpoint_dir = data_dir / "base_checkpoint"
            checkpoint_dir.mkdir()

            # Create evaluate directories with some content
            eval_dir1 = checkpoint_dir / "evaluate_20250101_120000"
            eval_dir2 = checkpoint_dir / "evaluate_20250102_130000"
            eval_dir1.mkdir()
            eval_dir2.mkdir()

            # Add some files to the evaluate directories
            (eval_dir1 / "results.json").write_text('{"test": "data1"}')
            (eval_dir2 / "results.json").write_text('{"test": "data2"}')
            (eval_dir1 / "subdir").mkdir()
            (eval_dir1 / "subdir" / "nested_file.txt").write_text("nested content")

            # Call backup function
            backup_evaluate_dirs(str(checkpoint_dir))

            # Verify backup directories were created (checkpoint_dir/evaluate/evaluate_name/)
            evaluate_root = checkpoint_dir / "evaluate"
            assert evaluate_root.exists()
            assert evaluate_root.is_dir()

            # Verify backed up directories exist
            backup_eval1 = evaluate_root / "evaluate_20250101_120000"
            backup_eval2 = evaluate_root / "evaluate_20250102_130000"
            assert backup_eval1.exists()
            assert backup_eval2.exists()

            # Verify content was copied correctly
            assert (backup_eval1 / "results.json").read_text() == '{"test": "data1"}'
            assert (backup_eval2 / "results.json").read_text() == '{"test": "data2"}'
            assert (
                backup_eval1 / "subdir" / "nested_file.txt"
            ).read_text() == "nested content"

    def test_backup_existing_evaluate_dirs_nonexistent_data_dir(self):
        """Test that backup raises FileNotFoundError for nonexistent data directory."""
        nonexistent_path = Path("/nonexistent/path")

        with pytest.raises(
            FileNotFoundError, match="Checkpoint directory does not exist"
        ):
            backup_evaluate_dirs(str(nonexistent_path))

    def test_backup_existing_evaluate_dirs_no_evaluate_dirs(self):
        """Test backup when no evaluate directories exist (should not fail)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            checkpoint_dir = data_dir / "base_checkpoint"
            checkpoint_dir.mkdir()

            # Create some non-evaluate directories
            (checkpoint_dir / "other_dir").mkdir()
            (checkpoint_dir / "regular_file.txt").touch()

            # Should not raise an exception
            backup_evaluate_dirs(str(checkpoint_dir))

            # evaluate directory should not be created if no evaluate dirs exist
            evaluate_dir = checkpoint_dir / "evaluate"
            assert not evaluate_dir.exists()


class TestGetTotalEpisodes:
    def test_get_total_episodes_empty_directory(self):
        """Test that get_total_episodes returns 0 for directory with no evaluate_ dirs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            checkpoint_dir = data_dir / "base_checkpoint"
            checkpoint_dir.mkdir()

            result = get_total_episodes(str(checkpoint_dir))
            assert result == 0

    def test_get_total_episodes_with_valid_sessions(self):
        """Test get_total_episodes with valid session directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            checkpoint_dir = data_dir / "base_checkpoint"
            checkpoint_dir.mkdir()

            # Create evaluate directories
            eval_dir1 = checkpoint_dir / "evaluate_20250101_120000"
            eval_dir2 = checkpoint_dir / "evaluate_20250102_130000"
            eval_dir1.mkdir()
            eval_dir2.mkdir()

            # Create valid session directories in first evaluate dir
            session1 = eval_dir1 / "1"
            session2 = eval_dir1 / "2"
            session1.mkdir()
            session2.mkdir()

            # Add required files to make sessions valid
            required_files = ['config.json', 'episodes.zip', 'metrics.json', 'run.json']
            for file in required_files:
                (session1 / file).touch()
                (session2 / file).touch()

            # Create valid session in second evaluate dir
            session3 = eval_dir2 / "1"
            session3.mkdir()
            for file in required_files:
                (session3 / file).touch()

            result = get_total_episodes(str(checkpoint_dir))
            assert result == 3

    def test_get_total_episodes_nonexistent_directory(self):
        """Test that get_total_episodes raises FileNotFoundError for nonexistent directory."""
        nonexistent_path = "/nonexistent/path"

        with pytest.raises(
            FileNotFoundError, match="Checkpoint directory does not exist"
        ):
            get_total_episodes(nonexistent_path)

    def test_get_total_episodes_mixed_evaluate_dirs(self):
        """Test get_total_episodes with mix of valid and invalid evaluate directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            checkpoint_dir = data_dir / "base_checkpoint"
            checkpoint_dir.mkdir()

            # Create evaluate directory with valid sessions
            eval_dir1 = checkpoint_dir / "evaluate_20250101_120000"
            eval_dir1.mkdir()

            session1 = eval_dir1 / "1"
            session1.mkdir()
            required_files = ['config.json', 'episodes.zip', 'metrics.json', 'run.json']
            for file in required_files:
                (session1 / file).touch()

            # Create evaluate directory with no valid sessions
            eval_dir2 = checkpoint_dir / "evaluate_20250102_130000"
            eval_dir2.mkdir()
            (eval_dir2 / "some_file.txt").touch()

            # Create non-evaluate directory (should be ignored)
            non_eval_dir = checkpoint_dir / "other_directory"
            non_eval_dir.mkdir()

            result = get_total_episodes(str(checkpoint_dir))
            assert result == 1
