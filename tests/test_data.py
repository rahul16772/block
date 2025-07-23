import pytest
import tempfile
import zipfile
from pathlib import Path

from blockassist.data import (
    get_all_evaluate_dirs,
    backup_existing_evaluate_dirs,
    get_all_evaluate_zips,
)


class TestGetEvaluationDirs:
    def test_get_evaluation_dirs_empty_directory(self):
        """Test that get_evaluation_dirs returns empty list for directory with no evaluate_ dirs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            # Create the base_checkpoint subdirectory that the function expects
            checkpoint_dir = data_dir / "base_checkpoint"
            checkpoint_dir.mkdir()

            result = get_all_evaluate_dirs(data_dir)
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

            result = get_all_evaluate_dirs(data_dir)
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

            result = get_all_evaluate_dirs(data_dir)
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
            backup_existing_evaluate_dirs(data_dir)

            # Verify backup directories were created (data_dir/evaluate/evaluate_name/)
            evaluate_root = data_dir / "evaluate"
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

        with pytest.raises(FileNotFoundError, match="Data directory does not exist"):
            backup_existing_evaluate_dirs(nonexistent_path)

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
            backup_existing_evaluate_dirs(data_dir)

            # evaluate directory should not be created if no evaluate dirs exist
            evaluate_dir = data_dir / "evaluate"
            assert not evaluate_dir.exists()


class TestGetAllEvaluateZips:
    def test_get_all_evaluate_zips_success(self):
        """Test successful creation of zip files from all evaluate directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            checkpoint_dir = data_dir / "base_checkpoint"
            checkpoint_dir.mkdir()

            # Create evaluate directories with content
            eval_dir1 = checkpoint_dir / "evaluate_20250101_120000"
            eval_dir2 = checkpoint_dir / "evaluate_20250102_130000"
            eval_dir1.mkdir()
            eval_dir2.mkdir()

            # Add content to directories
            (eval_dir1 / "results1.json").write_text('{"old": "data"}')
            (eval_dir2 / "results2.json").write_text('{"new": "data"}')
            (eval_dir2 / "subdir").mkdir()
            (eval_dir2 / "subdir" / "nested.txt").write_text("nested content")

            result = get_all_evaluate_zips(data_dir)

            # Verify zip files were created in the data_dir
            assert len(result) == 2
            expected_zip_names = {"evaluate_20250101_120000.zip", "evaluate_20250102_130000.zip"}
            actual_zip_names = {zip_path.name for zip_path in result}
            assert actual_zip_names == expected_zip_names

            # Verify all zip files exist
            for zip_path in result:
                assert zip_path.exists()
                assert zip_path.parent == data_dir

            # Verify zip contents for one of them
            eval1_zip = data_dir / "evaluate_20250101_120000.zip"
            with zipfile.ZipFile(eval1_zip, "r") as zipf:
                zip_contents = zipf.namelist()
                assert "results1.json" in zip_contents
                assert zipf.read("results1.json").decode() == '{"old": "data"}'

            eval2_zip = data_dir / "evaluate_20250102_130000.zip"
            with zipfile.ZipFile(eval2_zip, "r") as zipf:
                zip_contents = zipf.namelist()
                assert "results2.json" in zip_contents
                assert "subdir/nested.txt" in zip_contents
                assert zipf.read("results2.json").decode() == '{"new": "data"}'
                assert zipf.read("subdir/nested.txt").decode() == "nested content"

    def test_get_all_evaluate_zips_nonexistent_data_dir(self):
        """Test that function raises FileNotFoundError for nonexistent data directory."""
        nonexistent_path = Path("/nonexistent/path")

        with pytest.raises(FileNotFoundError, match="Data directory does not exist"):
            get_all_evaluate_zips(nonexistent_path)

    def test_get_all_evaluate_zips_no_evaluate_dirs(self):
        """Test that function raises ValueError when no evaluate directories exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            checkpoint_dir = data_dir / "base_checkpoint"
            checkpoint_dir.mkdir()

            # Create some non-evaluate directories
            (checkpoint_dir / "other_dir").mkdir()
            (checkpoint_dir / "regular_file.txt").touch()

            with pytest.raises(
                ValueError, match="No timestamped evaluation directories found"
            ):
                get_all_evaluate_zips(data_dir)

    def test_get_all_evaluate_zips_replaces_existing_zip(self):
        """Test that existing zip files are replaced."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            checkpoint_dir = data_dir / "base_checkpoint"
            checkpoint_dir.mkdir()

            # Create evaluate directory
            eval_dir = checkpoint_dir / "evaluate_test"
            eval_dir.mkdir()
            (eval_dir / "new_content.txt").write_text("new content")

            # Create existing zip file
            existing_zip = data_dir / "evaluate_test.zip"
            with zipfile.ZipFile(existing_zip, "w") as zipf:
                zipf.writestr("old_content.txt", "old content")

            result = get_all_evaluate_zips(data_dir)

            # Verify new zip was created
            assert len(result) == 1
            assert result[0] == existing_zip
            assert existing_zip.exists()

            # Verify content is new (not old)
            with zipfile.ZipFile(existing_zip, "r") as zipf:
                zip_contents = zipf.namelist()
                assert "new_content.txt" in zip_contents
                assert "old_content.txt" not in zip_contents
