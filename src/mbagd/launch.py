import asyncio
import os

import hydra
from omegaconf import DictConfig

from mbagd.distributed.hf import convert_checkpoint_to_hf
from mbagd.context import EpisodeContext, MinecraftContext, TrainingContext
from mbagd.globals import get_logger

_LOG = get_logger()

def get_stages(cfg: DictConfig) -> list[str]:
    if cfg["mode"] == "e2e":
        return [
            "episode",
            "train",
            "convert",
        ]

    return [cfg["mode"]]

async def _main(cfg: DictConfig):
    try:
        if cfg["mode"] == "e2e":
            _LOG.info("Starting full recording session!!")

        stages = get_stages(cfg)
        if "episode" in stages:
            _LOG.info("Starting episode recording!!")
            async with MinecraftContext(num_instances=1).start() as minecraft_ctx:
                await asyncio.wait_for(
                    minecraft_ctx.game_started.wait(), timeout=60 * 5 # minutes
                )
                if not minecraft_ctx.game_crashed:
                    async with EpisodeContext().start() as episode_ctx:
                        await asyncio.wait(
                            [minecraft_ctx.game_ended.wait(), episode_ctx.building_ended.wait()],
                            return_when=asyncio.FIRST_COMPLETED,
                            timeout=60 * 30 # minutes
                        )
                        episode_ctx.process.terminate()

        if "train" in stages:
            _LOG.info("Starting model training!!")
            async with TrainingContext(
                data_split="human_with_assistant", algorithm="bc_human"
            ).start() as training_ctx:
                await asyncio.wait_for(
                    training_ctx.training_ended.wait(), timeout=60 * 60 * 24 # hours
                )

        if "convert" in stages:
            _LOG.info("Starting model conversion!!")
            # TODO: Fix!!
            convert_checkpoint_to_hf(
                checkpoint_dir="mbag-repo/data/assistancezero_assistant/checkpoint-002000",
                out_dir="mbag-repo/data/assistancezero_assistant_hf",
                arch="custom",
            )

    except Exception as e:
        _LOG.warning("Recording session was stopped with exception", exc_info=e)


@hydra.main(version_base=None, config_path=".", config_name="config")
def main(cfg: DictConfig) -> None:
    asyncio.run(_main(cfg))


if __name__ == "__main__":
    os.environ["HYDRA_FULL_ERROR"] = "1"
    main()
