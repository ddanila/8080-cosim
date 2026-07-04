#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

python3 spinoffs/minimal-vga/kicad/report_rev_a_fab_readiness.py "$@"
