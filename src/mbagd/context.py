import asyncio
import sys
from types import TracebackType

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

    async def process_line(self, line):
        if "Successfully transformed method <init>" in line:
            self.game_started.set()
        elif "Minecraft unexpectedly crashed on launch." in line:
            _LOG.error("Minecraft unexpectedly crashed on launch.")
            self.game_crashed = True
            self.game_started.set()
        elif "[Client thread/INFO]: Stopping!" in line:
            _LOG.info("Minecraft instance ended gracefully.")
            self.game_ended.set()

        return line

    async def __aenter__(self):
        await super().__aenter__()
        await self.game_started.wait()
        if self.game_crashed:
            raise RuntimeError("Minecraft Malmo subprocesses failed to start.")

        _LOG.info("Minecraft Malmo subprocesses started and ready.")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await super().__aexit__(exc_type, exc_value, traceback)
        _LOG.info("Minecraft Malmo subprocesses terminated.")


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

    def args(self):
        args = [sys.executable, "-m", "mbag.scripts.evaluate"]
        if self.human_alone:
            args += ["with", "human_alone"]
        if self.assistant_checkpoint:
            args += [f"assistant_checkpoint={self.assistant_checkpoint}"]
        return args

    async def __aenter__(self):
        _LOG.info("Building episode started.")
        return await super().__aenter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await super().__aexit__(exc_type, exc_value, traceback)
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

    async def __aenter__(self):
        _LOG.info("Training episode started.")
        print(" ".join(self.args()))
        return await super().__aenter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await super().__aexit__(exc_type, exc_value, traceback)
        _LOG.info("Training episode finished.")
