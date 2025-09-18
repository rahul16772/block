import asyncio
import time
from pathlib import Path

from mbag.environment.goals import ALL_GOAL_GENERATORS
from mbag.scripts.evaluate import ex
from sacred.observers import FileStorageObserver

from blockassist import telemetry
from blockassist.globals import (
    _DEFAULT_CHECKPOINT,
    _MAX_EPISODE_COUNT,
    get_identifier,
    get_logger,
)
from blockassist.goals.diamond_quest import DiamondQuestGenerator
from blockassist.goals.emerald_quest import EmeraldQuestGenerator
from blockassist.goals.generator import BlockAssistGoalGenerator
from blockassist.goals.obsidian_quest import ObsidianQuestGenerator

_LOG = get_logger()

ex.observers.append(FileStorageObserver.create("episode_runs"))

@ex.named_config
def blockassist():
    num_simulations = 1  # noqa: F841
    goal_set = "test"
    house_id = None
    goal_generator_name = "blockassist"

    env_config_updates = {  # noqa: F841
        "num_players": 2,
        "goal_generator_config": {
            "goal_generator": goal_generator_name,
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


@ex.config_hook
def _apply_goal_generator_from_name(config, command_name, logger):
    """Ensure goal generator matches the configured name after overrides."""

    goal_generator_name = config.get("goal_generator_name", "blockassist")
    env_config_updates = config.setdefault("env_config_updates", {})
    goal_generator_config = env_config_updates.setdefault(
        "goal_generator_config", {}
    )
    goal_generator_config["goal_generator"] = goal_generator_name or "blockassist"
    return config


def run_main(goal_generator: str = "blockassist"):
    ALL_GOAL_GENERATORS["blockassist"] = BlockAssistGoalGenerator
    ALL_GOAL_GENERATORS["diamond_quest"] = DiamondQuestGenerator
    ALL_GOAL_GENERATORS["emerald_quest"] = EmeraldQuestGenerator
    ALL_GOAL_GENERATORS["obsidian_quest"] = ObsidianQuestGenerator
    selected_goal_generator = goal_generator or "blockassist"
    run = ex.run(
        named_configs=["human_with_assistant", "blockassist"],
        config_updates={
            "assistant_checkpoint": _DEFAULT_CHECKPOINT,
            "goal_generator_name": selected_goal_generator,
            "env_config_updates.goal_generator_config.goal_generator": selected_goal_generator,
        },
    )
    run_main.evaluate_dir = Path(run.observers[-1].dir)
    result = run.result
    assert result
    return result


class EpisodeRunner:
    """Class recording a building episode in Minecraft."""

    def __init__(
        self,
        address_eoa: str,
        checkpoint_dir: str,
        episode_count: int = _MAX_EPISODE_COUNT,
        human_alone: bool = True,
        goal_generator: str = "blockassist",
    ):
        self.address_eoa = address_eoa

        self.human_alone = human_alone
        self.checkpoint_dir = checkpoint_dir
        self.goal_generator = goal_generator or "blockassist"

        self.completed_episode_count = 0
        self.episode_count = episode_count
        self.evaluate_dirs = []

        self.start_time = time.time()
        self.end_time = None

        self.building_started = asyncio.Event()
        self.building_ended = asyncio.Event()

    def wait_for_start(self, timeout=60 * 2):  # minutes
        return asyncio.wait_for(self.building_started.wait(), timeout)

    def wait_for_end(self, timeout=60 * 2):  # hours
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
            duration_ms, get_identifier(self.address_eoa), self.get_last_goal_percentage_min(result)
        )

    def before_session(self):
        _LOG.info("Episode recording session started.")
        self.building_started.set()

    def after_session(self):
        _LOG.info("Episode recording session ended.")
        self.building_ended.set()
        self.end_time = time.time()

    def start(self):
        self.before_session()
        for i in range(self.episode_count):
            try:
                _LOG.info(f"Episode {i} recording started.")
                result = run_main(self.goal_generator)
                evaluate_dir = getattr(run_main, "evaluate_dir", None)
                if evaluate_dir:
                    self.evaluate_dirs.append(evaluate_dir)
                self.after_episode(result)
            except KeyboardInterrupt:
                _LOG.info(f"Episode {i} recording stopped!")
            # except

        self.after_session()
