import asyncio
import os
import socket
import sys
import time

import hydra
from omegaconf import DictConfig

from blockassist import telemetry
from blockassist.context import (
    MinecraftContext,
    TrainingContext,
    _log_dir,
)
from blockassist.distributed.hf import convert_checkpoint_to_hf
from blockassist.episode import EpisodeRunner
from blockassist.globals import get_logger

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
    # TODO: Fill in real telemetry values
    # Specifically: `goal_pct` in session call
    # `session_count` in training call
    # all values for upload
    try:
        if cfg["mode"] == "e2e":
            _LOG.info("Starting full recording session!!")

        stages = get_stages(cfg)
        num_instances = cfg.get("num_instances", 2)
        if "episode" in stages:
            start = time.time()
            _LOG.info("Starting episode recording!!")
            async with MinecraftContext(
                num_instances=num_instances
            ).start() as minecraft_ctx:
                # TODO: Make timeout an arg to started/ended/etc.
                await asyncio.wait_for(
                    minecraft_ctx.started(),
                    timeout=60 * 2,  # minutes
                )
                if not minecraft_ctx.any_game_crashed:
                    episode_runner = EpisodeRunner(human_alone=num_instances == 1)
                    episode_runner.start()
                    tasks = list(
                        map(
                            asyncio.create_task,
                            (minecraft_ctx.ended(), episode_runner.ended()),
                        )
                    )
                    await asyncio.wait(
                        tasks,
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=60 * 30,  # minutes
                    )
                else:
                    raise RuntimeError("A Minecraft instance crashed during launch.")

        if "episode_only" in stages:
            _LOG.info("Starting episode building only!!")
            episode_runner = EpisodeRunner(human_alone=num_instances == 1)
            episode_runner.start()
            await asyncio.wait_for(
                episode_runner.ended(),
                timeout=60 * 30,  # minutes
            )

        if "train" in stages:
            start = time.time()
            _LOG.info("Starting model training!!")
            async with TrainingContext(
                data_split="human_with_assistant", algorithm="bc_human"
            ).start() as training_ctx:
                await asyncio.wait_for(
                    training_ctx.training_ended.wait(),
                    timeout=60 * 60 * 24,  # hours
                )
            duration_ms = int((time.time() - start) * 1000)
            telemetry.push_telemetry_event_trained(duration_ms, socket.gethostname(), 1)

        if "convert" in stages:
            _LOG.info("Starting model conversion!!")
            # TODO: Fix!!
            convert_checkpoint_to_hf(
                checkpoint_dir="mbag-repo/data/assistancezero_assistant/checkpoint-002000",
                out_dir="mbag-repo/data/assistancezero_assistant_hf",
                arch="custom",
            )
            telemetry.push_telemetry_event_uploaded(0, socket.gethostname(), "")

    except Exception as e:
        _LOG.error("Recording session was stopped with exception", exc_info=e)
        sys.exit(1)


@hydra.main(version_base=None, config_path=".", config_name="config")
def main(cfg: DictConfig) -> None:
    if not _log_dir().exists():
        _log_dir().mkdir(parents=True, exist_ok=True)

    asyncio.run(_main(cfg))


if __name__ == "__main__":
    os.environ["HYDRA_FULL_ERROR"] = "1"
    main()
