#!/usr/bin/env bash
# build-collection.sh — regenerate collection/<skill>.zip from source on release.
#
# Build artifacts are NOT committed (see .gitignore). The source tree is the only
# source of truth; these zips are a packaging convenience rebuilt from it. This
# exists because committing the zips is exactly what let a stale copy of the
# linter ship inside atra-sweep.zip after the source had moved on — never again.
#
# Each zip is simply the skill's top-level directory, with build/cache cruft
# excluded. Run from anywhere; paths are resolved relative to the repo root.
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"
mkdir -p collection

# Every top-level directory that contains a SKILL.md is a shippable skill.
shopt -s nullglob
built=0
for skill_md in */SKILL.md; do
  skill="${skill_md%/SKILL.md}"
  zip_path="collection/${skill}.zip"
  rm -f "$zip_path"
  # -X strips extra file attributes for reproducible archives.
  zip -r -q -X "$zip_path" "$skill" \
    -x '*/__pycache__/*' '*.pyc' '*/.DS_Store'
  echo "built ${zip_path}"
  built=$((built + 1))
done

echo "done — ${built} skill archive(s) regenerated into collection/"
