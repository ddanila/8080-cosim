#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
cp docs/d15-d16-firmware-lineage.md "$tmp"
python3 scripts/report_d15_d16_firmware_lineage.py
cmp "$tmp" docs/d15-d16-firmware-lineage.md
