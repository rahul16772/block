#!/bin/bash

set -e -u
set -o pipefail


if [[ "$OSTYPE" == "darwin"* ]]; then
    export TMPDIR="/tmp"
fi

. blockassist-venv/bin/activate

python -m blockassist.launch +stages=[train,upload_model] > logs/blockassist-train.log 2>&1