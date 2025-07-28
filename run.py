import json
import os
import time
import signal
import sys

from subprocess import Popen
from typing import List, Optional, Dict

PROCESSES: List[Popen] = []

def setup_venv():
    cmd = "./scripts/venv_setup.sh | tee logs/venv.log"
    process = Popen(cmd, shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(ret)

def setup_gradle():
    cmd = "./scripts/gradle_setup.sh"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    ret = process.wait()
    if ret != 0:
        sys.exit(ret)

def setup_yarn():
    cmd = "./scripts/yarn_setup.sh"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    ret = process.wait()
    if ret != 0:
        sys.exit(ret)

def run_malmo():
    cmd = "./scripts/run_malmo.sh"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    return process

def run_yarn():
    cmd = './scripts/yarn_run.sh'
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    return process

def run_open():
    cmd = "open http://localhost:3000 2> /dev/null"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    return process

def run_blockassist(env: Optional[Dict] = None):
    cmd = "./scripts/run_blockassist.sh"
    process = Popen(cmd, shell=True, env=env)
    PROCESSES.append(process)
    return process

def send_blockassist_sigint(pid: int):
    cmd = f"kill -s INT -- $(pgrep -P {pid})"
    process = Popen(cmd, shell=True)
    process.wait()

def train_blockassist(env: Optional[Dict] = None):
    cmd = "./scripts/train_blockassist.sh"
    process = Popen(cmd, shell=True, env=env)
    PROCESSES.append(process)
    return process

def wait_for_login():
    # Extract environment variables from userData.json
    print("Waiting for modal userData.json to be created...")
    user_data_path = "modal-login/temp-data/userData.json"
    while not os.path.exists(user_data_path):
        time.sleep(1)
    print("Found userData.json. Proceeding...")

    # Read and parse the JSON file
    with open(user_data_path, 'r') as f:
        user_data = json.load(f)

    # Extract BA_ORG_ID (last non-empty string value in the JSON)
    def get_last_string_value(obj):
        """Recursively find the last string value in a JSON object"""
        if isinstance(obj, dict):
            for value in reversed(list(obj.values())):
                result = get_last_string_value(value)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in reversed(obj):
                result = get_last_string_value(item)
                if result:
                    return result
        elif isinstance(obj, str) and obj.strip():
            return obj
        return None

    # Extract BA_ADDRESS_EOA (first "address" field value)
    def get_address_value(obj):
        """Recursively find the first 'address' field value"""
        if isinstance(obj, dict):
            if 'address' in obj:
                return obj['address']
            for value in obj.values():
                result = get_address_value(value)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = get_address_value(item)
                if result:
                    return result
        return None
    
    return {
        "BA_ORG_ID": get_last_string_value(user_data) or '',
        "BA_ADDRESS_EOA": get_address_value(user_data) or '',
        "PYTHONWARNINGS": 'ignore::DeprecationWarning'
    }

def run():
    print("Welcome to Blockassist")

    print("Setting up virtualenv")
    setup_venv()

    print("Setting up Gradle")
    setup_gradle()

    print("Compiling Yarn")

    setup_yarn()

    print("Done setting up Yarn")

    proc_malmo = run_malmo()

    print("Running Gensyn login modal")
    proc_yarn = run_yarn()
    env = wait_for_login()

    proc_open = run_open()

    print("Please press ENTER when you have logged in with your Gensyn account")
    input()
    print("Enter received")

    print("Please press ENTER when two Minecraft windows have opened. This may take up to 5 minutes to happen")
    input()
    print("Enter received")

    proc_blockassist = run_blockassist(env=env)

    print("Press ENTER when you have finished recording your episode")
    input()
    print("Enter received")

    print("Stopping episode recording")
    send_blockassist_sigint(proc_blockassist.pid)

    print("Killing Malmo")
    print("You can close the two Minecraft windows, now")
    proc_malmo.kill()
    proc_malmo.wait()

    print("Waiting for BlockAssist to stop")
    proc_blockassist.wait()

    print("Running training")
    proc_train = train_blockassist(env=env)
    proc_train.wait()


if __name__ == "__main__":
    try:
        run()
        for proc in PROCESSES:
            proc.wait()
    except KeyboardInterrupt:
        for proc in PROCESSES:
            proc.kill()
            proc.wait()