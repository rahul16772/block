import asyncio
import os
import signal
import sys

import hydra
from omegaconf import DictConfig

from mbagd.context import EpisodeContext, MinecraftContext, TrainingContext
from mbagd.distributed.hf import convert_checkpoint_to_hf
from mbagd.globals import get_logger

from mbagd.telemetry import get_system_info

from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# Service name is required for most backends
resource = Resource.create(attributes={
    SERVICE_NAME: "blockassist"
})

tracerProvider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="https://public-otel-collector.public-telemetry.svc.internal-apps-central1.clusters.gensyn.ai:4318/v1/traces"))
tracerProvider.add_span_processor(processor)
trace.set_tracer_provider(tracerProvider)

reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="https://public-otel-collector.public-telemetry.svc.internal-apps-central1.clusters.gensyn.ai:4318/v1/metrics")
)
meterProvider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meterProvider)

tracer = trace.get_tracer("blockassist-tracer")


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
        with tracer.start_as_current_span("blockassist-main") as span:
            info = get_system_info()
            span.set_attributes(info)

            stages = get_stages(cfg)
            if "episode" in stages:
                with tracer.start_as_current_span("episode") as span:
                    span.set_attributes(info)
                    _LOG.info("Starting episode recording!!")
                    num_instances = cfg.get("num_instances", 2)
                    async with MinecraftContext(num_instances=num_instances).start() as minecraft_ctx:
                        await asyncio.wait_for(
                            minecraft_ctx.started(),
                            timeout=60 * 5,  # minutes
                        )
                        if not minecraft_ctx.any_game_crashed:
                            async with EpisodeContext(human_alone=num_instances == 1).start() as episode_ctx:
                                await asyncio.wait_for(
                                    episode_ctx.started(),
                                    timeout=60 * 5,  # minutes
                                )
                                tasks = list(
                                    map(
                                        asyncio.create_task,
                                        (minecraft_ctx.ended(), episode_ctx.ended()),
                                    )
                                )
                                await asyncio.wait(
                                    tasks,
                                    return_when=asyncio.FIRST_COMPLETED,
                                    timeout=60 * 60,  # minutes
                                )
                                minecraft_ctx.process.terminate()
                                episode_ctx.process.send_signal(signal.SIGINT)

                        else:
                            raise RuntimeError("A Minecraft instance crashed during launch.")

            if "train" in stages:
                with tracer.start_as_current_span("train") as span:
                    span.set_attributes(info)
                    _LOG.info("Starting model training!!")
                    async with TrainingContext(
                        data_split="human_with_assistant", algorithm="bc_human"
                    ).start() as training_ctx:
                        await asyncio.wait_for(
                            training_ctx.training_ended.wait(),
                            timeout=60 * 60 * 24,  # hours
                        )

            if "convert" in stages:
                with tracer.start_as_current_span("convert") as span:
                    span.set_attributes(info)
                    _LOG.info("Starting model conversion!!")
                    # TODO: Fix!!
                    convert_checkpoint_to_hf(
                        checkpoint_dir="mbag-repo/data/assistancezero_assistant/checkpoint-002000",
                        out_dir="mbag-repo/data/assistancezero_assistant_hf",
                        arch="custom",
                    )

    except Exception as e:
        _LOG.error("Recording session was stopped with exception", exc_info=e)
        sys.exit(1)


@hydra.main(version_base=None, config_path=".", config_name="config")
def main(cfg: DictConfig) -> None:
    asyncio.run(_main(cfg))


if __name__ == "__main__":
    os.environ["HYDRA_FULL_ERROR"] = "1"
    main()
