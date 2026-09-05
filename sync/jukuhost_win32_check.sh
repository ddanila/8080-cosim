#!/usr/bin/env bash
# Desk-qualify the Win32 artifact without claiming a physical Windows result.
set -euo pipefail

project_root=$(cd "$(dirname "$0")/.." && pwd)
first="$project_root/build/win32-repro-a"
second="$project_root/build/win32-repro-b"
mkdir -p "$project_root/build"

cc -std=c99 -O2 -pedantic -Wall -Wextra -Werror -Wconversion -Wshadow \
    -I"$project_root/host/include" -I"$project_root/host/windows" \
    "$project_root/host/src/jukuhost_core.c" \
    "$project_root/host/src/jukuhost_sha256.c" \
    "$project_root/host/windows/jukuwin_payloads.c" \
    "$project_root/host/tests/jukuwin_payload_test.c" \
    -o "$project_root/build/jukuwin_payload_test"
"$project_root/build/jukuwin_payload_test"

cc -std=c99 -O2 -pedantic -Wall -Wextra -Werror -Wconversion -Wshadow \
    -I"$project_root/host/include" -I"$project_root/host/windows" \
    "$project_root/host/windows/jukuwin_config.c" \
    "$project_root/host/tests/jukuwin_config_test.c" \
    -o "$project_root/build/jukuwin_config_test"
"$project_root/build/jukuwin_config_test"

cc -std=c99 -O2 -pedantic -Wall -Wextra -Werror -Wconversion -Wshadow \
    -I"$project_root/host/tests/win32-shim" \
    -I"$project_root/host/windows" \
    "$project_root/host/windows/jukuwin_config_store.c" \
    "$project_root/host/tests/jukuwin_config_store_test.c" \
    -o "$project_root/build/jukuwin_config_store_test"
"$project_root/build/jukuwin_config_store_test"

cc -std=c99 -O2 -pedantic -Wall -Wextra -Werror -Wconversion -Wshadow \
    -I"$project_root/host/windows" \
    "$project_root/host/windows/jukuwin_serial_select.c" \
    "$project_root/host/tests/jukuwin_serial_select_test.c" \
    -o "$project_root/build/jukuwin_serial_select_test"
"$project_root/build/jukuwin_serial_select_test"

cc -std=c99 -O2 -pedantic -Wall -Wextra -Werror -Wconversion -Wshadow \
    -I"$project_root/host/tests/win32-shim" \
    -I"$project_root/host/include" -I"$project_root/host/src" \
    "$project_root/host/src/platform_win32.c" \
    "$project_root/host/tests/platform_win32_test.c" \
    -o "$project_root/build/platform_win32_test"
"$project_root/build/platform_win32_test"

"$project_root/sync/jukuhost_win32_build.sh" "$first"
"$project_root/sync/jukuhost_win32_build.sh" "$second"
cmp "$first/JUKUWIN.EXE" "$second/JUKUWIN.EXE"
echo "JUKUWIN-WIN32-REPRODUCIBILITY: PASS"

"$project_root/tools/check-jukuwin-pe.py" "$first/JUKUWIN.EXE" \
    --allowlist "$project_root/host/windows/win95-imports.txt" \
    --subsystem windows

if command -v wine >/dev/null 2>&1 &&
        command -v wineboot >/dev/null 2>&1 &&
        command -v xvfb-run >/dev/null 2>&1; then
    python3 "$project_root/tests/jukuwin_wine_e2e_test.py" \
        --selftest-only "$first/JUKUWIN.EXE"
else
    echo "JUKUWIN-WINE-SELFTEST: SKIP (Wine/Xvfb prerequisites unavailable)"
fi

"$project_root/tools/package-jukuhost-windows.py" \
    --build-dir "$first" --output "$project_root/build/jukuwin-package"
test -f "$project_root/build/jukuwin-package/JUKUWIN.EXE"
test -f "$project_root/build/jukuwin-package/JUKUWIN.INI"
test ! -e "$project_root/build/jukuwin-package/SYSTEM.BIN"
test ! -e "$project_root/build/jukuwin-package/FAST16.BIN"
"$project_root/tools/check-jukuwin-package.py" \
    "$project_root/build/jukuwin-package"

echo "JUKUWIN-WIN32-CHECK: PASS (cross-build desk boundary)"
