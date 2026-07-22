#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_alive.py --check
python3 spinoffs/jukuravi/firmware/build_d0_cpu.py --check
"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c
python3 tests/jukuravi_d0_alive_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-alive.bin
python3 tests/jukuravi_d0_cpu_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-cpu.bin

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
python3 - "$tmp/success.hex" "$tmp/failure.hex" <<'PY'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "spinoffs/jukuravi/firmware"))
import build_d0_alive
import build_d0_cpu

image, metadata = build_d0_cpu.build()
success = bytearray(image + bytes([0x76]) * 8192)
# The HDL fixture compresses only the half-second register delay; every CPU
# self-test and terminal-path byte stays identical to the burn image.
success[build_d0_alive.DELAY_COUNT_OFFSET] = 1
success[build_d0_alive.DELAY_COUNT_OFFSET + 1] = 0
failure = bytearray(success)
failure[metadata["signature_expected_offset"]] ^= 1
for path, data in ((Path(sys.argv[1]), success), (Path(sys.argv[2]), failure)):
    path.write_text("\n".join(f"{byte:02x}" for byte in data) + "\n")
PY
read -r success_pc failure_pc < <(
  PYTHONPATH=spinoffs/jukuravi/firmware python3 - <<'PY'
import build_d0_cpu
_, metadata = build_d0_cpu.build()
print(f"{metadata['success_halt']:04x} {metadata['fail_halt']:04x}")
PY
)
iverilog -g2012 -o "$tmp/jukuravi_d0_cpu_tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/jukuravi_d0_cpu_tb.v
for fixture in success failure; do
  args=(+rom="$tmp/$fixture.hex" +success="$success_pc" +failure="$failure_pc")
  [[ $fixture == failure ]] && args+=(+expect_fail)
  hdl_out=$(vvp "$tmp/jukuravi_d0_cpu_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-CPU-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-CPU-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done
./sync/beeper_check.sh
