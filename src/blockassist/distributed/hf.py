from pathlib import Path

from huggingface_hub import HfApi

from blockassist.globals import get_logger
from blockassist import telemetry
import io
import json


_LOG = get_logger()


def upload_to_huggingface(
    model_path: Path, user_id: str, repo_id: str, hf_token: str | None = None, chain_metadata_dict: dict | None = None,
) -> None:
    if not model_path.exists():
        raise FileNotFoundError(f"Model directory does not exist: {model_path}")

    try:
        api = HfApi(token=hf_token)
        api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True, private=True)
        api.upload_folder(repo_id=repo_id, repo_type="model", folder_path=model_path)

        if chain_metadata_dict:
            metadata_json = json.dumps(chain_metadata_dict, indent=2)
            metadata_bytes = io.BytesIO(metadata_json.encode("utf-8"))
            api.upload_file(
                path_or_fileobj=metadata_bytes,
                path_in_repo="gensyn.json",
                repo_id=repo_id,
                repo_type="model"
            )
            _LOG.info("Uploaded metadata dictionary")

        # Calculate total size
        total_size = sum(f.stat().st_size for f in model_path.rglob("*") if f.is_file())
        _LOG.info(
            f"Successfully uploaded model to HuggingFace: {repo_id} with size {total_size / 1024 / 1024:.2f} MB"
        )
        telemetry.push_telemetry_event_uploaded(total_size, user_id, repo_id)

    except Exception as e:
        _LOG.error(f"Failed to upload model to HuggingFace: {e}", exc_info=True)
        raise
