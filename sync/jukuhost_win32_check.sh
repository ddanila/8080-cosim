#!/usr/bin/env bash
# Desk-qualify the Win32 artifact without claiming a physical Windows result.
set -euo pipefail

project_root=$(cd "$(dirname "$0")/.." && pwd)
first="$project_root/build/win32-repro-a"
second="$project_root/build/win32-repro-b"

cc -std=c99 -O2 -pedantic -Wall -Wextra -Werror -Wconversion -Wshadow \
    -I"$project_root/host/include" -I"$project_root/host/windows" \
    "$project_root/host/src/jukuhost_core.c" \
    "$project_root/host/src/jukuhost_sha256.c" \
    "$project_root/host/windows/jukuwin_payloads.c" \
    "$project_root/host/tests/jukuwin_payload_test.c" \
    -o "$project_root/build/jukuwin_payload_test"
"$project_root/build/jukuwin_payload_test"

"$project_root/sync/jukuhost_win32_build.sh" "$first"
"$project_root/sync/jukuhost_win32_build.sh" "$second"
cmp "$first/JUKUWIN.EXE" "$second/JUKUWIN.EXE"
echo "JUKUWIN-WIN32-REPRODUCIBILITY: PASS"

"$project_root/tools/check-jukuwin-pe.py" "$first/JUKUWIN.EXE" \
    --allowlist "$project_root/host/windows/win95-imports.txt" \
    --subsystem console

if command -v wine >/dev/null 2>&1; then
    wine "$first/JUKUWIN.EXE" --selftest
    echo "JUKUWIN-WINE-SELFTEST: PASS"
else
    echo "JUKUWIN-WINE-SELFTEST: SKIP (Wine not installed)"
fi

echo "JUKUWIN-WIN32-CHECK: PASS (cross-build desk boundary)"
