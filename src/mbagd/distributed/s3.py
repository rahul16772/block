import zipfile
from pathlib import Path
import boto3

from mbagd.globals import get_logger

_LOG = get_logger()


def get_latest_checkpoint_dir_and_zip(
    episode_dir: str = "mbag-repo/data/assistancezero_assistant/checkpoint_002000",
) -> str:
    """
    Finds the latest timestamped directory in the episode path and zips it up.

    Args:
        episode_dir: Base path to the episode directory

    Returns:
        str: Path to the created zip file
    """
    checkpoint_path = Path(episode_dir)

    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint path does not exist: {checkpoint_path}")

    # Find all evaluate_* directories (timestamped directories)
    evaluate_dirs = [
        d
        for d in checkpoint_path.iterdir()
        if d.is_dir() and d.name.startswith("evaluate_")
    ]

    if not evaluate_dirs:
        raise ValueError(
            f"No timestamped evaluation directories found in {checkpoint_path}"
        )

    # Sort by modification time to get the latest
    latest_dir = max(evaluate_dirs, key=lambda d: d.stat().st_mtime)
    _LOG.info(f"Found latest checkpoint directory: {latest_dir}")

    # Create zip file name based on the directory name
    zip_filename = f"{latest_dir.name}.zip"
    zip_path = checkpoint_path / zip_filename

    # Remove existing zip if it exists
    if zip_path.exists():
        zip_path.unlink()

    # Create zip file
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in latest_dir.rglob("*"):
            if file_path.is_file():
                # Calculate relative path for the zip
                arcname = file_path.relative_to(latest_dir)
                zipf.write(file_path, arcname)

    _LOG.info(
        f"Created zip file: {zip_path} (size: {zip_path.stat().st_size / 1024 / 1024:.2f} MB)"
    )
    return str(zip_path)


def upload_zip_to_s3(
    zip_file_path: str, bucket_name: str, s3_key: str | None = None
) -> str:
    zip_path = Path(zip_file_path)

    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file does not exist: {zip_path}")

    # Use filename as S3 key if not provided
    if s3_key is None:
        s3_key = zip_path.name

    _LOG.info(f"Uploading {zip_path} to S3 bucket {bucket_name} with key {s3_key}")

    s3_client = boto3.client("s3")

    try:
        s3_client.upload_file(str(zip_path), bucket_name, s3_key)
        s3_uri = f"s3://{bucket_name}/{s3_key}"
        _LOG.info(f"Successfully uploaded to {s3_uri}")
        return s3_uri
    except Exception as e:
        _LOG.error(f"Failed to upload {zip_path} to S3: {e}")
        raise


def zip_and_upload_latest_episode(
    checkpoint_base_path: str = "mbag-repo/data/assistancezero_assistant/checkpoint_002000",
    bucket_name: str = "blockassist-episode",
    s3_key: str | None = None,
) -> tuple[str, str]:
    zip_path = get_latest_checkpoint_dir_and_zip(checkpoint_base_path)
    s3_uri = upload_zip_to_s3(zip_path, bucket_name, s3_key)
    return zip_path, s3_uri

# FIX!!
if __name__ == "__main__":
    print(zip_and_upload_latest_episode())
