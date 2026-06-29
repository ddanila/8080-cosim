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
for tb in juku_sim_tb juku_chips_tb juku_struct_tb; do
  case $tb in
    juku_sim_tb)    dump=vram_hdl.bin ;;
    juku_chips_tb)  dump=vram_chips.bin ;;
    juku_struct_tb) dump=vram_struct.bin ;;
  esac
  iverilog -g2012 -o "$TMP/$tb" hdl/vendor/vm80a.v "hdl/sim/$tb.v"
  vvp "$TMP/$tb" +maxvram=$WRITES >/dev/null 2>&1
  if cmp -s "$TMP/ref_ekta37.bin" "hdl/sim/$dump"; then echo "  PASS  $tb == cosim"
  else echo "  FAIL  $tb differs from cosim"; fail=1; fi
done

echo "== synthetic-ROM datapath check (self-contained, HLT-bounded) =="
( cd cosim && "$TMP/trace" ../tests/regress.bin 1000000 >/dev/null 2>&1 )   # halts after 256 writes
cp cosim/vram.bin "$TMP/ref_regress.bin"
vvp "$TMP/juku_struct_tb" +rom=tests/regress.hex +maxvram=256 >/dev/null 2>&1
if cmp -s "$TMP/ref_regress.bin" hdl/sim/vram_struct.bin; then echo "  PASS  synthetic ROM: HDL == cosim"
else echo "  FAIL  synthetic ROM: HDL differs from cosim"; fail=1; fi

if [ "$fail" = 0 ]; then echo "BOOT-CHECK: PASS (merge intact)"; else echo "BOOT-CHECK: FAIL"; exit 1; fi
