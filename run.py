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
    
    for k in user_data.keys():
        d = os.environ.copy()
        
        d["BA_ORG_ID"] = user_data[k].get("orgId", '')
        d["BA_ADDRESS_EOA"] = user_data[k].get("address", '')
        d["PYTHONWARNINGS"] = 'ignore::DeprecationWarning'
        
        return d
    
    raise ValueError("No user data found in userData.json")

def run():
    print("Welcome to Blockassist")

    if os.environ.get("HF_TOKEN") is None:
        print("Please set the HF_TOKEN environment variable to your Hugging Face token in your ~/.bashrc or ~/.zshrc (Mac) file")
        print("Example:")
        print("export HF_TOKEN='your_token_here'")
        sys.exit(1)

    print("Setting up virtualenv")
    setup_venv()

    print("Setting up Gradle")
    setup_gradle()

    print("Compiling Yarn")

    setup_yarn()

    print("Done setting up Yarn")

    proc_malmo = run_malmo()

    proc_yarn = run_yarn()
    time.sleep(5)
    if not os.path.exists("modal-login/temp-data/userData.json"):
        print("Running Gensyn login modal")
        run_open()

    env = wait_for_login()

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

    print("Training complete")

    print("Killing Yarn")
    proc_yarn.kill()


if __name__ == "__main__":
    try:
        run()
        for proc in PROCESSES:
            proc.wait()
    except KeyboardInterrupt:
        for proc in PROCESSES:
            proc.kill()
            proc.wait()