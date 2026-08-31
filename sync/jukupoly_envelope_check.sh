#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 spinoffs/jukupoly/tools/report_jukupoly_envelope.py --check
