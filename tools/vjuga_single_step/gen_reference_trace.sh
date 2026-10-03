#!/usr/bin/env bash
# Generate the VJUGA single-step reference trace from the verified simulation
# twin. A bench session with the Arduino UNO rig (vjuga_single_step.ino) prints
# one line per M1 opcode fetch in the SAME format; `diff` the bench log against
# this reference to find the exact fetch where a socketed chip diverges.
#
# Usage:  gen_reference_trace.sh [out-file]   (default: ./vjuga_reference_trace.txt)
# Env:    DECODE_MODE (0=B РТ4, 1=A). The twin caps the trace at 256 fetches.
set -euo pipefail

OUT=${1:-vjuga_reference_trace.txt}
DECODE_MODE=${DECODE_MODE:-0}
HERE="$(cd "$(dirname "$0")" && pwd)"
MV="$(cd "$HERE/../../spinoffs/minimal-vga" && pwd)"
ROOT="$(cd "$MV/../.." && pwd)"
TV="$MV/external/tv80/rtl/core"
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
if [ ! -f "$TV/tv80s.v" ]; then
  echo "  SKIP  tv80 submodule not initialized -- run: git submodule update --init"; exit 0
fi
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
python3 -c "open('$TMP/e.hex','w').write(chr(10).join('%02x'%b for b in open('$MV/roms/ekta37_z80.bin','rb').read())+chr(10))"

# Stop after 2000 framebuffer writes; early M1 tracing caps at 256 fetches.
iverilog -g2012 \
  -Pvjuga_juku_tb.rom_file="\"$TMP/e.hex\"" \
  -Pvjuga_juku_tb.vw_limit=2000 \
  -Pvjuga_juku_tb.decode_mode="$DECODE_MODE" \
  -Pvjuga_juku_tb.dump_file="\"$TMP/dump.bin\"" \
  -o "$TMP/twin" \
  "$ROOT/hdl/vendor/vm80a.v" \
  "$TV/tv80_alu.v" "$TV/tv80_reg.v" "$TV/tv80_mcode.v" "$TV/tv80_core.v" "$TV/tv80s.v" \
  "$ROOT/hdl/devices.v" "$MV/hdl/u24_dram_timing.v" \
  "$MV/hdl/vjuga_juku_top.v" "$MV/hdl/vjuga_juku_tb.v"
vvp "$TMP/twin" +trace="$TMP/trace.txt" >/dev/null 2>&1 || true

if [ ! -s "$TMP/trace.txt" ]; then
  echo "  FAIL  no trace produced"; exit 1
fi
cp "$TMP/trace.txt" "$OUT"
echo "wrote $(wc -l < "$OUT") M1-fetch reference lines (decode mode $DECODE_MODE) -> $OUT"
head -8 "$OUT"
