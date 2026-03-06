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

echo ""
echo "─── agentic-engineer: dist/ smoke ───"

DIST_DIR="$PROJECT_DIR/dist/spec-driven-dev"

# SKILL.md exists
if [ ! -f "$DIST_DIR/SKILL.md" ]; then
    echo "✗ dist/spec-driven-dev/SKILL.md not found"
    exit 1
fi

# All 3 scripts present and respond to --help
for script in scorecard_parser.py spec_lint.py check_consistency.py; do
    if ! python3 "$DIST_DIR/scripts/$script" --help > /dev/null 2>&1; then
        echo "✗ dist script $script --help failed"
        exit 1
    fi
done

# MANIFEST integrity: recompute and compare
MANIFEST_FILE="$DIST_DIR/MANIFEST"
if [ ! -f "$MANIFEST_FILE" ]; then
    echo "✗ dist/spec-driven-dev/MANIFEST not found"
    exit 1
fi

EXPECTED=$(cd "$DIST_DIR" && grep -v '^#' MANIFEST)
ACTUAL=$(cd "$DIST_DIR" && find . -type f -not -name MANIFEST -not -path './.omc/*' | LC_ALL=C sort | xargs shasum -a 256)
if [ "$EXPECTED" != "$ACTUAL" ]; then
    echo "✗ MANIFEST integrity check failed — checksums do not match"
    exit 1
fi

echo "✓ agentic-engineer dist/ smoke passed"
