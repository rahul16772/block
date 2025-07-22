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
pyenv init # Follow instructions from this command
pyenv install 3.10
pyenv shell 3.10
```

#### Linux

```bash
curl -fsSL https://pyenv.run | bash
pyenv init # Follow instructions from this command
pyenv install 3.10
pyenv shell 3.10
```

### Java JDK 8u152

Run the setup.sh script in the repo to install Java 8u152.

```bash
curl "https://raw.githubusercontent.com/gensyn-ai/blockassist-private/refs/heads/eamonn/ci/setup.sh" | bash
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

---
# OUTDATED

## Setup

### Dependencies

#### Java 8u152

Install JDK 8u152 with the binaries available in the `bin` folder.

On MacOS: Run the `jdk-8u152-macosx-x64.dmg` installer. If you encounter an error at the last step, don't worry, it has installed anyway.

On Linux, unzip the `jdk-8u152-linux-x64.tar.gz` archive, and run the following:
```bash
sudo tar -xf /location-to-file/jdk1.8.0_202.tar.gz -C /opt
echo "JAVA_PATH=/opt/jdk1.8.0_202" >> $HOME/.bashrc
echo "PATH=$PATH:$JAVA_PATH/bin" >> $HOME/.bashrc
```

#### Python

Supported Python versions: [3.8, 3.9, 3.10] (see [pyenv](https://github.com/pyenv/pyenv)).

Similar to the original MBAG [repository](https://github.com/cassidylaidlaw/minecraft-building-assistance-game) instructions, setup your Python environment by running:

    pip install -e .

You will also need to install Java JDK 8u152, which can be found [here](https://www.oracle.com/java/technologies/javase/javase8-archive-downloads.html).

### Linting / Testing

This project relies mostly on ruff for formatting/linting purposes. To format, simply run:

    ruff check --select I --fix .

Pytest is used to run unit/integration tests. See below.

    pytest .
    pytest -m "integration" .

## Flow

This project has three primary interaction phases; 1.) startup + goal selection, 2.) recording a building episode, and 3.) training the actual model. The first and third are mediated by the launcher script but the 2nd is entirely in the Minecraft client.

Individual commands are explained below, but you can also run `blockassist` in `e2e` mode, which will run through all following steps in sequence:

    python -m blockassist.launch

### Startup

To initiate the primary episode recording flow, execute the following in a terminal:

    python -m blockassist.init

Upon a successful startup, you will see a Minecraft window (waiting at the menu screen) and the following console output:

    Hello world!

### Recording/Building

Starts recording a single episode of the user building a randomly selected goal.

    python -m blockassist.record

### Training

Trains a model from a previously saved episode and saves it in HuggingFace format. Optionally uploads.

    python -m blockassist.train

### Evaluation

Evaluates the performance of a trained checkpoint against cross validated human data.

    python -m blockassist.eval

## Telemetry

This repository uploads telemetry to Gensyn services. To disable telemetry, export the following variable:

```bash
export DISABLE_TELEMETRY=1
```

Then, you can run the repository as normal.
