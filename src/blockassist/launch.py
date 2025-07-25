import asyncio
import os
import sys

import hydra
from omegaconf import DictConfig

from blockassist.distributed.hf import convert_checkpoint_to_hf
from blockassist.episode import EpisodeRunner
from blockassist.train import TrainingRunner
from blockassist.globals import get_logger

_LOG = get_logger()


def get_stages(cfg: DictConfig) -> list[str]:
    mode = cfg["mode"]

    if mode == "e2e":
        return [
            "episode",
            "train",
            "convert",
        ]
    elif mode in ("episode", "train", "convert"):
        return [mode]

    _LOG.error(f"Unknown script mode: {mode}")
    return []


async def _main(cfg: DictConfig):
    # TODO: Fill in real telemetry values
    # all values for upload
    try:
        if cfg["mode"] == "e2e":
            _LOG.info("Starting full recording session!!")

        stages = get_stages(cfg)
        num_instances = cfg.get("num_instances", 2)
        human_alone = num_instances == 1

        for stage in stages:
            if stage == "episode":
                _LOG.info("Starting episode recording!!")
                episode_runner = EpisodeRunner(human_alone)
                episode_runner.start()
                await episode_runner.wait_for_end()

            elif stage == "train":
                _LOG.info("Starting model training!!")
                hf_token = cfg.get("hf_token")
                training_runner = TrainingRunner(hf_token=hf_token)
                training_runner.start()
                await training_runner.wait_for_end()

            elif stage == "convert":
                _LOG.info("Starting model conversion!!")
                # TODO: Fix!!
                convert_checkpoint_to_hf(
                    checkpoint_dir="mbag-repo/data/assistancezero_assistant/checkpoint-002000",
                    out_dir="mbag-repo/data/assistancezero_assistant_hf",
                    arch="custom",
                )
                # TODO: Fix!!
                # telemetry.push_telemetry_event_uploaded(0, socket.gethostname(), "")

    except Exception as e:
        _LOG.error("Recording session was stopped with exception", exc_info=e)
        sys.exit(1)


@hydra.main(version_base=None, config_path=".", config_name="config")
def main(cfg: DictConfig) -> None:
    asyncio.run(_main(cfg))


if __name__ == "__main__":
    os.environ["HYDRA_FULL_ERROR"] = "1"
    main()
