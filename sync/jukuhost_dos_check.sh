#!/usr/bin/env bash
# Complete automatable Pocket8086/DOS M2.2 gate.
set -euo pipefail
cd "$(dirname "$0")/.."

sync/jukuhost_dos_build.sh build/dos-repro-a
sync/jukuhost_dos_build.sh build/dos-repro-b
cmp build/dos-repro-a/JUKUHOST.EXE build/dos-repro-b/JUKUHOST.EXE
echo "JUKUHOST-DOS-REPRODUCIBILITY: PASS"

sync/jukuhost_dos_build.sh
tools/package-jukuhost-dos.py

selftest_dir=$(mktemp -d /tmp/jukuhost-dos-selftest.XXXXXX)
trap 'rm -r -- "$selftest_dir"' EXIT
cp build/dos/JUKUHOST.EXE "$selftest_dir/"
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy dosbox-x \
    -silent -fastlaunch -nogui -nomenu -noautoexec -exit \
    -set "cpu cputype=8086" -set "cpu core=normal" \
    -set "cpu cycles=fixed 50000" \
    -c "mount c $selftest_dir" -c "c:" \
    -c "JUKUHOST --selftest > SELF.TXT" -c "exit" >/dev/null 2>&1
grep -q "selftest: PASS" "$selftest_dir/SELF.TXT"
echo "JUKUHOST-DOS-SELFTEST: PASS"

python3 tests/jukuhost_dos_stock_cosim_test.py
python3 tests/jukuhost_dos_c8_cosim_test.py
echo "JUKUHOST-DOS-CHECK: PASS"
