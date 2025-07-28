#!/bin/bash

set -e -u
set -o pipefail

source .env

# Function to clean up the server process upon exit
cleanup() {
    # Kill all processes belonging to this script's process group
    echo "Killing BlockAssist"
    kill -s SIGINT -- -$$ || true
    echo "BlockAssist SIGINT sent"

    exit 0
}
trap cleanup SIGINT

# Set TMPDIR=/tmp on macOS to avoid path length errors
if [[ "$OSTYPE" == "darwin"* ]]; then
    export TMPDIR=/tmp
    PID=$(lsof -nP -iTCP:10001 | awk '$2 ~ /^[0-9]+$/ { print $2; exit }')

    # Now tell System Events to minimize every window of that process by ID:
    osascript <<EOF
tell application "System Events"
    tell (first process whose unix id is $PID)
        repeat with w in windows
            tell w to set value of attribute "AXMinimized" to true
        end repeat
    end tell
end tell
EOF
fi

. blockassist-venv/bin/activate

python -m blockassist.launch +stages=[backup_evaluate,clean_evaluate,restore_backup,episode,upload_episodes] > logs/blockassist.log 2>&1