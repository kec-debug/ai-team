#!/usr/bin/env bash
# Show the status of the "ai-team" tmux session.

set -euo pipefail

SESSION="ai-team"

if ! command -v tmux >/dev/null 2>&1; then
    echo "Error: tmux is not installed." >&2
    exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' is RUNNING."
    echo
    echo "Windows:"
    tmux list-windows -t "$SESSION" -F "  #I: #W#{?window_active, (active),}"
    echo
    echo "Next commands:"
    echo "  tmux attach -t $SESSION         # re-attach"
    echo "  ./scripts/stop-ai-team.sh       # stop the session"
else
    echo "Session '$SESSION' is NOT running."
    echo
    echo "Next commands:"
    echo "  ./scripts/start-ai-team.sh [PROJECT_DIR]   # start it"
fi
