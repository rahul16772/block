"""Custom quest using an emerald maze map."""

from .generator import BlockAssistGoalGenerator

ULTRA_BLOCK_ID = (133, 0)


class EmeraldQuestGenerator(BlockAssistGoalGenerator):
    """Goal generator that always selects the emerald maze map."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config.setdefault("subset", "test")
        self.config["house_id"] = "emerald_maze"

