import asyncio
import os

import hydra
from omegaconf import DictConfig

from mbagd.context import EpisodeContext, MinecraftContext, TrainingContext
from mbagd.globals import get_logger

_LOG = get_logger()


async def _main(cfg: DictConfig):
    try:
        # TODO: Run in a loop
        _LOG.info("Starting full recording session!!")
        async with MinecraftContext() as minecraft_ctx:
            async with EpisodeContext() as episode_ctx:
                await asyncio.wait_for(
                    minecraft_ctx.game_ended.wait(), timeout=60 * 30
                )

        async with TrainingContext(
            data_split="human_alone", algorithm="bc_human"
        ) as training_ctx:
            await asyncio.wait_for(
                training_ctx.training_ended.wait(), timeout=60 * 60 * 6
            )

    except Exception as e:
        _LOG.warning("Recording session was stopped with exception", exc_info=e)


@hydra.main(version_base=None)
def main(cfg: DictConfig) -> None:
    asyncio.run(_main(cfg))


if __name__ == "__main__":
    os.environ["HYDRA_FULL_ERROR"] = "1"
    main()
