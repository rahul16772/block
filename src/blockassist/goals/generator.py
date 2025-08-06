import glob
import json
import logging
import os
from typing import Dict

from mbag.environment.goals.craftassist import CraftAssistGoalGenerator

logger = logging.getLogger(__name__)


class BlockAssistGoalGenerator(CraftAssistGoalGenerator):
    def _load_block_map(self):
        block_map_fname = os.path.join(
            os.path.dirname(__file__), "craftassist_block_map.json"
        )
        with open(block_map_fname, "r") as block_map_file:
            self.block_map = json.load(block_map_file)

        limited_block_map_fname = os.path.join(
            os.path.dirname(__file__), "limited_block_map.json"
        )
        with open(limited_block_map_fname, "r") as block_map_file:
            limited_block_map: Dict[str, str] = json.load(block_map_file)

        for key, value in self.block_map.items():
            if value is not None:
                self.block_map[key] = limited_block_map[value[0]], value[1]

    def _load_house_ids(self):
        self.house_ids = []
        for house_dir in glob.glob(
            os.path.join(
                self.config["data_dir"],
                "houses",
                self.config["subset"],
                "*",
            )
        ):
            house_id = os.path.split(house_dir)[-1]
            if self.config["house_id"] is None or self.config["house_id"] == house_id:
                self.house_ids.append(house_id)
