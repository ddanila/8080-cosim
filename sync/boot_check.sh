#!/usr/bin/env bash
# Boot-regression guard for the MERGE: every HDL sim level must boot the real BIOS
# byte-for-byte identical to the cosim oracle. Bounded (stops after N video writes /
# on HLT) so it runs in seconds, never the slow full banner -- safe for CI (<10 min).
#
# Run from anywhere:  sync/boot_check.sh
set -euo pipefail
cd "$(dirname "$0")/.."                 # repo root
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
CC=${CC:-cc}
WRITES=6000                             # stop point for the real-boot cross-check
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
fail=0

echo "== generate ROM hex from vendored ROM =="
python3 -c "open('hdl/sim/ekta37.hex','w').write(chr(10).join('%02x'%b for b in open('roms/ekta37.bin','rb').read())+chr(10))"

echo "== build cosim =="
$CC -O2 -I cosim -o "$TMP/trace" cosim/trace.c cosim/i8080.c

echo "== cosim reference: real ekta37 boot @ $WRITES video writes =="
( cd cosim && "$TMP/trace" ../roms/ekta37.bin 50000000 "$WRITES" >/dev/null 2>&1 )
cp cosim/vram.bin "$TMP/ref_ekta37.bin"

echo "== HDL sims must match cosim @ $WRITES writes =="
# juku_top_tb drives the REAL LVS-checked netlist (juku_top.v + devices.v) -- it is THE model,
# and boots ekta37 bit-identically (proven deeper by sync/cosim_check.sh). juku_sim/chips are the
# earlier monolithic/chip-decomposed levels kept as stepping stones. (juku_struct is no longer a
# boot level here -- it now serves as the cosim_check oracle; hdl/sim/juku_struct.v.)
for tb in juku_sim_tb juku_chips_tb juku_top_tb; do
  case $tb in
    juku_sim_tb)    dump=vram_hdl.bin;    src="hdl/sim/$tb.v" ;;
    juku_chips_tb)  dump=vram_chips.bin;  src="hdl/sim/$tb.v" ;;
    juku_top_tb)    dump=vram_top.bin;    src="hdl/devices.v hdl/juku_top.v hdl/sim/$tb.v" ;;
  esac
  iverilog -g2012 -o "$TMP/$tb" hdl/vendor/vm80a.v $src
  vvp "$TMP/$tb" +maxvram=$WRITES >/dev/null 2>&1
  if cmp -s "$TMP/ref_ekta37.bin" "hdl/sim/$dump"; then echo "  PASS  $tb == cosim"
  else echo "  FAIL  $tb differs from cosim"; fail=1; fi
done

echo "== clock-mesh unit test (running divider self-clocks) =="
iverilog -g2012 -o "$TMP/clock_mesh_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/sim/clock_mesh_tb.v 2>/dev/null
if vvp "$TMP/clock_mesh_tb" 2>/dev/null | grep -q "\[mesh\] PASS"; then echo "  PASS  clock_mesh_tb (divider + SYNC-qualified strobe)"
else echo "  FAIL  clock_mesh_tb"; fail=1; fi

echo "== self-clocking boot: CPU runs on the mesh divider alone (-DSELF_CLOCK) =="
# No forced Φ1/Φ2, no external osc -- juku_top self-generates the clock from the running D40 divider.
# Must still boot ekta37 byte-identical to the cosim reference.
iverilog -g2012 -DSELF_CLOCK -o "$TMP/selfclk" hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/juku_selfclk_tb.v 2>/dev/null
vvp "$TMP/selfclk" +maxvram=$WRITES >/dev/null 2>&1
if cmp -s "$TMP/ref_ekta37.bin" hdl/sim/vram_selfclk.bin; then echo "  PASS  juku_selfclk_tb == cosim (CPU booted on self-generated mesh clock)"
else echo "  FAIL  juku_selfclk_tb differs from cosim"; fail=1; fi

echo "== synthetic-ROM datapath check (self-contained, HLT-bounded) =="
( cd cosim && "$TMP/trace" ../tests/regress.bin 1000000 >/dev/null 2>&1 )   # halts after 256 writes
cp cosim/vram.bin "$TMP/ref_regress.bin"
vvp "$TMP/juku_top_tb" +rom=tests/regress.hex +maxvram=256 >/dev/null 2>&1
if cmp -s "$TMP/ref_regress.bin" hdl/sim/vram_top.bin; then echo "  PASS  synthetic ROM: HDL == cosim"
else echo "  FAIL  synthetic ROM: HDL differs from cosim"; fail=1; fi

if [ "$fail" = 0 ]; then echo "BOOT-CHECK: PASS (merge intact)"; else echo "BOOT-CHECK: FAIL"; exit 1; fi
