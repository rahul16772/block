import json
import os
import time
import signal
import sys

import subprocess
from subprocess import Popen
from typing import List, Optional, Dict

PROCESSES: List[Popen] = []

def create_logs_dir():
    if not os.path.exists("logs"):
        print("Creating logs directory")
        cmd = "mkdir -p logs"
        process = Popen(cmd, shell=True)
        ret = process.wait()
        if ret != 0:
            sys.exit(ret)
    else:
        print("Logs directory already exists")

def create_evaluate_dir():
    if not os.path.exists("data/base_checkpoint/evaluate"):
        print("Creating evaluate directory")
        cmd = "mkdir -p data/base_checkpoint/evaluate"
        process = Popen(cmd, shell=True)
        ret = process.wait()
        if ret != 0:
            sys.exit(ret)
    else:
        print("Evaluate directory already exists")

def kill_gradle_processes():
    cmd = "pkill -f gradle"
    process = Popen(cmd, shell=True)
    process.wait()

def cleanup_processes():
    print("Cleaning up processes...")
    kill_gradle_processes()
    for proc in PROCESSES:
        if proc.poll() is None:  # Process is still running
            proc.kill()
            proc.wait()

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
    pid_cmd = Popen(f"pgrep -P {pid}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    pid_cmd.wait()
    pid_child, _ = pid_cmd.communicate()
    pid_child = pid_child.replace("\n", "")

    # Hack because Linux runs a subshell of a subshell
    if sys.platform == "linux" or sys.platform == "linux2":
        pid_cmd = Popen(f"pgrep -P {pid_child}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        pid_cmd.wait()
        pid_child, _ = pid_cmd.communicate()
        pid_child = pid_child.replace("\n", "")

    cmd = f"kill -s INT -- {pid_child}"
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
        print("Please set the HF_TOKEN environment variable to your Hugging Face token in your ~/.bashrc or ~/.zshrc (Mac) file")
        print("Example:")
        print("export HF_TOKEN='your_token_here'")
        sys.exit(1)

    print("Creating directories...")
    create_logs_dir()
    create_evaluate_dir()
    
    print("Setting up virtualenv...")
    setup_venv()

    print("Setting up Gradle...")
    setup_gradle()

    print("Compiling Yarn...")

    setup_yarn()

    print("Setting up Minecraft...")
    proc_malmo = run_malmo()
    

    print("\nLOGIN")
    print("========")
    if sys.platform == "darwin":
        print("You will likely be asked to approve accessibility permissions. Please do so and, if necessary, restart the program.")
    proc_yarn = run_yarn()
    time.sleep(5)
    if not os.path.exists("modal-login/temp-data/userData.json"):
        print("Running Gensyn login modal")
        run_open()

    env = wait_for_login()

    print("\nSTART MINECRAFT")
    print("========")
    print("Please press ENTER when two Minecraft windows have opened. This may take up to 5 minutes to happen.")
    print("NOTE: If one or both of the windows closes, please restart the program.")
    print("If you don't see 'Enter received', press ENTER again.")
    print("\nLoading...")

    input()
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
    print("------")
    print("\nPress ENTER when you have finished recording your episode")
    print("After this point, the model will train on your episode data")

    proc_blockassist = run_blockassist(env=env)

    input()
    print("Enter received")

    print("Stopping episode recording")
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
        kill_gradle_processes()
        for proc in PROCESSES:
            proc.wait()
    except KeyboardInterrupt:
        kill_gradle_processes()
        for proc in PROCESSES:
            proc.kill()
            proc.wait()
