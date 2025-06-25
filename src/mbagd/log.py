import asyncio
import os
from abc import ABC
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiofiles

from mbagd.globals import get_logger

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
            await asyncio.wait(tasks)
            if self.process and not self.process.returncode:
                _LOG.info(f"Terminating {self.prefix} process...")
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=10)
                except TimeoutError:
                    _LOG.warning(f"Killing {self.prefix} process...")
                    self.process.kill()
                    await self.process.wait()
        except ProcessLookupError:
            _LOG.warning(f"Process {self.process.pid} not found!")
        except asyncio.CancelledError:
            _LOG.warning(f"Process {self.process.pid} was cancelled!")
            raise
