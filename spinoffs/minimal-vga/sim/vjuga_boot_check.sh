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

echo "== build VJUGA Verilog twin (tv80 + real К565РУ5) =="
# vm80a.v satisfies devices.v's cpu_8080 wrapper reference (unused here; tv80 is the CPU).
iverilog -g2012 \
  -Pvjuga_juku_tb.rom_file="\"$TMP/ekta37_z80.hex\"" \
  -Pvjuga_juku_tb.vw_limit="$WRITES" \
  -Pvjuga_juku_tb.dump_file="\"$TMP/vjuga.bin\"" \
  -o "$TMP/twin" \
  "$ROOT/hdl/vendor/vm80a.v" \
  "$TV/tv80_alu.v" "$TV/tv80_reg.v" "$TV/tv80_mcode.v" "$TV/tv80_core.v" "$TV/tv80s.v" \
  "$ROOT/hdl/devices.v" "$MV/hdl/vjuga_juku_top.v" "$MV/hdl/vjuga_juku_tb.v"

echo "== boot the real ROM on the VJUGA twin and dump its framebuffer =="
vvp "$TMP/twin" >/dev/null 2>&1

if [ ! -f "$TMP/vjuga.bin" ]; then
  echo "  FAIL  VJUGA twin never reached $WRITES video writes (no framebuffer dumped)"; exit 1
fi
if cmp -s "$TMP/vjuga.bin" "$TMP/ref.bin"; then
  echo "  PASS  VJUGA Verilog twin framebuffer == cosim after $WRITES video writes"
  echo "        (tv80 Z80 boots ekta37_z80 with the real К565РУ5 dram_64kx1 model)"
  echo "VJUGA-VERILOG-BOOT-CHECK: PASS"
else
  echo "  FAIL  VJUGA twin framebuffer differs from cosim @ $WRITES writes"
  echo "VJUGA-VERILOG-BOOT-CHECK: FAIL"; exit 1
fi
