#!/usr/bin/env bash
# Start the AI team tmux session.
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

# --- Create session with the five windows ------------------------------------
tmux new-session -d -s "$SESSION" -n "gemini-manager"    -c "$WORK_DIR"
tmux new-window  -t "$SESSION"   -n "claude-architect"  -c "$WORK_DIR"
tmux new-window  -t "$SESSION"   -n "codex-implementer" -c "$WORK_DIR"
tmux new-window  -t "$SESSION"   -n "claude-reviewer"   -c "$WORK_DIR"
tmux new-window  -t "$SESSION"   -n "git-shell"         -c "$WORK_DIR"

# --- Window 1: Gemini Manager ------------------------------------------------
print_banner "gemini-manager"    "Gemini Manager"    "Requirements, planning, English prompt generation" "$PROMPTS_DIR/gemini-manager.md"
launch_tool  "gemini-manager"    "gemini"

# --- Window 2: Claude Architect ----------------------------------------------
print_banner "claude-architect"  "Claude Architect"  "Architecture review, risk analysis, test strategy" "$PROMPTS_DIR/claude-architect.md"
launch_tool  "claude-architect"  "claude"

# --- Window 3: Codex Implementer ---------------------------------------------
print_banner "codex-implementer" "Codex Implementer" "Implementation, tests, patches"                    "$PROMPTS_DIR/codex-implementer.md"
launch_tool  "codex-implementer" "codex"

# --- Window 4: Claude Reviewer -----------------------------------------------
print_banner "claude-reviewer"   "Claude Reviewer"   "PR diff review, quality gate"                      "$PROMPTS_DIR/claude-reviewer.md"
launch_tool  "claude-reviewer"   "claude"

# --- Window 5: Git Shell (plain shell, no tool launch) -----------------------
print_banner "git-shell"         "Git Shell"         "git / gh / branch / commit / PR / CI checks"       "(no prompt file — plain shell)"
tmux send-keys -t "$SESSION:git-shell" "echo 'Use this window for: git, gh, branch, commit, PR, CI.'" Enter
tmux send-keys -t "$SESSION:git-shell" "echo 'Reminder: never push to main directly; never auto-merge.'" Enter
tmux send-keys -t "$SESSION:git-shell" "echo" Enter

# --- Land on the manager window first ----------------------------------------
tmux select-window -t "$SESSION:gemini-manager"

if [ -t 1 ]; then
    exec tmux attach -t "$SESSION"
else
    echo "Session '$SESSION' started (detached). Attach with: tmux attach -t $SESSION"
fi
