import torch
from mbag.environment.goals import ALL_GOAL_GENERATORS
from mbag.scripts.evaluate import ex

from blockassist.goals.generator import BlockAssistGoalGenerator


@ex.named_config
def blockassist():
    assistant_checkpoint = "data/base_checkpoint"  # noqa: F841
    assistant_run = "MbagAlphaZero"
    num_simulations = 10
    goal_set = "test"
    house_id = None

    runs = ["HumanAgent", assistant_run]  # noqa: F841
    checkpoints = [None, assistant_checkpoint]  # noqa: F841
    policy_ids = [None, "assistant"]  # noqa: F841
    num_episodes = 2  # noqa: F841
    algorithm_config_updates = [  # noqa: F841
        {},
        {
            "num_gpus": 1 if torch.cuda.is_available() else 0,
            "num_gpus_per_worker": 0,
            "player_index": 1,
            "mcts_config": {"num_simulations": num_simulations},
        },
    ]
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
    min_action_interval = 0.8  # noqa: F841
    use_malmo = True  # noqa: F841


def run_main():
    ALL_GOAL_GENERATORS["blockassist"] = BlockAssistGoalGenerator
    ex.run(named_configs=["blockassist"])
