#!/bin/bash

# Script to tail all files in logs/ directory using tmux in a grid layout
# Usage: ./tmux_tail.sh [logs_directory] [session_name]

# Default values
LOGS_DIR="${1:-./logs/}"
SESSION_NAME="${2:-blockassist_logs}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to workspace root
cd "$WORKSPACE_ROOT"

# Check if logs directory exists
if [ ! -d "$LOGS_DIR" ]; then
    echo "Error: Logs directory '$LOGS_DIR' does not exist"
    echo "Usage: $0 [logs_directory] [session_name]"
    exit 1
fi

# Find all files in logs directory (excluding directories)
log_files=()
while IFS= read -r -d $'\0' file; do
    log_files+=("$file")
done < <(find "$LOGS_DIR" -type f -print0 | sort -z)

if [ ${#log_files[@]} -eq 0 ]; then
    echo "No files found in '$LOGS_DIR' directory!"
    exit 0
fi

echo "Found ${#log_files[@]} log files:"
printf '%s\n' "${log_files[@]}"

# Kill existing session if it exists
tmux kill-session -t "$SESSION_NAME" 2> /dev/null

# Create new tmux session
tmux new-session -d -s "$SESSION_NAME"

# If only one file, just tail it
if [ ${#log_files[@]} -eq 1 ]; then
    tmux send-keys -t "$SESSION_NAME:0" "tail -f '${log_files[0]}'" Enter
    tmux attach-session -t "$SESSION_NAME"
    exit 0
fi

# Calculate grid dimensions (try to make it as square as possible)
num_files=${#log_files[@]}
cols=$(echo "sqrt($num_files)" | bc -l | cut -d. -f1)
rows=$(((num_files + cols - 1) / cols))

echo "Creating ${rows}x${cols} grid for $num_files files"

# Start with the first file in the initial pane
tmux send-keys -t "$SESSION_NAME:0" "tail -f '${log_files[0]}'" Enter

# Create additional panes for remaining files
for ((i = 1; i < num_files; i++)); do
    # Calculate position for grid layout
    row=$((i / cols))
    col=$((i % cols))

    if [ $col -eq 0 ] && [ $row -gt 0 ]; then
        # Start a new row - split horizontally from the first pane of previous row
        prev_row_first_pane=$(((row - 1) * cols))
        tmux split-window -t "$SESSION_NAME:0.$prev_row_first_pane" -v
        current_pane=$((row * cols))
    else
        # Continue current row - split vertically from previous pane
        prev_pane=$((i - 1))
        tmux split-window -t "$SESSION_NAME:0.$prev_pane" -h
        current_pane=$i
    fi

    # Start tailing the file in the new pane
    tmux send-keys -t "$SESSION_NAME:0.$current_pane" "tail -f '${log_files[$i]}'" Enter
done

# Set pane titles to show filenames
for ((i = 0; i < num_files; i++)); do
    filename=$(basename "${log_files[$i]}")
    tmux select-pane -t "$SESSION_NAME:0.$i" -T "$filename"
done

# Enable pane titles and synchronize panes for easier navigation
tmux set-option -t "$SESSION_NAME" pane-border-status top
tmux set-option -t "$SESSION_NAME" pane-border-format "#{pane_title}"

# Balance the layout to make panes roughly equal size
tmux select-layout -t "$SESSION_NAME:0" tiled

echo "Tmux session '$SESSION_NAME' created successfully!"
echo "Use 'tmux attach-session -t $SESSION_NAME' to connect"
echo "Use Ctrl+B then arrow keys to navigate between panes"
echo "Use 'tmux kill-session -t $SESSION_NAME' to stop all tails"

# Optionally attach to the session immediately
read -p "Attach to the session now? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    tmux attach-session -t "$SESSION_NAME"
fi
