import datetime
import json
import os
import platform
from importlib.metadata import version

import requests
import torch
from pydantic import BaseModel

TELEMETRY_API_BASE = "https://telemetry-api.internal-apps-central1.clusters.gensyn.ai"
TELEMETRY_API_EVENT_SESSION = f"{TELEMETRY_API_BASE}/event/session"
TELEMETRY_API_EVENT_MODEL_TRAINED = f"{TELEMETRY_API_BASE}/event/trained"
TELEMETRY_API_EVENT_MODEL_UPLOADED = f"{TELEMETRY_API_BASE}/event/uploaded"
BLOCKASSIST_VERSION = version("blockassist")

class EventSession(BaseModel):
    timestamp: str
    duration_ms: int
    user_id: str
    goal_pct: float
    ip_addr: str
    blockassist_version: str

class EventModelTrained(BaseModel):
    timestamp: str
    duration_ms: int
    session_count: int
    user_id: str
    ip_addr: str
    hardware_dict: str
    blockassist_version: str

class EventModelUploaded(BaseModel):
    timestamp: str
    size_bytes: int
    user_id: str
    ip_addr: str
    huggingface_id: str
    blockassist_version: str


def get_ip():
    ip = requests.get("https://icanhazip.com/").text
    return ip

def get_accelerator_info():
    out_devices = []

    if torch.cuda.is_available():
        for device in range(torch.cuda.device_count()):
            properties = torch.cuda.get_device_properties(device)
            d = {
                "name": properties.name,
                "major": properties.major,
                "minor": properties.minor,
                "total_memory": properties.total_memory,
                "multi_processor_count": properties.multi_processor_count,
                "max_threads_per_multi_processor": properties.max_threads_per_multi_processor,
            }
            out_devices.append(d)

    return out_devices

def get_system_info():
    return {
        "uname": json.dumps(platform.uname()._asdict()),
        "arch": platform.machine(),
        "os": platform.system(),
        "accelerators": get_accelerator_info(),
        "ip": get_ip()
    }


def is_telemetry_disabled():
    return os.environ.get("DISABLE_TELEMETRY", "false").lower() in ("true", "1", "yes")

def push_telemetry_event_session(duration_ms: int, user_id: str, goal_pct: float):
    if is_telemetry_disabled():
        return

    c = EventSession(
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        duration_ms=duration_ms,
        user_id=user_id,
        goal_pct=goal_pct,
        ip_addr=get_ip(),
        blockassist_version=BLOCKASSIST_VERSION
    )
    requests.post(TELEMETRY_API_EVENT_SESSION, json=dict(c))


def push_telemetry_event_trained(duration_ms: int, user_id: str, session_count: int):
    if is_telemetry_disabled():
        return

    c = EventModelTrained(
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        duration_ms=duration_ms,
        user_id=user_id,
        session_count=session_count,
        hardware_dict=json.dumps(get_system_info()),  # Convert dict to JSON string
        ip_addr=get_ip(),
        blockassist_version=BLOCKASSIST_VERSION
    )
    requests.post(TELEMETRY_API_EVENT_MODEL_TRAINED, json=dict(c))

def push_telemetry_event_uploaded(size_bytes: int, user_id: str, huggingface_id: str):
    if is_telemetry_disabled():
        return

    c = EventModelUploaded(
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        size_bytes=size_bytes,
        user_id=user_id,
        huggingface_id=huggingface_id,
        ip_addr=get_ip(),
        blockassist_version=BLOCKASSIST_VERSION
    )
    requests.post(TELEMETRY_API_EVENT_MODEL_UPLOADED, json=dict(c))
