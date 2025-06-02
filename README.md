# MBAG-d

Distributed extensions of the paper [AssistanceZero: Scalably Solving Assistance Games](https://arxiv.org/abs/2504.07091). Adds
multiplayer interactions, distributed training modalities, model merging/uploading, and on-chain attribution.

## Setup

### Dependencies

Supported Python versions: [3.8, 3.9, 3.10] (see [pyenv](https://github.com/pyenv/pyenv)).

Similar to the original MBAG [repository](https://github.com/cassidylaidlaw/minecraft-building-assistance-game) instructions, setup your Python environment by running `pip install -e .`

You will also need to install Java JDK 8u152, which can be found [here](https://www.oracle.com/java/technologies/javase/javase8-archive-downloads.html).

### Linting / Testing

This project relies mostly on ruff for formatting/linting purposes. To format, simply run:

    ruff check --select I --fix .

Pytest is used to run unit/integration tests. See below.

    pytest .
    pytest -m "integration" .

## Flow

This project has three primary interaction phases; 1.) startup + goal selection, 2.) recording a building episode, and 3.) training the actual model. The first and third are mediated by the launcher script but the 2nd is entirely in the Minecraft client.

Individual commands are explained below, but you can also run mbag-d in `e2e` mode, which will run through all following steps in sequence:

    mbag-d e2e

### Startup

To initiate the primary episode recording flow, execute the following in a terminal:

    mbag-d init

Upon a successful startup, you will see a Minecraft window (waiting at the menu screen) and the following console output:

    Hello world!

### Recording/Building

Starts recording a single episode of the user building a randomly selected goal.

    mbag-d record

### Training

Trains a model from a previously saved episode and saves it in HuggingFace format. Optionally uploads.

    mbag-d train

### Evaluation

Evaluates the performance of a trained checkpoint against cross validated human data.

    mbag-d eval
