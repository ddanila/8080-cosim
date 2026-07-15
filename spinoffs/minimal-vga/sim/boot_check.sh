#!/usr/bin/env bash
# VJUGA Juku-ROM boot check.
#
# Proves the VJUGA T80 top boots the REAL Juku ekta37 ROM by producing a
# framebuffer byte-identical to the recreation's cosim oracle after N video
# writes -- the same oracle+ROM the main sync/boot_check.sh uses. This is the
# VJUGA release-gate item "boot the intended real Juku ROM on the VJUGA top".
#
# Reused from the 8080-cosim recreation: roms/ekta37.bin (the ROM), cosim (the
# reference emulator), the Juku memory map, and the 0xD800 framebuffer format.
# VJUGA supplies its own Z80/T80 core (run in 8080 mode) + memory subsystem.
#
# No FDC, no interrupts: the ekta37 banner draws without them, exactly as cosim
# runs it (frame interrupt off).
set -euo pipefail

WRITES=${WRITES:-6000}                 # video writes before dump/compare (matches boot_check)
CPU_MODE=${CPU_MODE:-2}                # T80 mode: 2 = 8080 (Juku firmware is 8080 code)

MV="$(cd "$(dirname "$0")/.." && pwd)" # spinoffs/minimal-vga
ROOT="$(cd "$MV/../.." && pwd)"        # repo root
command -v ghdl >/dev/null || { echo "ghdl not found"; exit 2; }
command -v iverilog >/dev/null 2>&1 || true
CC=${CC:-cc}
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== reuse recreation ROM: generate ekta37.hex =="
python3 -c "open('$TMP/ekta37.hex','w').write(chr(10).join('%02x'%b for b in open('$ROOT/roms/ekta37.bin','rb').read())+chr(10))"

echo "== reuse recreation oracle: cosim reference framebuffer @ $WRITES video writes =="
$CC -O2 -I "$ROOT/cosim" -o "$TMP/trace" \
  "$ROOT/cosim/trace.c" "$ROOT/cosim/i8080.c" "$ROOT/cosim/juk_disk.c" "$ROOT/cosim/juku_fdc.c"
( cd "$ROOT/cosim" && "$TMP/trace" "$ROOT/roms/ekta37.bin" 50000000 "$WRITES" >/dev/null 2>&1 )
cp "$ROOT/cosim/vram.bin" "$TMP/ref.bin"

echo "== build VJUGA T80 + Juku-boot top (ghdl) =="
W="$TMP/work"; mkdir -p "$W"
( cd "$MV"
  while IFS= read -r f; do
    ghdl -a --workdir="$W" --std=08 -fsynopsys "$(echo "$f" | sed 's#^../external#external#')" >/dev/null 2>&1
  done < hdl/t80-vhdl.files
  ghdl -a --workdir="$W" --std=08 -fsynopsys hdl/juku_boot_top.vhd >/dev/null 2>&1
  ghdl -a --workdir="$W" --std=08 -fsynopsys hdl/juku_boot_tb.vhd  >/dev/null 2>&1
  ghdl -e --workdir="$W" --std=08 -fsynopsys juku_boot_tb          >/dev/null 2>&1 )

echo "== boot the real ROM on VJUGA and dump its framebuffer =="
( cd "$MV" && ghdl -r --workdir="$W" --std=08 -fsynopsys juku_boot_tb \
    -grom_file="$TMP/ekta37.hex" -gvw_limit="$WRITES" -gdump_file="$TMP/vjuga.bin" -gcpu_mode="$CPU_MODE" \
    --ieee-asserts=disable >/dev/null 2>&1 )

if [ ! -f "$TMP/vjuga.bin" ]; then
  echo "  FAIL  VJUGA never reached $WRITES video writes (no framebuffer dumped)"; exit 1
fi
if cmp -s "$TMP/vjuga.bin" "$TMP/ref.bin"; then
  echo "  PASS  VJUGA framebuffer == cosim after $WRITES video writes (8080-mode T80 boots ekta37)"
  echo "VJUGA-BOOT-CHECK: PASS"
else
  echo "  FAIL  VJUGA framebuffer differs from cosim @ $WRITES writes"
  cmp "$TMP/vjuga.bin" "$TMP/ref.bin" || true
  echo "VJUGA-BOOT-CHECK: FAIL"; exit 1
fi
