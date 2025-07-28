#!/bin/bash

set -e -u
set -o pipefail

eval "$(pyenv init -)"

pyenv shell 3.10

if [ ! -d blockassist-venv ]; then
    python -m venv blockassist-venv
    . blockassist-venv/bin/activate

    pip install -e .
fi