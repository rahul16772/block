# JSON files are copied from https://github.com/cassidylaidlaw/minecraft-building-assistance-game/tree/master/mbag/environment/goals
from .diamond_quest import DiamondQuestGenerator
from .emerald_quest import EmeraldQuestGenerator
from .obsidian_quest import ObsidianQuestGenerator

__all__ = [
    "DiamondQuestGenerator",
    "EmeraldQuestGenerator",
    "ObsidianQuestGenerator",
]
