from pathlib import Path
import shutil
import tempfile
import os
import pickle
import zipfile

from blockassist.globals import get_identifier, get_logger
from blockassist.distributed.s3 import upload_zip_to_s3

from mbag.evaluation.episode import MbagEpisode

_LOG = get_logger()

## Evaluate data utilities.


def get_all_evaluate_dirs(data_dir: Path) -> list[Path]:
    checkpoint_dir = data_dir
    evaluate_dirs = [
        d
        for d in checkpoint_dir.iterdir()
        if d.is_dir() and d.name.startswith("evaluate_")
    ]
    return evaluate_dirs


def backup_existing_evaluate_dirs(data_dir: Path) -> None:
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")

    for d in get_all_evaluate_dirs(data_dir):
        evaluate_dir = data_dir / "evaluate"
        backup_path = evaluate_dir / d.name
        if not backup_path.exists():
            _LOG.info(f"Backing up {d} to {backup_path}")
            shutil.copytree(d, backup_path)


def get_all_evaluate_zips(data_dir: Path) -> list[Path]:
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")

    evaluate_dirs = get_all_evaluate_dirs(data_dir)
    if not evaluate_dirs:
        raise ValueError(f"No timestamped evaluation directories found in {data_dir}")

    zip_paths = []
    for evaluate_dir in evaluate_dirs:
        _LOG.info(f"Processing evaluation directory: {evaluate_dir}")

        # Create zip file of entire directory + delete existing.
        zip_filename = f"{evaluate_dir.name}.zip"
        zip_path = data_dir / zip_filename
        if zip_path.exists():
            zip_path.unlink()

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in evaluate_dir.rglob("*"):
                if file_path.is_file():
                    # Calculate relative path for the zip
                    arcname = file_path.relative_to(evaluate_dir)
                    zipf.write(file_path, arcname)

        _LOG.info(
            f"Created zip file: {zip_path} (size: {zip_path.stat().st_size / 1024 / 1024:.2f} MB)"
        )
        zip_paths.append(zip_path)

    return zip_paths


## Training data utilities.


def load_episodes_from_evaluate_dirs(
    evaluate_dirs: list[Path] = [],
) -> list[MbagEpisode]:
    episodes = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        for evaluate_dir in evaluate_dirs:
            for d in evaluate_dir.iterdir():
                if d.is_dir():
                    episodes_zip = d / "episodes.zip"
                    if episodes_zip.exists():
                        _LOG.info(f"Extracting episodes zip: {episodes_zip}")

                        episode_extract_dir = (
                            temp_path / f"{evaluate_dir.name}_{d.name}"
                        )
                        episode_extract_dir.mkdir(exist_ok=False)
                        with zipfile.ZipFile(episodes_zip, "r") as zip_file:
                            zip_file.extractall(episode_extract_dir)

                        episode_files = []
                        for root, _, files in os.walk(episode_extract_dir):
                            for file in files:
                                if file.endswith(".pickle"):
                                    episode_files.append(Path(root) / file)

                        for episode_file in episode_files:
                            _LOG.info(f"Loading episode file: {episode_file}")
                            try:
                                # Load the episode file with pickle
                                with open(episode_file, "rb") as f:
                                    episodes_data = pickle.load(f)

                                if (
                                    isinstance(episodes_data, list)
                                    and len(episodes_data) > 0
                                ):
                                    for episode in episodes_data:
                                        if isinstance(episode, MbagEpisode):
                                            episodes.append(episode)
                                elif isinstance(episodes_data, MbagEpisode):
                                    episodes.append(episodes_data)

                            except Exception as e:
                                raise RuntimeError(
                                    f"Failed to load episode from {episode_file}: {e}"
                                )

        _LOG.info(f"Loaded {len(episodes)} episodes from {evaluate_dirs}")
        return episodes


def zip_and_upload_episodes(data_dir: Path, bucket_name: str) -> list[str]:
    """
    Zip all episode directories and upload them to S3.

    Args:
        data_dir: Path to the data directory containing evaluate_ directories
        bucket_name: S3 bucket name for upload

    Returns:
        List of S3 URIs of the uploaded zip files
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")

    # Get all evaluate directories
    evaluate_dirs = get_all_evaluate_dirs(data_dir)
    if not evaluate_dirs:
        raise ValueError(f"No timestamped evaluation directories found in {data_dir}")

    s3_uris = []
    for evaluate_dir in evaluate_dirs:
        _LOG.info(f"Processing evaluation directory: {evaluate_dir}")

        # Create zip file of the directory
        zip_filename = f"{evaluate_dir.name}.zip"
        zip_path = data_dir / zip_filename

        # Remove existing zip if it exists
        if zip_path.exists():
            zip_path.unlink()

        _LOG.info(f"Creating zip file: {zip_path}")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in evaluate_dir.rglob("*"):
                if file_path.is_file():
                    # Calculate relative path for the zip
                    arcname = file_path.relative_to(evaluate_dir)
                    zipf.write(file_path, arcname)

        zip_size_mb = zip_path.stat().st_size / 1024 / 1024
        _LOG.info(f"Created zip file: {zip_path} (size: {zip_size_mb:.2f} MB)")

        # Upload to S3
        s3_uri = upload_zip_to_s3(str(zip_path), bucket_name, f"{get_identifier()}/{zip_filename}")
        s3_uris.append(s3_uri)

    return s3_uris
