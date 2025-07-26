from pathlib import Path
import tempfile

from huggingface_hub import HfApi
from mbag.rllib.bc import BC
from mbag.rllib.training_utils import (
    load_policies_from_checkpoint,
)

from blockassist.globals import get_logger
from blockassist import telemetry
import io
import json


_LOG = get_logger()


def load_rllib_checkpoint(checkpoint_path):
    _LOG.info(f"Loading checkpoint from {checkpoint_path}")

    load_policies_mapping = {}
    exclude_loaded_policy_modules = []

    trainer = BC(BC.get_default_config())
    load_policies_from_checkpoint(
        checkpoint_path,
        trainer,
        lambda policy_id: load_policies_mapping.get(policy_id),
        lambda param_name: not any(
            param_name.startswith(module_name)
            for module_name in exclude_loaded_policy_modules
        ),
    )

    if checkpoint_path is not None:
        _LOG.info(f"Restoring checkpoint at {checkpoint_path}")

        old_set_state = trainer.__setstate__

        def new_set_state(checkpoint_data):
            # Remove config information from checkpoint_data so we don't override
            # the current config.
            if "config" in checkpoint_data:
                del checkpoint_data["config"]
            for policy_state in checkpoint_data["worker"]["policy_states"].values():
                if "policy_spec" in policy_state:
                    del policy_state["policy_spec"]
                if "_optimizer_variables" in policy_state:
                    del policy_state["_optimizer_variables"]
            return old_set_state(checkpoint_data)

        trainer.__setstate__ = new_set_state  # type: ignore

        trainer.restore(checkpoint_path)

    return trainer


def convert_checkpoint_to_hf(checkpoint_dir, out_dir = None, arch="custom"):
    trainer = load_rllib_checkpoint(checkpoint_dir)
    _LOG.info(f"Loaded trainer: {trainer}")

    if not out_dir:
        out_dir = tempfile.mkdtemp(prefix="hf_")

    # Create output directory
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Save trainer checkpoint in HF directory
    trainer_path = out_path / "trainer_checkpoint"
    trainer.save(str(trainer_path))

    config_json = {
        "model_type": "blockassist_bc",
        "architecture": arch,
        "checkpoint_dir": str(checkpoint_dir),
        "trainer_type": "BC"
    }

    with open(out_path / "config.json", "w") as f:
        json.dump(config_json, f, indent=2)

    # Create basic README.md
    readme_content = f"""# BlockAssist BC Model

This model was trained using the Minecraft Building Assistant Game (MBAG) framework as part of the BlockAssist program!

- Architecture: {arch}
- Source checkpoint: {checkpoint_dir}
- Trainer type: BC (Behavioral Cloning)

"""

    with open(out_path / "README.md", "w") as f:
        f.write(readme_content)

    _LOG.info(f"HuggingFace model files created in {out_dir}")
    return out_dir


def upload_to_huggingface(model_path: Path, user_id: str, repo_id: str, chain_metadata_dict: dict | None = None, hf_token: str | None = None) -> None:
    if not model_path.exists():
        raise FileNotFoundError(f"Model directory does not exist: {model_path}")

    try:
        api = HfApi(token=hf_token)
        api.create_repo(repo_id=repo_id, repo_type="model", exist_ok=True)
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
            _LOG.info(f"Uploaded metadata dictionary")

        # Calculate total size
        total_size = sum(f.stat().st_size for f in model_path.rglob("*") if f.is_file())
        _LOG.info(f"Successfully uploaded model to HuggingFace: {repo_id} with size {total_size / 1024 / 1024:.2f} MB")
        telemetry.push_telemetry_event_uploaded(total_size, user_id, repo_id)

    except Exception as e:
        _LOG.error(f"Failed to upload model to HuggingFace: {e}", exc_info=True)
        raise
