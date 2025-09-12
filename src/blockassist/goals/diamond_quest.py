"""Custom quest using a diamond fortress map."""

from .generator import BlockAssistGoalGenerator

OVERPOWERED_BLOCK_ID = (57, 0)


class DiamondQuestGenerator(BlockAssistGoalGenerator):
    """Goal generator that always selects the diamond fortress map."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config.setdefault("subset", "test")
        self.config["house_id"] = "diamond_fortress"
