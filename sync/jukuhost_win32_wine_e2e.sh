#!/usr/bin/env bash
# Exercise the actual PE through Wine COM1 against stock, C11, and C12 co-sim.
set -euo pipefail

project_root=$(cd "$(dirname "$0")/.." && pwd)
if (( $# > 1 )); then
    echo "usage: $0 [JUKUWIN.EXE]" >&2
    exit 2
fi

for command in wine wineboot xvfb-run socat; do
    if ! command -v "$command" >/dev/null 2>&1; then
        echo "JUKUWIN-WINE-E2E: SKIP ($command not installed)"
        exit 0
    fi
done

if (( $# == 0 )); then
    executable="$project_root/build/win32-wine-e2e/JUKUWIN.EXE"
    "$project_root/sync/jukuhost_win32_build.sh" "$(dirname "$executable")"
else
    executable=$1
    if [[ ! -f "$executable" ]]; then
        echo "JUKUWIN-WINE-E2E: missing executable: $executable" >&2
        exit 2
    fi
fi

python3 "$project_root/tests/jukuwin_wine_e2e_test.py" "$executable"
