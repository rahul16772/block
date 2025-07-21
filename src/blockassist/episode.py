import asyncio
from pathlib import Path

from mbag.environment.goals import ALL_GOAL_GENERATORS
from mbag.scripts.evaluate import ex

from blockassist.data import backup_existing_evaluate_dirs
from blockassist.globals import _DATA_DIR, get_logger
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
    ex.run(
        named_configs=["human_with_assistant", "blockassist"],
        config_updates={"assistant_checkpoint": "data/base_checkpoint"},
    )


class EpisodeRunner:
    """Class recording a building episode in Minecraft."""

    def __init__(
        self,
        human_alone: bool = True,
        assistant_checkpoint: str = "data/base_checkpoint",
    ):
        self.human_alone = human_alone
        self.assistant_checkpoint = assistant_checkpoint

        self.episode_count = 1

        self.building_started = asyncio.Event()
        self.building_ended = asyncio.Event()

    def started(self):
        return self.building_started.wait()

    def ended(self):
        return self.building_ended.wait()

    def start(self):
        # TODO: Fix early exit when Minecraft instances go down.
        # original_get_observations = MalmoClient.get_observations

        # def wrapped_get_observations(self, player_index):
        #     agent_host = self.agent_hosts[player_index]
        #     world_state = agent_host.getWorldState()
        #     if not world_state.is_mission_running:
        #         raise KeyboardInterrupt("Mission ended unexpectedly.")

        #     return original_get_observations(self, player_index)

        # MalmoClient.get_observations = wrapped_get_observations

        _LOG.info("Backing up old evaluate directories.")
        backup_existing_evaluate_dirs(Path(_DATA_DIR))

        self.building_started.set()
        for _ in range(self.episode_count):
            try:
                run_main()
            except KeyboardInterrupt:
                _LOG.info("Episode recording stopped!")

        self.building_ended.set()

        # MalmoClient.get_observations = original_get_observations

        # try:
        #     zip_and_upload_latest_episode(
        #         "data/base_checkpoint",
        #         "blockassist-episode",
        #     )
        #     _LOG.info("Episode data uploaded successfully.")
        # except boto3.exceptions.S3UploadFailedError:  # type: ignore
        #     _LOG.error("Failed to upload episode data to S3.", exc_info=True)
