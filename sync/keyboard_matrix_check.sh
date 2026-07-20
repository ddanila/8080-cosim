#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
cp docs/factory-keyboard-matrix.md "$tmp"
python3 scripts/report_keyboard_matrix.py
cmp "$tmp" docs/factory-keyboard-matrix.md
