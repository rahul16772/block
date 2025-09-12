"""Custom quest using an obsidian tower map."""

from .generator import BlockAssistGoalGenerator

UNBREAKABLE_BLOCK_ID = (49, 0)


class ObsidianQuestGenerator(BlockAssistGoalGenerator):
    """Goal generator that always selects the obsidian tower map."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config.setdefault("subset", "test")
        self.config["house_id"] = "obsidian_tower"
