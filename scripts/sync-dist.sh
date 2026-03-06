#!/usr/bin/env bash
# Installs dist/spec-driven-dev/ -> ~/.claude/skills/spec-driven-dev/
# Direction: repo -> local ONLY. Never reverse-copy local -> repo.
# Bootstrap note: dist/ was initially populated from ~/.claude/skills/ (one-time).
#   All subsequent edits MUST happen in dist/, then sync to local via this script.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SRC="$REPO_ROOT/dist/spec-driven-dev"
DST="$HOME/.claude/skills/spec-driven-dev"

if [ ! -d "$SRC" ]; then
  echo "ERROR: $SRC not found" >&2; exit 1
fi

# Safety: validate DST is under ~/.claude/skills/ before rm -rf
EXPECTED_PREFIX="$HOME/.claude/skills/"
RESOLVED_DST="$(cd "$DST" 2>/dev/null && pwd || echo "$DST")"
case "$RESOLVED_DST" in
  "$EXPECTED_PREFIX"*) ;;
  *) echo "ERROR: DST '$RESOLVED_DST' is not under $EXPECTED_PREFIX — aborting" >&2; exit 1 ;;
esac

# Mirror sync: clean target first to prevent stale files
rm -rf "$DST"
mkdir -p "$DST"
# Use rsync to exclude runtime noise (.omc/) that OMC auto-creates
rsync -a --exclude='.omc' "$SRC"/ "$DST"/
echo "✓ Installed dist/spec-driven-dev -> $DST ($(find "$DST" -type f | wc -l | tr -d ' ') files)"
