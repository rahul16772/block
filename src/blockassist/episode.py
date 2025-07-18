import asyncio

import boto3

from blockassist.distributed.s3 import zip_and_upload_latest_episode
from blockassist.globals import get_logger
from blockassist.mbag import run_main

from mbag.environment.malmo.malmo_client import MalmoClient



_LOG = get_logger()


class EpisodeRunner:
    """Class recording a building episode in Minecraft."""

    def __init__(
        self,
        human_alone: bool = True,
        assistant_checkpoint: str = "data/base_checkpoint",
    ):
        self.human_alone = human_alone
        self.assistant_checkpoint = assistant_checkpoint

        self.building_started = asyncio.Event()
        self.building_ended = asyncio.Event()

    def started(self):
        return self.building_started.wait()

    def ended(self):
        return self.building_ended.wait()

    def start(self):
        original_get_observations = MalmoClient.get_observations

        def wrapped_get_observations(self, player_index):
            agent_host = self.agent_hosts[player_index]
            world_state = agent_host.getWorldState()
            if not world_state.is_mission_running:
                raise StopIteration("Mission already ended!")

            return original_get_observations(self, player_index)

        MalmoClient.get_observations = wrapped_get_observations

        self.building_started.set()
        try:
            run_main()
        except StopIteration:
            pass
        self.building_ended.set()

        MalmoClient.get_observations = original_get_observations
        try:
            zip_and_upload_latest_episode()
            _LOG.info("Episode data uploaded successfully.")
        except boto3.exceptions.S3UploadFailedError:  # type: ignore
            _LOG.error("Failed to upload episode data to S3.", exc_info=True)
