# BlockAssist

**NOTE: this README.md is geared towards testing. It will be buffed prior to release.**

BlockAssist is a distributed extension of the paper [AssistanceZero: Scalably Solving Assistance Games](https://arxiv.org/abs/2504.07091).

## Installation (Mac)

*You only need to ever run these once, you can skip when running future tests*
**Clone and enter repo**
```bash
git clone git@github.com:gensyn-ai/blockassist-private.git
cd blockassist-private
```

**Install Java 1.8.0_152**
```bash
./setup.sh
```

**Ensure pyenv installed**
```bash
brew update
brew install pyenv
```

**Install Python 3.10**
```bash
pyenv install 3.10
```

**Install psutil**
```bash
pip install psutil
```

## Installation (Linux)

*You only need to ever run these once, you can skip when running future tests*

**Clone and enter repo**
```bash
git clone git@github.com:gensyn-ai/blockassist-private.git
cd blockassist-private
```

**Install Java 1.8.0_152**
```bash
./setup.sh
```

**Ensure pyenv installed**
```bash
curl -fsSL https://pyenv.run | bash
```

NOTE: Follow the instructions `pyenv` gives about adding it to your shell!

**Install Python 3.10**
```bash
sudo apt install libbz2-dev libssl-dev libreadline-dev libncurses-dev libffi-dev # Dependencies for Python installation
pyenv install 3.10
```

**Install psutil**
```bash
pip install psutil
```

## Run BlockAssist

Use `tail -f logs/[specific log].log` to monitor progress. `ls logs` to see options. Note, when asked to press enter, sometimes you need to do this a few times.

**Run Python file**
```bash
python run.py
```
The program will install various dependencies, as required. Follow any instructions and approve all asks.

**Modal login**

You will be prompted to log in via the modal. If you have previously logged in, it will skip this step. Else, log in and press enter when done.

**Play a few seconds of Minecraft**

Once the minecraft windows have loaded it will ask you to click enter.

Go to the minecraft window which is showing (one will be minimised). Click the window. Press enter. Move around a bit. Press escape. Go back to the terminal window. Press enter again, as prompted.

**Training**

A model will now train and be submitted to Hugging Face and the smart contract.

**Review logs**

If you reach this stage in the logging window, and can see a transactions in the block explorer then submissions have worked.

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

The program will end, please close any minecraft windows if they remain open.


## Configuration

BlockAssist uses Hydra for configuration management. You can modify settings in the `config.yaml` file or override them via command line arguments.
`episode_count` - Controls number of episodes. If `episode_count`>1, a new episode will be started every time you `ctrl+c`
`num_training_iters` - Controls number of training iterations on all your recorded episodes

## Testing & Contributing

### Linting / Testing

This project relies mostly on ruff for formatting/linting purposes. To format, simply run:

    ruff check --select I --fix .

Pytest is used to run unit/integration tests. See below.

    pytest .


## Telemetry

This repository uploads telemetry to Gensyn services. To disable telemetry, export the following variable:

```bash
export DISABLE_TELEMETRY=1
```
