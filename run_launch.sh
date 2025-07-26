#!/bin/bash

set -e -u
set -o pipefail

ROOT="$PWD"
cd "$ROOT"

# Function to clean up the server process upon exit
cleanup() {
    echo ">> Shutting down trainer..."

    # Remove modal credentials if they exist
    # rm -r $ROOT_DIR/modal-login/temp-data/*.json 2> /dev/null || true

    # Kill all processes belonging to this script's process group
    kill -- -$$ || true

    exit 0
}
trap cleanup EXIT

echo "=== Modal Login ==="

bash "$ROOT/modal_server.sh"
sleep 2

echo "=== BlockAssist Launch ==="

# Set TMPDIR=/tmp on macOS to avoid path length errors
if [[ "$OSTYPE" == "darwin"* ]]; then
    export TMPDIR=/tmp
fi
python -m blockassist.launch
