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

echo ""
echo "─── agentic-engineer: spec-lint smoke ───"

run_spec_lint() {
    local file="$1"
    if ! python3 "$PROJECT_DIR/tools/spec_lint.py" "$file"; then
        echo ""
        echo "✗ spec-lint smoke FAILED on ${file#$PROJECT_DIR/} — fix before pushing"
        exit 1
    fi
}

run_spec_lint "$PROJECT_DIR/spec/spec_final.md"
run_spec_lint "$PROJECT_DIR/spec/spec-lint/spec_final.md"
run_spec_lint "$PROJECT_DIR/spec/gpt-researcher/spec_final.md"

echo "✓ agentic-engineer spec-lint smoke passed"
