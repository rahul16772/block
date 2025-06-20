from mbag.rllib.bc import BC
from mbag.rllib.training_utils import (
    load_policies_from_checkpoint,
)

from mbagd.globals import get_logger

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


def convert_checkpoint_to_hf(checkpoint_dir, out_dir, arch="custom"):
    trainer = load_rllib_checkpoint(checkpoint_dir)
    print(trainer)

    # create_hf_model_files(policy_state, out_dir, params, arch)
