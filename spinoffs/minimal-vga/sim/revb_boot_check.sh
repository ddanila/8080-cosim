#!/usr/bin/env bash
# VJUGA rev B modular-backplane boot check (Phase B0 keystone).
#
# Boots the real Juku ekta37 firmware on the rev B card partition -- CPU / Memory /
# Video / I/O cards wired through revb_backplane_top -- and confirms the Video
# card's framebuffer is byte-for-byte identical to the cosim oracle after N video
# writes, in BOTH decode modes. This proves the modular repartition (SRAM main
# memory + framebuffer on a separate Video card, per build-plan C1) preserves the
# exact machine behavior that vjuga_juku_top.v established. No FDC, no interrupts.
set -euo pipefail

WRITES=${WRITES:-6000}
MV="$(cd "$(dirname "$0")/.." && pwd)"      # spinoffs/minimal-vga
ROOT="$(cd "$MV/../.." && pwd)"             # repo root
TV="$MV/external/tv80/rtl/core"
REVB="$MV/hdl/revb"
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

fail=0
for M in 0 1; do
  if [ "$M" = 0 ]; then MODE_NAME="B (real D6 РТ4 decode)"; else MODE_NAME="A (GAL-internal decode)"; fi
  echo "== build + boot rev B modular twin, decode Mode $MODE_NAME =="
  iverilog -g2012 \
    -Prevb_backplane_tb.rom_file="\"$TMP/ekta37_z80.hex\"" \
    -Prevb_backplane_tb.vw_limit="$WRITES" \
    -Prevb_backplane_tb.decode_mode="$M" \
    -Prevb_backplane_tb.dump_file="\"$TMP/revb_$M.bin\"" \
    -o "$TMP/twin_$M" \
    "$ROOT/hdl/vendor/vm80a.v" \
    "$TV/tv80_alu.v" "$TV/tv80_reg.v" "$TV/tv80_mcode.v" "$TV/tv80_core.v" "$TV/tv80s.v" \
    "$ROOT/hdl/devices.v" \
    "$REVB/revb_cpu_card.v" "$REVB/revb_mem_card.v" "$REVB/revb_video_card.v" \
    "$REVB/revb_io_card.v" "$REVB/revb_bus_monitor.v" \
    "$REVB/revb_backplane_top.v" "$REVB/revb_backplane_tb.v"
  vvp "$TMP/twin_$M" >"$TMP/run_$M.log" 2>&1 || true
  if grep -q "REVB-BUS-CONFLICT" "$TMP/run_$M.log"; then
    echo "  FAIL  Mode $M raised a bus-driver conflict:"; grep "REVB-BUS-CONFLICT" "$TMP/run_$M.log" | head -3 | sed 's/^/        /'; fail=1
  fi
  if [ ! -f "$TMP/revb_$M.bin" ]; then
    echo "  FAIL  Mode $M never reached $WRITES video writes (no framebuffer dumped)"; fail=1
  elif cmp -s "$TMP/revb_$M.bin" "$TMP/ref.bin"; then
    echo "  PASS  Mode $M framebuffer == cosim after $WRITES video writes"
  else
    echo "  FAIL  Mode $M framebuffer differs from cosim @ $WRITES writes"
    echo "        first differing bytes (1-based offset, twin, cosim; octal):"
    cmp -l "$TMP/revb_$M.bin" "$TMP/ref.bin" | head -8 || true
    fail=1
  fi
done

if [ "$fail" = 0 ]; then
  echo "        (rev B CPU/Memory/Video/I-O cards boot ekta37 byte-identical to"
  echo "         cosim through both decode modes -- modular partition validated)"
  echo "REVB-MODULAR-BOOT-CHECK: PASS"
else
  echo "REVB-MODULAR-BOOT-CHECK: FAIL"; exit 1
fi
