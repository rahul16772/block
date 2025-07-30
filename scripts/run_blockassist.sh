#!/bin/bash

set -e -u
set -o pipefail

# Set TMPDIR=/tmp on macOS to avoid path length errors
if [[ "$OSTYPE" == "darwin"* ]]; then
    export TMPDIR="/tmp"
    PID="$(lsof -nP -iTCP:10001 | awk '$2 ~ /^[0-9]+$/ { print $2; exit }')"
    # Now tell System Events to minimize every window of that process by ID. If it fails, reset Terminal preferences for the next time this script is run and continue
    {
    osascript <<EOF 2>/dev/null
tell application "System Events"
    tell (first process whose unix id is $PID)
        repeat with w in windows
            tell w to set value of attribute "AXMinimized" to true
        end repeat
    end tell
end tell
EOF
    } || echo ""
fi

. blockassist-venv/bin/activate

python -m blockassist.launch +stages=[backup_evaluate,clean_evaluate,episode,upload_episodes] > logs/blockassist.log 2>&1