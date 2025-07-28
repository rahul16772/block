import os
import time
import signal
import sys

from subprocess import Popen
from typing import List

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

def run_blockassist():
    cmd = "./scripts/run_blockassist.sh"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    return process

def send_blockassist_sigint(pid: int):
    cmd = f"kill -s INT -- $(pgrep -P {pid})"
    process = Popen(cmd, shell=True)
    process.wait()

def train_blockassist():
    cmd = "./scripts/train_blockassist.sh"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    return process

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
    time.sleep(5)

    proc_open = run_open()

    print("Please press ENTER when you have logged in with your Gensyn account")
    input()
    print("Enter received")

    print("Please press ENTER when two Minecraft windows have opened. This may take up to 5 minutes to happen")
    input()
    print("Enter received")

    proc_blockassist = run_blockassist()

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
    proc_train = train_blockassist()
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