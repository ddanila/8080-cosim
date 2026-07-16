#!/usr/bin/env bash
# VJUGA Phase 4 framebuffer-readback validation.
#
# The bench boot oracle (docs/phase4-bench-bringup.md 4.2) reconstructs the
# framebuffer from a captured memory-write stream instead of a video output. To
# trust it on the bench, the reassembly tool is validated HERE against the
# verified twin: boot the twin with +capture, and require that
#
#     reassemble.py(capture)  ==  the twin's own framebuffer dump  ==  cosim
#
# so a later bench mismatch indicts the socketed chip, not the tool. No FDC,
# no interrupts, no display electronics.
set -euo pipefail

WRITES=${WRITES:-6000}
MV="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$MV/../.." && pwd)"
TV="$MV/external/tv80/rtl/core"
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
if [ ! -f "$TV/tv80s.v" ]; then
  echo "  SKIP  tv80 submodule not initialized -- run: git submodule update --init"
  exit 0
fi
CC=${CC:-cc}
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== cosim oracle framebuffer @ $WRITES video writes =="
python3 -c "open('$TMP/e.hex','w').write(chr(10).join('%02x'%b for b in open('$MV/roms/ekta37_z80.bin','rb').read())+chr(10))"
$CC -O2 -I "$ROOT/cosim" -o "$TMP/trace" \
  "$ROOT/cosim/trace.c" "$ROOT/cosim/i8080.c" "$ROOT/cosim/juk_disk.c" "$ROOT/cosim/juku_fdc.c"
( cd "$ROOT/cosim" && "$TMP/trace" "$MV/roms/ekta37_z80.bin" 50000000 "$WRITES" >/dev/null 2>&1 )
cp "$ROOT/cosim/vram.bin" "$TMP/ref.bin"

echo "== boot the twin with +capture and dump its own framebuffer =="
iverilog -g2012 \
  -Pvjuga_juku_tb.rom_file="\"$TMP/e.hex\"" \
  -Pvjuga_juku_tb.vw_limit="$WRITES" \
  -Pvjuga_juku_tb.dump_file="\"$TMP/twin_dump.bin\"" \
  -o "$TMP/twin" \
  "$ROOT/hdl/vendor/vm80a.v" \
  "$TV/tv80_alu.v" "$TV/tv80_reg.v" "$TV/tv80_mcode.v" "$TV/tv80_core.v" "$TV/tv80s.v" \
  "$ROOT/hdl/devices.v" "$MV/hdl/u24_dram_timing.v" \
  "$MV/hdl/vjuga_juku_top.v" "$MV/hdl/vjuga_juku_tb.v"
vvp "$TMP/twin" +capture="$TMP/cap.txt" >/dev/null 2>&1

echo "== reassemble the framebuffer from the captured write stream =="
python3 "$ROOT/tools/vjuga_fb_readback/reassemble.py" "$TMP/cap.txt" "$TMP/fb.bin"

fail=0
if cmp -s "$TMP/fb.bin" "$TMP/twin_dump.bin"; then
  echo "  PASS  readback(capture) == twin framebuffer dump (tool validated)"
else
  echo "  FAIL  readback(capture) != twin framebuffer dump"; fail=1
fi
if cmp -s "$TMP/fb.bin" "$TMP/ref.bin"; then
  echo "  PASS  readback(capture) == cosim vram.bin (banner verified with no video HW)"
else
  echo "  FAIL  readback(capture) != cosim vram.bin"; fail=1
fi

if [ "$fail" = 0 ]; then
  echo "VJUGA-FB-READBACK-CHECK: PASS"
else
  echo "VJUGA-FB-READBACK-CHECK: FAIL"; exit 1
fi
