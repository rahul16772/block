from abc import ABC
import asyncio
import aiofiles
from types import TracebackType

from mbagd.globals import get_logger

_LOG = get_logger()

class LoggedProcessContext(ABC):
    """Context manager for running a subprocess with logging."""

    def __init__(self, prefix, cwd = None) -> None:
        self.prefix = prefix
        self.cwd = cwd
        self.tasks = []

    def args(self) -> list[str]: ...

    async def process_line(self, line):
        return line

    async def write_stream(self, stream, file):
        async with aiofiles.open(file, mode='w') as f:
            async for line in stream:
                line = await self.process_line(line.decode())
                await f.write(line)

    async def __aenter__(self):
        args = self.args()
        if self.cwd:
            kwargs = {"cwd": self.cwd}
        self.process = await asyncio.create_subprocess_exec(
            *args,
            **kwargs,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"TMPDIR": "/tmp/"},)
        self.tasks = list(
            map(
                asyncio.create_task,
                [
                    self.write_stream(self.process.stdout, f"logs/{self.prefix}_out.txt"),
                    self.write_stream(self.process.stderr, f"logs/{self.prefix}_err.txt"),
                ],
            )
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
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
