import asyncio
import sys
from abc import ABC
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import aiofiles

from blockassist.globals import _DEFAULT_CHECKPOINT, get_logger

_LOG = get_logger()


def _log_dir():
    time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return Path("logs") / f"run_{time_str}"


def _log_file(prefix, suffix):
    return _log_dir() / f"{prefix}_{suffix}.txt"


class LoggedProcessContext(ABC):
    """Context manager for running a subprocess with logging."""

    def __init__(self, prefix, cwd=None, checkpoint_dir=_DEFAULT_CHECKPOINT) -> None:
        self.prefix = prefix
        self.cwd = cwd
        self.checkpoint_dir = checkpoint_dir

    def args(self) -> list[str]: ...

    def process_line(self, file: Path, line: str):
        return line

    async def write_stream(self, stream, file):
        try:
            async with aiofiles.open(file, mode="w") as f:
                async for line in stream:
                    line = self.process_line(file, line.decode())
                    await f.write(line)
        except Exception as e:
            _LOG.error(f"Error writing to {file}: {e}", exc_info=True)
            raise

    @asynccontextmanager
    async def start(self) -> AsyncIterator["LoggedProcessContext"]:
        args = self.args()
        kwargs = {}
        if self.cwd:
            kwargs = {"cwd": self.cwd}

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
                        self.process.stdout, _log_file(self.prefix, "out")
                    ),
                    self.write_stream(
                        self.process.stderr, _log_file(self.prefix, "err")
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


# TODO: Connect to existing Minecraft instances.
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

    def process_line(self, file, line):
        if file.stem.endswith("out"):
            if "Successfully transformed method <init>" in line:
                self.num_games_started += 1
                _LOG.info(f"Minecraft instance {self.num_games_started} started.")
                if self.num_games_started == self.num_instances:
                    self.all_games_started.set()
                    _LOG.info("All Minecraft instances started successfully.")
            elif "[Client thread/INFO]: Stopping!" in line:
                self.any_game_ended.set()
                raise asyncio.CancelledError("Minecraft instance manually stopped.")
        elif file.stem.endswith("err"):
            if "Minecraft unexpectedly crashed on launch." in line:
                self.any_game_ended.set()
                self.any_game_crashed = True
                raise asyncio.CancelledError(
                    "Minecraft instance unexpectedly crashed on launch."
                )
            elif "ModuleNotFoundError: No module named" in line:
                raise asyncio.CancelledError(
                    "Dependencies not found. Refer to the README for setup instructions."
                )

        return line

    @asynccontextmanager
    async def start(self) -> AsyncIterator["MinecraftContext"]:
        async with super().start() as _:
            yield self
