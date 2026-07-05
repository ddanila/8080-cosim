#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

KCLI="$("scripts/find-kicad-cli.sh")"
KICAD_CLI="$KCLI" python3 spinoffs/minimal-vga/kicad/report_rev_a_erc_readiness.py "$@"
