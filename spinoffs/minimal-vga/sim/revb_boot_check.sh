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

# The B2 TTL-card boot below costs ~7 min on its own -- two async clocks (CPU plus
# the 25 MHz dot clock) make it far heavier than the single-clock mode boots, which
# together take ~100s. CI runs the two phases as separate parallel jobs so the slow
# one does not serialize the rest:
#   REVB_BOOT_PHASE=modes  decode Mode A/B boots only
#   REVB_BOOT_PHASE=ttl    the B2 chip-level TTL video-card boot only
# The default, "all", runs both -- so a plain local invocation is unchanged.
REVB_BOOT_PHASE=${REVB_BOOT_PHASE:-all}
case "$REVB_BOOT_PHASE" in
  all|modes|ttl) ;;
  *) echo "REVB_BOOT_PHASE must be all, modes or ttl (got '$REVB_BOOT_PHASE')" >&2; exit 2 ;;
esac

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

# Both phases drive the same cosim oracle binary, so always build it.
$CC -O2 -I "$ROOT/cosim" -o "$TMP/trace" \
  "$ROOT/cosim/trace.c" "$ROOT/cosim/i8080.c" "$ROOT/cosim/juk_disk.c" "$ROOT/cosim/juku_fdc.c"

fail=0
if [ "$REVB_BOOT_PHASE" = ttl ]; then
  echo "== decode Mode A/B boots -- SKIPPED (REVB_BOOT_PHASE=ttl) =="
else
echo "== reuse recreation oracle: cosim framebuffer @ $WRITES video writes =="
( cd "$ROOT/cosim" && "$TMP/trace" "$MV/roms/ekta37_z80.bin" 50000000 "$WRITES" >/dev/null 2>&1 )
cp "$ROOT/cosim/vram.bin" "$TMP/ref.bin"

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
    "$REVB/revb_video_card_ttl.v" \
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
fi

if [ "$REVB_BOOT_PHASE" = modes ]; then
  echo "== B2 TTL video-card boot -- SKIPPED (REVB_BOOT_PHASE=modes; own CI job) =="
else
# B2 (TI.3): integrated boot through the CHIP-LEVEL TTL video card, with the card's
# open-drain /WAIT wired into the CPU (VIDEO_TTL=1). Proves ekta37 boots byte-identical
# through the real framebuffer serving + cycle-steal contention (D2.9) with the actual T80,
# not just the behavioural card. Reduced write count: the two async clocks (CPU + 25 MHz
# dot) make this far heavier than the single-clock runs.
TTL_WRITES=${TTL_WRITES:-400}
echo "== B2: cosim reference @ $TTL_WRITES writes (TTL-card run) =="
( cd "$ROOT/cosim" && "$TMP/trace" "$MV/roms/ekta37_z80.bin" 50000000 "$TTL_WRITES" >/dev/null 2>&1 )
cp "$ROOT/cosim/vram.bin" "$TMP/ref_ttl.bin"
echo "== B2: boot rev B twin through the TTL video card (VIDEO_TTL=1, /WAIT contention) =="
iverilog -g2012 \
  -Prevb_backplane_tb.rom_file="\"$TMP/ekta37_z80.hex\"" \
  -Prevb_backplane_tb.vw_limit="$TTL_WRITES" \
  -Prevb_backplane_tb.decode_mode=0 \
  -Prevb_backplane_tb.video_ttl=1 \
  -Prevb_backplane_tb.dump_file="\"$TMP/revb_ttl.bin\"" \
  -o "$TMP/twin_ttl" \
  "$ROOT/hdl/vendor/vm80a.v" \
  "$TV/tv80_alu.v" "$TV/tv80_reg.v" "$TV/tv80_mcode.v" "$TV/tv80_core.v" "$TV/tv80s.v" \
  "$ROOT/hdl/devices.v" \
  "$REVB/revb_cpu_card.v" "$REVB/revb_mem_card.v" "$REVB/revb_video_card.v" \
  "$REVB/revb_video_card_ttl.v" \
  "$REVB/revb_io_card.v" "$REVB/revb_bus_monitor.v" \
  "$REVB/revb_backplane_top.v" "$REVB/revb_backplane_tb.v"
timeout 400 vvp "$TMP/twin_ttl" >"$TMP/run_ttl.log" 2>&1 || true
if grep -q "REVB-BUS-CONFLICT" "$TMP/run_ttl.log"; then
  echo "  FAIL  TTL-card run raised a bus-driver conflict"; fail=1
elif [ ! -f "$TMP/revb_ttl.bin" ]; then
  echo "  FAIL  TTL card never reached $TTL_WRITES writes (timeout or /WAIT stall)"; fail=1
elif cmp -s "$TMP/revb_ttl.bin" "$TMP/ref_ttl.bin"; then
  echo "  PASS  TTL-card framebuffer == cosim after $TTL_WRITES writes (real chips + /WAIT)"
else
  echo "  FAIL  TTL-card framebuffer differs from cosim @ $TTL_WRITES writes (D2.9)"; fail=1
fi
fi

if [ "$fail" = 0 ]; then
  case "$REVB_BOOT_PHASE" in
    all)
      echo "        (rev B CPU/Memory/Video/I-O cards boot ekta37 byte-identical to cosim"
      echo "         through both decode modes AND through the chip-level TTL video card)"
      echo "REVB-MODULAR-BOOT-CHECK: PASS" ;;
    modes)
      echo "        (rev B cards boot ekta37 byte-identical to cosim through both"
      echo "         decode modes; the TTL video-card boot runs as its own job)"
      echo "REVB-MODULAR-BOOT-CHECK(modes): PASS" ;;
    ttl)
      echo "        (rev B cards boot ekta37 byte-identical to cosim through the"
      echo "         chip-level TTL video card, real chips plus /WAIT contention)"
      echo "REVB-MODULAR-BOOT-CHECK(ttl): PASS" ;;
  esac
else
  echo "REVB-MODULAR-BOOT-CHECK($REVB_BOOT_PHASE): FAIL"; exit 1
fi
