import asyncio
from pathlib import Path
import time

from mbag.environment.goals import ALL_GOAL_GENERATORS
from mbag.scripts.evaluate import ex

from blockassist import telemetry
from blockassist.data import backup_existing_evaluate_dirs
from blockassist.globals import _DATA_DIR, get_identifier, get_logger
from blockassist.goals.generator import BlockAssistGoalGenerator

_LOG = get_logger()


@ex.named_config
def blockassist():
    num_simulations = 1  # noqa: F841
    goal_set = "test"
    house_id = None

    env_config_updates = {  # noqa: F841
        "num_players": 2,
        "goal_generator_config": {
            "goal_generator": "blockassist",
            "goal_generator_config": {"subset": goal_set, "house_id": house_id},
        },
        "malmo": {"action_delay": 0.8, "rotate_spectator": False},
        "horizon": 10000,
        "players": [
            {
                "player_name": "human",
            },
            {
                "player_name": "assistant",
            },
        ],
    }


def run_main():
    ALL_GOAL_GENERATORS["blockassist"] = BlockAssistGoalGenerator
    result = ex.run(
        named_configs=["human_with_assistant", "blockassist"],
        config_updates={"assistant_checkpoint": "data/base_checkpoint"},
    ).result
    assert result
    return result


class EpisodeRunner:
    """Class recording a building episode in Minecraft."""

    def __init__(
        self,
        human_alone: bool = True,
        assistant_checkpoint: str = "data/base_checkpoint",
    ):
        self.data_dir = Path(_DATA_DIR)

        self.human_alone = human_alone
        self.assistant_checkpoint = assistant_checkpoint

        self.completed_episode_count = 0
        self.episode_count = 1

        self.start_time = time.time()
        self.end_time = None

        self.building_started = asyncio.Event()
        self.building_ended = asyncio.Event()

    def wait_for_start(self, timeout=60 * 2): # minutes
        return asyncio.wait_for(self.building_started.wait(), timeout)

    def wait_for_end(self, timeout=60 * 2): # hours
        return asyncio.wait_for(self.building_ended.wait(), timeout)

    def get_last_goal_percentage_min(self, result):
        # Find the highest numbered goal_percentage_x_min key
        goal_percentage_keys = [
            key for key in result.keys() if key.startswith("goal_percentage_")
        ]
        if not goal_percentage_keys:
            return 0.0

        # Extract the minute values and find the maximum
        max_x = max(int(key.split("_")[-2]) for key in goal_percentage_keys)
        return result[f"goal_percentage_{max_x}_min"]

    def after_episode(self, result):
        self.completed_episode_count += 1

        duration_ms = int((time.time() - self.start_time) * 1000)
        telemetry.push_telemetry_event_session(
            duration_ms, get_identifier(), self.get_last_goal_percentage_min(result)
        )

    def before_session(self):
        _LOG.info("Episode recording session started.")
        self.building_started.set()

    def after_session(self):
        _LOG.info("Episode recording session ended.")
        self.building_ended.set()
        self.end_time = time.time()

    def start(self):
        # TODO: Fix early exit when Minecraft instances go down.

        _LOG.info("Backing up old evaluate directories.")
        backup_existing_evaluate_dirs(self.data_dir)

        self.before_session()
        for _ in range(self.episode_count):
            try:
                _LOG.info(f"Episode {self.episode_count} recording started.")
                result = run_main()
                self.after_episode(result)
            except KeyboardInterrupt:
                _LOG.info(f"Episode {self.episode_count} recording stopped!")

        self.after_session()

        # TODO: Fix uploading episodes to S3 post-backup flow.
        # try:
        #     zip_and_upload_latest_episode(
        #         "data/base_checkpoint",
        #         "blockassist-episode",
        #     )
        #     _LOG.info("Episode data uploaded successfully.")
        # except boto3.exceptions.S3UploadFailedError:  # type: ignore
        #     _LOG.error("Failed to upload episode data to S3.", exc_info=True)
