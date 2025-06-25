import asyncio
from collections.abc import AsyncIterator
import sys
from contextlib import asynccontextmanager

from mbagd.globals import get_logger
from mbagd.log import LoggedProcessContext

_LOG = get_logger()



# TODO: Connect to existing Minecraft servers.
class MinecraftContext(LoggedProcessContext):
    def __init__(self, num_instances=1) -> None:
        super().__init__("minecraft")
        self.num_instances = num_instances
        self.game_started = asyncio.Event()
        self.game_ended = asyncio.Event()
        self.game_crashed = False

    def args(self):
        return (
            [
                sys.executable,
                "-m",
                "malmo.minecraft",
                "launch",
                "--num_instances",
                f"{self.num_instances}",
            ]
            + ["--goal_visibility", "True"]
            + ["False" for _ in range(self.num_instances - 1)]
        )

    async def process_line(self, file, line):
        if file.endswith("_out.txt"):
            if "Successfully transformed method <init>" in line:
                self.game_started.set()
                _LOG.info("Minecraft instance started successfully.")
            elif "[Client thread/INFO]: Stopping!" in line:
                self.game_ended.set()
                raise asyncio.CancelledError("Minecraft instance manually stopped.")
        elif file.endswith("_err.txt"):
            if "Minecraft unexpectedly crashed on launch." in line:
                self.game_started.set()
                self.game_ended.set()
                self.game_crashed = True
                _LOG.error("Minecraft unexpectedly crashed on launch.")

        return line

    @asynccontextmanager
    async def start(self) ->  AsyncIterator['MinecraftContext']:
        async with super().start() as _:
            yield self


class EpisodeContext(LoggedProcessContext):
    """Context manager for recording a building episode in Minecraft."""

    def __init__(
        self,
        human_alone: bool = True,
        assistant_checkpoint: str = "data/assistancezero_assistant/checkpoint_002000",
    ):
        super().__init__("episode", cwd="mbag-repo")
        self.human_alone = human_alone
        self.assistant_checkpoint = assistant_checkpoint

        self.building_started = asyncio.Event()
        self.building_ended = asyncio.Event()

    def args(self):
        args = [sys.executable, "-m", "mbag.scripts.evaluate"]
        if self.human_alone:
            args += ["with", "human_alone"]
        if self.assistant_checkpoint:
            args += [f"assistant_checkpoint={self.assistant_checkpoint}"]
        return args

    @asynccontextmanager
    async def start(self) ->  AsyncIterator['EpisodeContext']:
        try:
            async with super().start() as _:
                yield self
        finally:
            self.building_ended.set()
            _LOG.info("Building episode finished.")



class TrainingContext(LoggedProcessContext):
    """Context manager for training an assistant in Minecraft."""

    def __init__(
        self,
        data_split,
        algorithm,
    ):
        super().__init__("training", cwd="mbag-repo")
        self.data_split = data_split
        self.algorithm = algorithm

        self.training_started = asyncio.Event()
        self.training_ended = asyncio.Event()

    def args(self):
        return [
            sys.executable,
            "-m",
            "mbag.scripts.train",
            "with",
            self.algorithm,
            f"data_split={self.data_split}",
        ]

    @asynccontextmanager
    async def start(self) ->  AsyncIterator['TrainingContext']:
        try:
            async with super().start() as _:
                yield self
        finally:
            self.training_ended.set()
            _LOG.info("Training model finished.")
