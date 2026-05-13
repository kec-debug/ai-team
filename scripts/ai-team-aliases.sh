#!/usr/bin/env bash
# AI Team aliases. **Source** this file — do not execute it.
#
# One-shot in the current shell:
#   source /absolute/path/to/ai-team/scripts/ai-team-aliases.sh
#
# To make it permanent, add this line **manually** to ~/.bashrc or ~/.zshrc:
#   source /absolute/path/to/ai-team/scripts/ai-team-aliases.sh
#
# This script does NOT edit ~/.bashrc or ~/.zshrc automatically.

# Resolve the ai-team repo directory relative to this script.
AI_TEAM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"

alias ai-team="$AI_TEAM_DIR/scripts/start-ai-team.sh"
alias ai-attach='tmux attach -t ai-team'
alias ai-status="$AI_TEAM_DIR/scripts/status-ai-team.sh"
alias ai-stop="$AI_TEAM_DIR/scripts/stop-ai-team.sh"
alias ai-job="$AI_TEAM_DIR/scripts/create-job.sh"

echo "AI Team aliases loaded:"
echo "  ai-team [PROJECT_DIR]      # start the tmux session"
echo "  ai-attach                  # re-attach to a running session"
echo "  ai-status                  # show session status"
echo "  ai-stop                    # stop the session (with confirmation)"
echo "  ai-job PROJECT_DIR JOB_ID  # create a new job folder"
