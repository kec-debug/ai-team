#!/usr/bin/env bash
# Stop the "ai-team" tmux session. Asks for confirmation first.
#
# Only touches the "ai-team" session. Other tmux sessions are left alone.

set -euo pipefail

SESSION="ai-team"

if ! command -v tmux >/dev/null 2>&1; then
    echo "Error: tmux is not installed." >&2
    exit 1
fi

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' is not running. Nothing to stop."
    exit 0
fi

echo "About to kill tmux session: $SESSION"
echo "Windows in this session:"
tmux list-windows -t "$SESSION" -F "  #I: #W"
echo

read -r -p "Proceed? [y/N]: " answer
case "$answer" in
    y|Y|yes|YES)
        tmux kill-session -t "$SESSION"
        echo "Session '$SESSION' stopped."
        ;;
    *)
        echo "Aborted. Session left running."
        exit 1
        ;;
esac
