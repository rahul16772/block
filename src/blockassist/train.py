import asyncio
import os
from pathlib import Path
import shutil

from mbag.environment.goals import ALL_GOAL_GENERATORS
from mbag.scripts.convert_human_data_to_rllib import ex as convert_ex
from mbag.scripts.train import ex as train_ex

from blockassist.globals import _DATA_DIR, _DEFAULT_CHECKPOINT, get_logger
from blockassist.goals.generator import BlockAssistGoalGenerator

_LOG = get_logger()


def run_train_main(mbag_config: dict, rllib_path: str):
    ALL_GOAL_GENERATORS["blockassist"] = BlockAssistGoalGenerator
    result = train_ex.run(
        named_configs=["bc_human"],
        config_updates={
            "data_split": "human_with_assistant",
            "goal_generator": "blockassist",
            "input": rllib_path,
            "num_training_iters": 1
        },
    ).result
    assert result
    return result


@convert_ex.named_config
def blockassist_convert():
    max_seq_len = 32  # noqa: F841
    inventory_player_indices = [0, 1] # noqa: F841

    data_dir = _DEFAULT_CHECKPOINT
    data_glob = os.path.join(data_dir, "**", "episodes.zip")  # noqa: F841
    out_dir = os.path.join(data_dir, "..", "rllib")  # noqa: F841


def run_convert_main():
    result = convert_ex.run(named_configs=["blockassist_convert"]).result
    assert result
    return result


class TrainingRunner:
    """Class for managing a Minecraft bot training session."""

    def __init__(self):
        self.training_started = asyncio.Event()
        self.training_ended = asyncio.Event()

    def started(self):
        return self.training_started.wait()

    def ended(self):
        return self.training_ended.wait()

    def start(self):
        self.training_started.set()

        _LOG.info("Conversion started!")
        shutil.rmtree(Path(_DATA_DIR) / "rllib", ignore_errors=True)
        convert_result = run_convert_main()
        try:
            _LOG.info("Training started!")
            run_train_main(
                mbag_config=convert_result["mbag_config"],
                rllib_path=convert_result["out_dir"],
            )
        except KeyboardInterrupt:
            _LOG.info("Training stopped!")
        finally:
            self.training_ended.set()
