#!/usr/bin/env bash
# Create a new Claude + Codex job folder inside a target project.
#
# Usage:
#   ./scripts/create-job.sh PROJECT_DIR JOB_ID [--force]
#
# Creates: PROJECT_DIR/docs/ai/jobs/JOB_ID/
#   - request.ko.md
#   - plan.md
#   - codex-task.md
#   - patch.md
#   - review.md
#   - status.md
#
# Does NOT run git commands. Existing files are overwritten only with --force.

set -euo pipefail

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    echo "Usage: $0 PROJECT_DIR JOB_ID [--force]"
    echo "Example: $0 ~/projects/my-app job-001"
    exit 1
fi

PROJECT_DIR_INPUT="$1"
JOB_ID="$2"
FORCE=false

if [ "$#" -eq 3 ]; then
    if [ "$3" = "--force" ]; then
        FORCE=true
    else
        echo "Error: unknown option '$3'. Only --force is supported." >&2
        exit 1
    fi
fi

if [ ! -d "$PROJECT_DIR_INPUT" ]; then
    echo "Error: project directory '$PROJECT_DIR_INPUT' does not exist." >&2
    exit 1
fi

PROJECT_DIR="$(cd "$PROJECT_DIR_INPUT" && pwd)"
TEMPLATE_DIR="$PROJECT_DIR/docs/ai/jobs/_template"
JOB_DIR="$PROJECT_DIR/docs/ai/jobs/$JOB_ID"

if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "Error: template directory not found: $TEMPLATE_DIR" >&2
    echo "Create docs/ai/jobs/_template first." >&2
    exit 1
fi

mkdir -p "$JOB_DIR"

created=0
skipped=0

for src in "$TEMPLATE_DIR"/*.md; do
    name="$(basename "$src")"
    dest="$JOB_DIR/$name"
    existed=false
    if [ -e "$dest" ]; then
        existed=true
    fi
    if [ -e "$dest" ] && [ "$FORCE" = false ]; then
        echo "Skip existing: $dest"
        skipped=$((skipped + 1))
    else
        cp "$src" "$dest"
        if [ "$existed" = true ] && [ "$FORCE" = true ]; then
            echo "Overwrote: $dest"
        else
            echo "Created: $dest"
        fi
        created=$((created + 1))
    fi
done

echo "Created job at: $JOB_DIR"
echo
echo "Files:"
ls -la "$JOB_DIR"
echo
echo "Created or overwritten files: $created"
echo "Skipped existing files: $skipped"
echo
echo "Next steps:"
echo "  1. Put the Korean request in: $JOB_DIR/request.ko.md"
echo "  2. Ask Claude with: prompts/claude.md"
echo "  3. Save Claude's plan to: $JOB_DIR/plan.md"
echo "  4. Ask Codex with: prompts/codex-implementer.md and $JOB_DIR/codex-task.md"
echo "  5. Save Codex's result to: $JOB_DIR/patch.md"
echo "  6. Ask Claude to review into: $JOB_DIR/review.md"
echo
echo "Workflow doc: $PROJECT_DIR/docs/ai/CLAUDE_CODEX_WORKFLOW.md"
