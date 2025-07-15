import asyncio
from collections.abc import AsyncIterator
import sys
from contextlib import asynccontextmanager

import boto3

from blockassist.distributed.s3 import zip_and_upload_latest_episode
from blockassist.globals import get_logger

import os
from abc import ABC

import aiofiles


_LOG = get_logger()


class LoggedProcessContext(ABC):
    """Context manager for running a subprocess with logging."""

    def __init__(self, prefix, cwd=None) -> None:
        self.prefix = prefix
        self.cwd = cwd

    def args(self) -> list[str]: ...

    async def process_line(self, file, line):
        return line

    async def write_stream(self, stream, file):
        try:
            async with aiofiles.open(file, mode="w") as f:
                async for line in stream:
                    line = await self.process_line(file, line.decode())
                    await f.write(line)
        except asyncio.CancelledError:
            self.process.terminate()

    @asynccontextmanager
    async def start(self) -> AsyncIterator["LoggedProcessContext"]:
        args = self.args()
        kwargs = {}
        if self.cwd:
            kwargs = {"cwd": self.cwd}

        if not os.path.exists("logs"):
            os.makedirs("logs")

        self.process = await asyncio.create_subprocess_exec(
            *args,
            **kwargs,
            limit=1024 * 1024,  # 1 MiB
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"TMPDIR": "/tmp/"},
        )
        tasks = list(
            map(
                asyncio.create_task,
                [
                    self.write_stream(
                        self.process.stdout, f"logs/{self.prefix}_out.txt"
                    ),
                    self.write_stream(
                        self.process.stderr, f"logs/{self.prefix}_err.txt"
                    ),
                ],
            )
        )
        try:
            yield self
            try:
                await asyncio.wait_for(self.process.wait(), timeout=30)  # seconds
                await asyncio.wait(tasks, timeout=30)  # seconds
                # Skip ValueError for stream limit exceeded
                # Skip Runtime Error for event loop is closed
                for task in tasks:
                    if ex := task.exception():
                        raise ex

            except asyncio.TimeoutError:
                if self.process.returncode is None:
                    _LOG.warning(
                        f"Process {self.process.pid} did not terminate in time; trying to kill next."
                    )
                    for task in tasks:
                        task.cancel()

                    self.process.kill()

        except ProcessLookupError:
            _LOG.warning(f"Process {self.process.pid} not found!")
        except asyncio.CancelledError:
            _LOG.warning(f"Process {self.process.pid} was cancelled!")
            raise


# TODO: Connect to existing Minecraft servers.
class MinecraftContext(LoggedProcessContext):
    def __init__(self, num_instances=1) -> None:
        super().__init__("minecraft")
        self.num_instances = num_instances

        self.num_games_started = 0
        self.all_games_started = asyncio.Event()
        self.any_game_ended = asyncio.Event()
        self.any_game_crashed = False

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

    def started(self):
        tasks = list(
            map(
                asyncio.create_task,
                (self.all_games_started.wait(), self.any_game_ended.wait()),
            )
        )
        return asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    def ended(self):
        tasks = list(
            map(
                asyncio.create_task,
                (self.process.wait(), self.any_game_ended.wait()),
            )
        )
        return asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    async def process_line(self, file, line):
        if file.endswith("_out.txt"):
            if "Successfully transformed method <init>" in line:
                self.num_games_started += 1
                if self.num_games_started == self.num_instances:
                    self.all_games_started.set()
                    _LOG.info("All Minecraft instances started successfully.")
            elif "[Client thread/INFO]: Stopping!" in line:
                self.any_game_ended.set()
                raise asyncio.CancelledError("Minecraft instance manually stopped.")
        elif file.endswith("_err.txt"):
            if "Minecraft unexpectedly crashed on launch." in line:
                self.any_game_ended.set()
                self.any_game_crashed = True
                raise asyncio.CancelledError(
                    "Minecraft instance unexpectedly crashed on launch."
                )

        return line

    @asynccontextmanager
    async def start(self) -> AsyncIterator["MinecraftContext"]:
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
        else:
            args += ["with", "human_with_assistant"]

        if self.assistant_checkpoint:
            args += [f"assistant_checkpoint={self.assistant_checkpoint}"]
        return args

    def started(self):
        return self.building_started.wait()

    def ended(self):
        tasks = list(
            map(
                asyncio.create_task,
                (self.process.wait(), self.building_ended.wait()),
            )
        )
        return asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    async def process_line(self, file, line):
        if "waiting for the mission to start" in line:
            self.building_started.set()
            _LOG.info("Waiting for Malmo mission to start.")
        elif "Attempted to get observation of an already ended mission" in line:
            self.building_ended.set()
            raise asyncio.CancelledError("Malmo mission concluded.")

        return line

    @asynccontextmanager
    async def start(self) -> AsyncIterator["EpisodeContext"]:
        async with super().start() as _:
            yield self

        try:
            zip_and_upload_latest_episode()
            _LOG.info("Episode data uploaded successfully.")
        except boto3.exceptions.S3UploadFailedError: # type: ignore
            _LOG.error("Failed to upload episode data to S3.", exc_info=True)

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
    async def start(self) -> AsyncIterator["TrainingContext"]:
        async with super().start() as _:
            yield self
