#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
cp ref/schematics/dgsh5-109-009-e3-notes.md "$tmp"
python3 scripts/report_dgsh5_109_009_e3_audit.py
cmp "$tmp" ref/schematics/dgsh5-109-009-e3-notes.md
