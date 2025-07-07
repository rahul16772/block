import json
import os
import platform

import torch
import requests

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
    if os.environ.get("DISABLE_TELEMETRY", "false").lower() != "false":
        return {}


    return {
        "uname": json.dumps(platform.uname()._asdict()),
        "arch": platform.machine(),
        "os": platform.system(),
        "accelerators": get_accelerator_info(),
        "ip": get_ip()
    }
