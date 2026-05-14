#!/usr/bin/env bash
# Start the simplified Claude + Codex tmux session with a manual shell.
#
# Usage:
#   ./scripts/start-ai-team.sh [PROJECT_DIR]
#
# If PROJECT_DIR is omitted, the current working directory is used.
#
# This script is idempotent: if a tmux session named "ai-team" already
# exists, it attaches to it instead of recreating it.

set -euo pipefail

SESSION="ai-team"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROMPTS_DIR="$REPO_DIR/prompts"

# --- Resolve work directory --------------------------------------------------
if [ "$#" -ge 1 ]; then
    WORK_DIR_INPUT="$1"
else
    WORK_DIR_INPUT="$(pwd)"
fi

if [ ! -d "$WORK_DIR_INPUT" ]; then
    echo "Error: project directory '$WORK_DIR_INPUT' does not exist." >&2
    exit 1
fi
WORK_DIR="$(cd "$WORK_DIR_INPUT" && pwd)"

# --- Verify tmux -------------------------------------------------------------
if ! command -v tmux >/dev/null 2>&1; then
    echo "Error: tmux is not installed. Install tmux and retry." >&2
    exit 1
fi

# --- Idempotency: attach if session already exists ---------------------------
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' already exists. Attaching..."
    if [ -t 1 ]; then
        exec tmux attach -t "$SESSION"
    else
        echo "Not a TTY. Attach manually: tmux attach -t $SESSION"
        exit 0
    fi
fi

# --- Helpers -----------------------------------------------------------------
print_banner() {
    local window="$1"
    local role="$2"
    local responsibility="$3"
    local prompt_path="$4"
    tmux send-keys -t "$SESSION:$window" "clear" Enter
    tmux send-keys -t "$SESSION:$window" "echo '======================================================='" Enter
    tmux send-keys -t "$SESSION:$window" "echo '  Role          : $role'" Enter
    tmux send-keys -t "$SESSION:$window" "echo '  Responsibility: $responsibility'" Enter
    tmux send-keys -t "$SESSION:$window" "echo '  Prompt file   : $prompt_path'" Enter
    tmux send-keys -t "$SESSION:$window" "echo '  Work dir      : $WORK_DIR'" Enter
    tmux send-keys -t "$SESSION:$window" "echo '======================================================='" Enter
    tmux send-keys -t "$SESSION:$window" "echo" Enter
    tmux send-keys -t "$SESSION:$window" "echo 'Safety reminders:'" Enter
    tmux send-keys -t "$SESSION:$window" "echo '  - No auto commit / push / merge.'" Enter
    tmux send-keys -t "$SESSION:$window" "echo '  - Do not touch .env, secrets, auth, payment,'" Enter
    tmux send-keys -t "$SESSION:$window" "echo '    production infra, or DB migration files.'" Enter
    tmux send-keys -t "$SESSION:$window" "echo" Enter
}

launch_tool() {
    local window="$1"
    local tool="$2"
    tmux send-keys -t "$SESSION:$window" \
        "if command -v $tool >/dev/null 2>&1; then $tool; else echo '[!] $tool not found in PATH. Install it, then run: $tool'; fi" Enter
}

# --- Create session with two AI windows and one manual shell ------------------
tmux new-session -d -s "$SESSION" -n "claude" -c "$WORK_DIR"
tmux new-window  -t "$SESSION"   -n "codex"  -c "$WORK_DIR"
tmux new-window  -t "$SESSION"   -n "git-shell" -c "$WORK_DIR"

# --- Window 1: Claude ---------------------------------------------------------
print_banner "claude" "Claude" "Planning, requirements, review" "$PROMPTS_DIR/claude.md"
launch_tool  "claude" "claude"

# --- Window 2: Codex ----------------------------------------------------------
print_banner "codex" "Codex" "Implementation, tests, patch summary" "$PROMPTS_DIR/codex-implementer.md"
launch_tool  "codex" "codex"

# --- Window 3: Manual Shell ---------------------------------------------------
tmux send-keys -t "$SESSION:git-shell" "clear" Enter
tmux send-keys -t "$SESSION:git-shell" "echo '======================================================='" Enter
tmux send-keys -t "$SESSION:git-shell" "echo '  Window        : Manual Shell (git-shell)'" Enter
tmux send-keys -t "$SESSION:git-shell" "echo '  Responsibility: git status, git diff, tests, human commit/PR commands'" Enter
tmux send-keys -t "$SESSION:git-shell" "echo '  Work dir      : $WORK_DIR'" Enter
tmux send-keys -t "$SESSION:git-shell" "echo '======================================================='" Enter
tmux send-keys -t "$SESSION:git-shell" "echo" Enter
tmux send-keys -t "$SESSION:git-shell" "echo 'Manual shell only. It is not an AI role and is never automated by the GUI pipeline.'" Enter
tmux send-keys -t "$SESSION:git-shell" "echo" Enter

# --- Land on Claude first -----------------------------------------------------
tmux select-window -t "$SESSION:claude"

if [ -t 1 ]; then
    exec tmux attach -t "$SESSION"
else
    echo "Session '$SESSION' started (detached). Attach with: tmux attach -t $SESSION"
fi
