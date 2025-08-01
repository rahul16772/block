# BlockAssist

BlockAssist is a distributed extension of the paper [AssistanceZero: Scalably Solving Assistance Games](https://arxiv.org/abs/2504.07091).

## Installation (Mac)

*You only need to ever run these once per computer*

**Step 1: Clone and enter repo**

```bash
git clone https://github.com/gensyn-ai/blockassist-private.git
cd blockassist-private
```

**Step 2: Install Java 1.8.0_152**

```bash
./setup.sh
```

**Step 3: Install Pyenv**

*NOTE: This step assumes [Homebrew](https://brew.sh/) is installed on your Mac*

```bash
brew update
brew install pyenv
```

**Step 4: Install Python 3.10**

```bash
pyenv install 3.10
```

**Step 5: Install psutil and readchar**

```bash
pyenv exec pip install psutil readchar
```

## Installation (Linux)

*You only need to ever run these once per computer*

**Step 1: Clone and enter repo**

```bash
git clone https://github.com/gensyn-ai/blockassist-private.git
cd blockassist-private
```

**Step 2: Install Java 1.8.0_152**

```bash
./setup.sh
```

**Step 3: Install Pyenv**

```bash
curl -fsSL https://pyenv.run | bash
```

NOTE: Follow the instructions `pyenv` gives about adding it to your shell!

**Step 4: Install Python 3.10**

```bash
sudo apt update
sudo apt install make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl git libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev # Dependencies for Python installation
pyenv install 3.10
```

**Step 5: Install psutil and readchar**

```bash
pip install psutil readchar
```

## Run BlockAssist

Use `tail -f logs/[specific log].log` to monitor progress. `ls logs` to see options. Note, when asked to press ENTER, sometimes you need to do this a few times.

**Run with Python**

* On Mac: `pyenv exec python run.py`
* On Linux: `python run.py`

The program will install various dependencies as required. Follow any instructions and approve all asks.

**Modal login**

You will be prompted to log in via the modal. If you have previously logged in, it will skip this step. Else, log in and press ENTER when done.

**Play Minecraft**

Once the Minecraft windows have loaded, the Python script will ask you to press ENTER.

Go to the first Minecraft window that opened (the other one will be minimised if you are running on Mac). Click the window. Press ENTER to have it capture your inputs. Complete the structure in-game, then go back to your terminal and hit ENTER to end the session.

**Training**

A model will now be trained and submitted to Hugging Face and Gensyn's smart contract.

**Review logs**

If you reach this stage in the logging window, and can see a transaction in the block explorer, then submissions have worked.

Logging window:

```
[2025-07-28 05:03:48,955][blockassist.globals][INFO] - Successfully uploaded model to HuggingFace: h-grieve/blockassist-bc-bellowing_pouncing_horse_1753675374 with size 20.00 MB
```

[Block explorer](https://gensyn-testnet.explorer.alchemy.com/address/0xa6834217923D7A2A0539575CFc67abA209E6436F?tab=logs):

```
huggingFaceID
string
false
h-grieve/blockassist-bc-bellowing_pouncing_horse_1753675374
```

The program will then end. Please close any minecraft windows if they remain open.


## Configuration

BlockAssist uses Hydra for configuration management. You can modify settings in the `config.yaml` file or override them via command line arguments.

- `episode_count` - Controls number of episodes. If `episode_count` is greater than 1, a new episode will be started every time you press ENTER during session recording.
- `num_training_iters` - Controls number of training iterations on all your recorded episodes.

## Testing & Contributing

### Linting / Testing

This project relies mostly on ruff for formatting/linting purposes. To format, simply run:

```bash
ruff check --select I --fix .
```

## Telemetry

This repository uploads telemetry to Gensyn services. To disable telemetry, export the following variable:

```bash
export DISABLE_TELEMETRY=1
```
