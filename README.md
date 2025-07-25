# BlockAssist

Distributed extensions of the paper [AssistanceZero: Scalably Solving Assistance Games](https://arxiv.org/abs/2504.07091). Adds
multiplayer interactions, distributed training modalities, model merging/uploading, and on-chain attribution.

## Installation

### Python

First, you need to be running Python 3.10. It is recommended to install it with Pyenv.

#### MacOS

```bash
brew update
brew install pyenv
```

Now Pyenv is installed. Run the following command, and **follow the instructions** it displays

```bash
pyenv init # Follow the instructions from this command
```

For example, it may ask you to update your .zshrc.

Once that is done, you can install Python 3.10.

```
pyenv install 3.10
pyenv shell 3.10
```

#### Linux

```bash
curl -fsSL https://pyenv.run | bash
```

Now Pyenv is installed. Run the following command, and **follow the instructions** it displays

```bash
pyenv init # Follow the instructions from this command
```

For example, it may ask you to update your .zshrc.

Once that is done, you can install Python 3.10.

```
pyenv install 3.10
pyenv shell 3.10
```

### Java JDK 8u152

Run the setup.sh script in the repo to install Java 8u152.

```bash
curl "https://raw.githubusercontent.com/gensyn-ai/blockassist-private/refs/heads/main/setup.sh" | bash
```

### BlockAssist

Next, create a Python virtual environment install BlockAssist from Pip:

```bash
python -m venv blockassist-venv
. blockassist-venv/bin/activate
pip install blockassist
```

## Running

After installing the dependencies, you're ready to launch!

### Linux

```bash
python -m blockassist.launch
```

### MacOS

```bash
TMPDIR=/tmp/ python -m blockassist.launch
```

## Waiting for Launch

NOTE: The first time you run BlockAssist, it may take upwards of five minutes to launch. If you see an error from `asyncio` saying that it has timed out, just run the same command again.

Minecraft will launch two windows. One window is the "assistant," and one window is your game. For more information on how to interact with the game, [click here]().

# FIX THIS LINK

## Configuration

BlockAssist uses Hydra for configuration management. You can modify settings in the `config.yaml` file or override them via command line arguments.

### HuggingFace Token Configuration

To upload trained models to HuggingFace, you need to configure your HuggingFace token. There are several ways to do this:

#### Method 1: Configuration File

Edit `src/blockassist/config.yaml` and set your token:

```yaml
mode: e2e
hf_token: "hf_your_token_here"
```

#### Method 2: Command Line Override

Pass the token as a command line argument:

```bash
python -m blockassist.launch hf_token="hf_your_token_here"
```

#### Method 3: Environment Variable

Set the HuggingFace Hub token as an environment variable:

```bash
export HUGGINGFACE_HUB_TOKEN="hf_your_token_here"
python -m blockassist.launch
```

**Note:** If no token is provided, the system will attempt to use HuggingFace Hub's default authentication mechanism. You can obtain a HuggingFace token from your [HuggingFace settings page](https://huggingface.co/settings/tokens).

## Testing & Contributing

### Linting / Testing

This project relies mostly on ruff for formatting/linting purposes. To format, simply run:

    ruff check --select I --fix .

Pytest is used to run unit/integration tests. See below.

    pytest .

## Flow

This project has three primary interaction phases; 1.) startup + goal selection, 2.) recording a building episode, and 3.) training the actual model. The first and third are mediated by the launcher script but the 2nd is entirely in the Minecraft client.

Individual commands are explained below, but you can also run `blockassist` in `e2e` mode, which will run through all following steps in sequence:

    python -m blockassist.launch

### Recording/Building

Starts recording a single episode of the user building a randomly selected goal.

    python -m blockassist.launch mode=episode

### Training

Trains a model from a previously saved episode and saves it in HuggingFace format. Optionally uploads to HuggingFace if `hf_token` is configured.

    python -m blockassist.launch mode=train

## Telemetry

This repository uploads telemetry to Gensyn services. To disable telemetry, export the following variable:

```bash
export DISABLE_TELEMETRY=1
```

Then, you can run the repository as normal.
