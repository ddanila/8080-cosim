#!/usr/bin/env bash
# VJUGA Juku-ROM boot check.
#
# VJUGA is a single-+5 V board built around a Z80 (T80 core), chosen so the
# board needs no +12 V / -5 V rails that the Juku's original 8080 (КР580ВМ80)
# requires. The stock Juku firmware is 8080 code with three bytes a Z80 decodes
# differently, so VJUGA runs a 3-byte-patched ROM (roms/ekta37_z80.bin, derived
# from roms/ekta37.bin -- see roms/README.md).
#
# This check proves the whole chain:
#   1. regenerate ekta37_z80.bin and confirm it matches the committed copy;
#   2. confirm the patch does NOT change 8080 behavior (cosim identical on the
#      original vs patched ROM);
#   3. boot the patched ROM on the VJUGA T80 core in Z80 mode and confirm the
#      framebuffer is byte-for-byte identical to the cosim oracle after N video
#      writes -- the same ROM/map/oracle the main sync/boot_check.sh uses.
#
# No FDC, no interrupts: the ekta37 banner draws without them (cosim runs the
# same way with the frame interrupt off).
set -euo pipefail

WRITES=${WRITES:-6000}
CPU_MODE=${CPU_MODE:-0}                # T80 mode: 0 = Z80 (VJUGA's actual CPU)

MV="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$MV/../.." && pwd)"
command -v ghdl >/dev/null || { echo "ghdl not found"; exit 2; }
CC=${CC:-cc}
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== reuse recreation oracle: build cosim + make_z80_rom =="
$CC -O2 -I "$ROOT/cosim" -o "$TMP/trace" \
  "$ROOT/cosim/trace.c" "$ROOT/cosim/i8080.c" "$ROOT/cosim/juk_disk.c" "$ROOT/cosim/juku_fdc.c"
$CC -O2 -I "$ROOT/cosim" -o "$TMP/mkz80" "$MV/tools/make_z80_rom.c" "$ROOT/cosim/i8080.c"

echo "== regenerate Z80 ROM and check it matches the committed copy =="
"$TMP/mkz80" "$ROOT/roms/ekta37.bin" "$TMP/ekta37_z80.bin" "$WRITES" >/dev/null 2>&1
if ! cmp -s "$TMP/ekta37_z80.bin" "$MV/roms/ekta37_z80.bin"; then
  echo "  FAIL  regenerated ekta37_z80.bin differs from the committed roms/ekta37_z80.bin"; exit 1
fi
echo "  PASS  committed Z80 ROM is reproducible"

echo "== confirm the patch is 8080-behavior-preserving (cosim original vs patched) =="
( cd "$ROOT/cosim" && "$TMP/trace" "$ROOT/roms/ekta37.bin"        50000000 "$WRITES" >/dev/null 2>&1 ); cp "$ROOT/cosim/vram.bin" "$TMP/ref_orig.bin"
( cd "$ROOT/cosim" && "$TMP/trace" "$MV/roms/ekta37_z80.bin"      50000000 "$WRITES" >/dev/null 2>&1 ); cp "$ROOT/cosim/vram.bin" "$TMP/ref.bin"
if ! cmp -s "$TMP/ref_orig.bin" "$TMP/ref.bin"; then
  echo "  FAIL  patch changed 8080 behavior (cosim framebuffers differ)"; exit 1
fi
echo "  PASS  cosim draws the identical framebuffer from the original and patched ROM"

echo "== build VJUGA T80 + Juku-boot top (ghdl) =="
python3 -c "open('$TMP/ekta37_z80.hex','w').write(chr(10).join('%02x'%b for b in open('$MV/roms/ekta37_z80.bin','rb').read())+chr(10))"
W="$TMP/work"; mkdir -p "$W"
( cd "$MV"
  while IFS= read -r f; do
    ghdl -a --workdir="$W" --std=08 -fsynopsys "$(echo "$f" | sed 's#^../external#external#')" >/dev/null 2>&1
  done < hdl/t80-vhdl.files
  ghdl -a --workdir="$W" --std=08 -fsynopsys hdl/juku_boot_top.vhd >/dev/null 2>&1
  ghdl -a --workdir="$W" --std=08 -fsynopsys hdl/juku_boot_tb.vhd  >/dev/null 2>&1
  ghdl -e --workdir="$W" --std=08 -fsynopsys juku_boot_tb          >/dev/null 2>&1 )

echo "== boot the Z80 ROM on VJUGA (T80 mode $CPU_MODE) and dump its framebuffer =="
( cd "$MV" && ghdl -r --workdir="$W" --std=08 -fsynopsys juku_boot_tb \
    -grom_file="$TMP/ekta37_z80.hex" -gvw_limit="$WRITES" -gdump_file="$TMP/vjuga.bin" -gcpu_mode="$CPU_MODE" \
    --ieee-asserts=disable >/dev/null 2>&1 )

if [ ! -f "$TMP/vjuga.bin" ]; then
  echo "  FAIL  VJUGA never reached $WRITES video writes (no framebuffer dumped)"; exit 1
fi
if cmp -s "$TMP/vjuga.bin" "$TMP/ref.bin"; then
  echo "  PASS  VJUGA framebuffer == cosim after $WRITES video writes (real Z80 boots the Juku ROM)"
  echo "VJUGA-BOOT-CHECK: PASS"
else
  echo "  FAIL  VJUGA framebuffer differs from cosim @ $WRITES writes"
  echo "VJUGA-BOOT-CHECK: FAIL"; exit 1
fi
