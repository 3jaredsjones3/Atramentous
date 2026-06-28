#!/usr/bin/env bash
# Atramentous nightly sweep — local harness (cron / launchd / Cowork schedule).
#
# Same contract as the CI version: PROPOSE, never commit to main. This writes a
# dated digest and stages safe repairs on a branch. It does NOT merge and does
# NOT touch your working branch.
#
# Install (cron, 02:00 daily):
#   crontab -e
#   0 2 * * * /path/to/repo/.atramentous/atra-sweep.sh /path/to/repo >> /tmp/atra-sweep.log 2>&1
#
# Install (macOS launchd): wrap this in a LaunchAgent plist with StartCalendarInterval.
# Install (Claude Cowork): point a scheduled task at "Use atra-sweep on this repo."
set -euo pipefail

REPO="${1:-$PWD}"
cd "$REPO"
DATE="$(date -u +%Y-%m-%d)"
SWEEPS="docs/atramentous/sweeps"
mkdir -p "$SWEEPS"

LINT="$(dirname "$0")/atra_lint.py"
[ -f "$LINT" ] || LINT="$REPO/.atramentous/atra_lint.py"

python3 "$LINT" "$REPO" --since-last --state "$SWEEPS/.state.json" \
  > "$SWEEPS/${DATE}.md" || true
cp "$SWEEPS/${DATE}.md" "$SWEEPS/latest.md"

head -2 "$SWEEPS/${DATE}.md"

# Only open a proposal branch if something actually drifted.
if grep -qE '^entropy: [1-9]' "$SWEEPS/${DATE}.md"; then
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    BRANCH="atra/sweep-${DATE}"
    CUR="$(git rev-parse --abbrev-ref HEAD)"
    git stash -u --quiet || true
    git checkout -B "$BRANCH" --quiet
    git add "$SWEEPS"
    git commit -m "atra-sweep ${DATE}: entropy digest + safe proposals" --quiet || true
    git checkout "$CUR" --quiet
    git stash pop --quiet 2>/dev/null || true
    echo "proposal branch: $BRANCH  (review, then run atra-reconcile to dispose)"
  fi
else
  echo "no drift — nothing proposed."
fi
