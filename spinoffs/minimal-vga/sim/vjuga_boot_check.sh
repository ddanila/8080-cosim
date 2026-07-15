#!/usr/bin/env bash
# VJUGA Verilog twin boot check (Phase 1).
#
# Boots the real Juku firmware on the VJUGA Verilog twin -- tv80 (Verilog Z80) +
# the real К565РУ5 (dram_64kx1) DRAM AND the real D6 К556РТ4 (decode_prom) /
# D8 К155РЕ3 (re3_prom) decode PROMs, all reused verbatim from hdl/devices.v --
# and confirms the framebuffer is byte-for-byte identical to the cosim oracle
# after N video writes. This boots the real ROM on a real Z80 (goal 1) and
# exercises the DRAM + both PROMs in the functional path (goals 2 and 3): a bad
# socketed chip would diverge the boot. No FDC, no interrupts.
#
# The byte-identical banner also validates the RAM READ path: the BIOS RAM test
# reads back what it writes, so a wrong read would diverge the boot and the
# framebuffer would not match.
set -euo pipefail

WRITES=${WRITES:-6000}
MV="$(cd "$(dirname "$0")/.." && pwd)"      # spinoffs/minimal-vga
ROOT="$(cd "$MV/../.." && pwd)"             # repo root
TV="$MV/external/tv80/rtl/core"
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
if [ ! -f "$TV/tv80s.v" ]; then
  echo "  SKIP  tv80 submodule not initialized ($TV missing) -- run: git submodule update --init"
  exit 0
fi
CC=${CC:-cc}
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== reuse recreation ROM: ekta37_z80.hex =="
python3 -c "open('$TMP/ekta37_z80.hex','w').write(chr(10).join('%02x'%b for b in open('$MV/roms/ekta37_z80.bin','rb').read())+chr(10))"

echo "== reuse recreation oracle: cosim framebuffer @ $WRITES video writes =="
$CC -O2 -I "$ROOT/cosim" -o "$TMP/trace" \
  "$ROOT/cosim/trace.c" "$ROOT/cosim/i8080.c" "$ROOT/cosim/juk_disk.c" "$ROOT/cosim/juku_fdc.c"
( cd "$ROOT/cosim" && "$TMP/trace" "$MV/roms/ekta37_z80.bin" 50000000 "$WRITES" >/dev/null 2>&1 )
cp "$ROOT/cosim/vram.bin" "$TMP/ref.bin"

# Both decode modes = the physical MODE_B jumper (J94):
#   0 = Mode B: the real D6 РТ4 (decode_prom) drives the ROM/RAM decision.
#   1 = Mode A: the U5 GAL's internal coarse decode, РТ4 socket empty (the
#       western-parts bring-up baseline). Each must boot byte-identical to cosim
#       so every physical jumper setting has a proven simulated counterpart.
fail=0
for M in 0 1; do
  if [ "$M" = 0 ]; then MODE_NAME="B (real D6 РТ4 decode)"; else MODE_NAME="A (GAL-internal decode, РТ4 socket empty)"; fi
  echo "== build + boot VJUGA twin, decode Mode $MODE_NAME =="
  # vm80a.v satisfies devices.v's cpu_8080 wrapper reference (unused here; tv80 is the CPU).
  iverilog -g2012 \
    -Pvjuga_juku_tb.rom_file="\"$TMP/ekta37_z80.hex\"" \
    -Pvjuga_juku_tb.vw_limit="$WRITES" \
    -Pvjuga_juku_tb.decode_mode="$M" \
    -Pvjuga_juku_tb.dump_file="\"$TMP/vjuga_$M.bin\"" \
    -o "$TMP/twin_$M" \
    "$ROOT/hdl/vendor/vm80a.v" \
    "$TV/tv80_alu.v" "$TV/tv80_reg.v" "$TV/tv80_mcode.v" "$TV/tv80_core.v" "$TV/tv80s.v" \
    "$ROOT/hdl/devices.v" "$MV/hdl/vjuga_juku_top.v" "$MV/hdl/vjuga_juku_tb.v"
  vvp "$TMP/twin_$M" >/dev/null 2>&1 || true
  if [ ! -f "$TMP/vjuga_$M.bin" ]; then
    echo "  FAIL  Mode $M never reached $WRITES video writes (no framebuffer dumped)"; fail=1
  elif cmp -s "$TMP/vjuga_$M.bin" "$TMP/ref.bin"; then
    echo "  PASS  Mode $M framebuffer == cosim after $WRITES video writes"
  else
    echo "  FAIL  Mode $M framebuffer differs from cosim @ $WRITES writes"; fail=1
  fi
done

if [ "$fail" = 0 ]; then
  echo "        (tv80 Z80 boots ekta37_z80 with the real К565РУ5 dram_64kx1 model,"
  echo "         through both the real D6 РТ4 decode and the GAL-internal baseline)"
  echo "VJUGA-VERILOG-BOOT-CHECK: PASS"
else
  echo "VJUGA-VERILOG-BOOT-CHECK: FAIL"; exit 1
fi
