import json
import logging
import os
import time
import signal
import sys
import threading
import readchar

from subprocess import Popen
from typing import Optional, Dict

import psutil


from daemon import PROCESSES, cleanup_processes, start_log_watcher

def create_logs_dir(clear_existing=True):
    logging.info("Running create_logs_dir")
    if not os.path.exists("logs"):
        print("Creating logs directory")
        cmd = "mkdir -p logs"
        process = Popen(cmd, shell=True)
        ret = process.wait()
        if ret != 0:
            sys.exit(ret)
    else:
        print("Logs directory already exists")
        if clear_existing:
            print("Clearing existing logs directory")
            cmd = "rm -f logs/*"
            process = Popen(cmd, shell=True)
            ret = process.wait()
            if ret != 0:
                sys.exit(ret)


def create_evaluate_dir():
    logging.info("Running create_evaluate_dir")
    if not os.path.exists("data/base_checkpoint/evaluate"):
        print("Creating evaluate directory")
        cmd = "mkdir -p data/base_checkpoint/evaluate"
        process = Popen(cmd, shell=True)
        ret = process.wait()
        if ret != 0:
            sys.exit(ret)
    else:
        print("Evaluate directory already exists")

def setup_venv():
    logging.info("Running setup_venv")
    cmd = "./scripts/venv_setup.sh | tee logs/venv.log"
    process = Popen(cmd, shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(ret)

def setup_gradle():
    logging.info("Running setup_gradle")
    cmd = "./scripts/gradle_setup.sh"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    ret = process.wait()
    if ret != 0:
        sys.exit(ret)

def setup_yarn():
    logging.info("Running setup_yarn")
    cmd = "./scripts/yarn_setup.sh"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    ret = process.wait()
    if ret != 0:
        sys.exit(ret)

def run_malmo():
    logging.info("Running run_malmo")
    cmd = "./scripts/run_malmo.sh"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    return process

def run_yarn():
    logging.info("Running run_yarn")
    cmd = './scripts/yarn_run.sh'
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    return process

def run_open():
    logging.info("Running run_open")
    cmd = "open http://localhost:3000 2> /dev/null"
    process = Popen(cmd, shell=True)
    PROCESSES.append(process)
    return process

def run_blockassist(env: Optional[Dict] = None):
    logging.info("Running run_blockassist")
    cmd = "./scripts/run_blockassist.sh"
    process = Popen(cmd, shell=True, env=env)
    PROCESSES.append(process)
    return process


_ENTER_KEYS = ('\r', '\n')
def wait_for_enter(on_received=None):
    wait_for_keys(keys=_ENTER_KEYS, on_received=on_received)

def wait_for_keys(keys=_ENTER_KEYS, on_received=None):
    while True:
        char = readchar.readchar()
        if char in keys:  # Enter key
            if on_received:
                on_received(char)
            break
        else:
            print(f"Unknown key pressed: {repr(char)}. Please press a valid key in ({keys}) to continue.")

def send_blockassist_sigint(pid: int):
    logging.info("Running send_blockassist_sigint")
    print("Sending SIGINT to BlockAssist process with PID:", pid)

    parent_process = psutil.Process(pid)
    if parent_process.is_running():
        logging.info(f"Parent process {pid} is running, attempting to send SIGINT to its children.")

    # Get all child processes of the parent process
    children = parent_process.children(recursive=True)
    if not children:
        logging.info(f"No child processes found for PID {pid}.")
        return

    logging.info(f"Found {len(children)} child processes for PID {pid}. Sending SIGINT to them.")
    for child in children:
        logging.info(f"Got child process '{child.name()}' with pid {child.pid}")

        if child.name() == "python3.10" or child.name() == "python":
            child.send_signal(signal.SIGINT)
            logging.info(f"Sent SIGINT to child process {child.pid} ('{child.name()}')")
        else:
            logging.info(f"Child process '{child.name()}' was not targeted")

def train_blockassist(env: Optional[Dict] = None):
    logging.info("Running train_blockassist")
    cmd = "./scripts/train_blockassist.sh"
    process = Popen(cmd, shell=True, env=env)
    PROCESSES.append(process)
    return process

def wait_for_login():
    logging.info("Running wait_for_login")
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
    logging.info("Running BlockAssist run.py script")
    print(
        '''
██████╗ ██╗      ██████╗  ██████╗██╗  ██╗
██╔══██╗██║     ██╔═══██╗██╔════╝██║ ██╔╝
██████╔╝██║     ██║   ██║██║     █████╔╝
██╔══██╗██║     ██║   ██║██║     ██╔═██╗
██████╔╝███████╗╚██████╔╝╚██████╗██║  ██╗
╚═════╝ ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝

 █████╗ ███████╗███████╗██╗███████╗████████╗
██╔══██╗██╔════╝██╔════╝██║██╔════╝╚══██╔══╝
███████║███████╗███████╗██║███████╗   ██║
██╔══██║╚════██║╚════██║██║╚════██║   ██║
██║  ██║███████║███████║██║███████║   ██║
╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚══════╝   ╚═╝

By Gensyn
        '''
    )

    if os.environ.get("HF_TOKEN") is None:
        logging.info("HF_TOKEN not found, prompting")
        print("Please enter your Hugging Face token and press ENTER. If you don't have one, just press ENTER to find out how.")
        print("Hugging Face token: ", end="", flush=True)
        hf_token = input("Hugging Face token: ").strip()

        if not hf_token:
            logging.info("Empty HF_TOKEN provided, opening docs")
            print("Opening Hugging Face documentation to create a token...")
            if sys.platform == "darwin":
                cmd = "open https://huggingface.co/docs/hub/en/security-tokens#how-to-manage-user-access-tokens"
            elif sys.platform == "linux" or sys.platform == "linux2":
                cmd = "xdg-open https://huggingface.co/docs/hub/en/security-tokens#how-to-manage-user-access-tokens"
            else:
                print("Please visit: https://huggingface.co/docs/hub/en/security-tokens#how-to-manage-user-access-tokens")
                print("After creating your token, restart this program and enter it when prompted.")
                sys.exit(0)

            process = Popen(cmd, shell=True)
            process.wait()
            print("After creating your token, restart this program and enter it when prompted.")
            sys.exit(0)
        else:
            os.environ["HF_TOKEN"] = hf_token
            print("✅ HF_TOKEN set successfully")

    print("Creating directories...")
    create_logs_dir(clear_existing=True)
    create_evaluate_dir()

    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    filename='logs/run.log',
                    level=logging.DEBUG,
                    datefmt='%Y-%m-%d %H:%M:%S')

    print("Setting up virtualenv...")
    setup_venv()

    print("Setting up Gradle...")
    setup_gradle()

    print("Compiling Yarn...")

    setup_yarn()

    print("Setting up Minecraft...")
    start_log_watcher()
    proc_malmo = run_malmo()


    print("\nLOGIN")
    print("========")
    if sys.platform == "darwin":
        print("You will likely be asked to approve accessibility permissions. Please do so and, if necessary, restart the program.")
    proc_yarn = run_yarn()
    time.sleep(5)
    if not os.path.exists("modal-login/temp-data/userData.json"):
        print("Running Gensyn login. If browser does not open automatically, please open a browser and go to http://localhost:3000 and click 'login' to continue.")
        print("Note, if it's your first time playing, also click 'log in')")
        run_open()

    env = wait_for_login()

    print("\nSTART MINECRAFT")
    print("========")
    print("Please press ENTER when two Minecraft windows have opened. This may take up to 5 minutes to happen.")
    print("NOTE: If one or both of the windows closes, please restart the program. You can also `tail -f logs/malmo.log` in another terminal if you suspect an error")
    print("\nLoading...")
    wait_for_enter()
    print("Enter received")

    print("\nINSTRUCTIONS")
    print("========")
    time.sleep(1)
    print("The goal of the game is to build the structure in front of you.")
    print("You do this by placing or destroying blocks.")
    print("Each building you build is a separate 'episode'")
    print("An AI player will assist you.")
    print("The more you play, the more the AI player learns.")
    print("You should break red blocks and place blocks where indicated")
    print("Click on the window and press ENTER to start playing")
    print("Left click to break blocks, right click to place blocks")
    print("Select an axe to break things, or various blocks, by pressing the number keys 1-9")
    print("Use the WASD keys to move around")
    print("Once you've finished playing, press ESC, then click back on the terminal window")
    print("------\n")

    proc_blockassist = run_blockassist(env=env)

    #TODO: Avoid duplicating the blockassist.globals._MAX_EPISODE_COUNT value
    # And find a more elegant way to pull it from the environment.
    _MAX_EPISODE_COUNT = 2

    for i in range(_MAX_EPISODE_COUNT):
        # Start timer in a separate thread
        timer_running = True
        start_time = time.time()

        def timer_display():
            while timer_running:
                elapsed = int(time.time() - start_time)
                hours = elapsed // 3600
                minutes = (elapsed % 3600) // 60
                seconds = elapsed % 60
                print(f"\r⏱️  Recording time: {hours:02d}:{minutes:02d}:{seconds:02d}", end="", flush=True)
                time.sleep(1)

        timer_thread = threading.Thread(target=timer_display, daemon=True)
        timer_thread.start()

        def timer_end(key):
            nonlocal timer_running
            timer_running = False


        print(f"\n[{i}] Press ENTER when you have finished recording your episode. **You may have to press it multiple times**")
        wait_for_enter(timer_end)
        print(f"\n[{i}] Enter received")

        print(f"\n[{i}] Stopping episode recording")
        send_blockassist_sigint(proc_blockassist.pid)

    print("Stopping Malmo")
    proc_malmo.kill()
    proc_malmo.wait()

    print("Waiting for BlockAssist to stop")
    proc_blockassist.wait()

    print("\nMODEL TRAINING")
    print("========")
    print("Your assistant is now training on the gameplay you recorded.")
    print("This may take a while, depending on your hardware. Please keep this window open until you see 'Training complete'.")
    print("Running training")
    proc_train = train_blockassist(env=env)
    proc_train.wait()

    print("Training complete")

    print("\nUPLOAD TO HUGGINGFACE AND SMART CONTRACT")
    print("========")
    # Monitor blockassist-train.log for HuggingFace upload confirmation and transaction hash
    print("Checking for upload confirmation and transaction hash...")
    train_log_path = "logs/blockassist-train.log"
    upload_confirmed = False
    transaction_hash = None

    # Wait up to 30 seconds for the logs to appear
    for attempt in range(30):
        time.sleep(1)

        try:
            # Check blockassist-train.log for both logs
            if os.path.exists(train_log_path):
                with open(train_log_path, 'r') as f:
                    lines = f.readlines()
                    last_15_lines = lines[-15:] if len(lines) >= 15 else lines

                for line in last_15_lines:
                    line = line.strip()
                    if "Successfully uploaded model to HuggingFace:" in line and not upload_confirmed:
                        print("✅ " + line)
                        upload_confirmed = True
                    elif "HF Upload API response:" in line and not transaction_hash:
                        print("🔗 " + line)
                        transaction_hash = line

            # If we found both, we can stop monitoring
            if upload_confirmed and transaction_hash:
                print("Copy your HuggingFace model path (e.g. 'block-fielding/bellowing_pouncing_horse_1753796381') and check for it here:\nhttps://gensyn-testnet.explorer.alchemy.com/address/0xa6834217923D7A2A0539575CFc67abA209E6436F?tab=logs")
                break

        except Exception as e:
            print(f"Error reading log file: {e}")
            break

    # If we didn't find the logs after 30 seconds
    if not upload_confirmed and not transaction_hash:
        print("⚠️ No upload confirmation or transaction hash found in blockassist-train.log")
    elif not upload_confirmed:
        print("⚠️ No HuggingFace upload confirmation found in blockassist-train.log")
    elif not transaction_hash:
        print("⚠️ No transaction hash found in blockassist-train.log")

    print("\nSHUTTING DOWN")
    print("========")
    print("Stopping Yarn")
    proc_yarn.kill()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_processes()
