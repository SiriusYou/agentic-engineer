#!/usr/bin/env bash
# Pre-push check for agentic-engineer
# Called by .git/hooks/pre-push in the standalone agentic-engineer repository.
# Exit 1 on any failure to block the push.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "─── agentic-engineer: consistency check ───"

if ! python3 "$PROJECT_DIR/tools/check_workflow_consistency.py" --root "$PROJECT_DIR" --format summary; then
    echo ""
    echo "✗ agentic-engineer consistency check FAILED — fix before pushing"
    exit 1
fi

echo "✓ agentic-engineer consistency check passed"
