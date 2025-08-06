from pathlib import Path

import boto3
from botocore import UNSIGNED
from botocore.client import Config

from blockassist.globals import get_logger

_LOG = get_logger()


def upload_zip_to_s3(
    zip_file_path: str, bucket_name: str, s3_key: str | None = None
) -> str:
    zip_path = Path(zip_file_path)
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file does not exist: {zip_path}")

    # Use filename as S3 key if not provided
    if s3_key is None:
        s3_key = zip_path.name

    try:
        s3_client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
        s3_client.upload_file(str(zip_path), bucket_name, s3_key)
        s3_uri = f"s3://{bucket_name}/{s3_key}"
        _LOG.info(f"Successfully uploaded to {s3_uri}")
        return s3_uri
    except Exception as e:
        _LOG.error(f"Failed to upload {zip_path} to S3: {e}")

