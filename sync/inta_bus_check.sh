#!/usr/bin/env bash
# Focused end-to-end MCS-80 interrupt differential. The C reference and vm80a
# execute the same PIC-programming/EI loop; the first model-generated frame edge
# must produce three typed INTA events carrying CALL FED4 in both implementations.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
CC=${CC:-cc}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

python3 tests/build_inta_bus_rom.py "$TMP/inta.bin"
python3 tests/build_inta_bus_rom.py --hex "$TMP/inta.hex"

$CC -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$TMP/trace" cosim/trace.c cosim/i8080.c cosim/juk_disk.c cosim/juku_fdc.c
(
  cd cosim
  JUKU_BUS_TRACE="$TMP/events.txt" JUKU_BUS_TRACE_LIMIT=500 \
    "$TMP/trace" "$TMP/inta.bin" 20000 0 1000 >/dev/null 2>"$TMP/cosim.err"
)

first_ia=$(awk '$1 == "IA" { print NR; exit }' "$TMP/events.txt")
if [ -z "$first_ia" ] || [ "$first_ia" -le 2 ]; then
  echo "INTA-BUS-CHECK: FAIL (C trace did not reach INTA)"
  exit 1
fi
# intr_ctl samples frame_tick before vm80a samples INTR at the instruction
# boundary. Assert during the penultimate bus transfer; the final operand read
# still matches before the first IA event.
irq_after=$((first_ia - 2))
awk '
  $1 == "IA" { count++; byte[count] = tolower($3) }
  END {
    if (count != 3 || byte[1] != "cd" || byte[2] != "d4" || byte[3] != "fe")
      exit 1
  }
' "$TMP/events.txt" || {
  echo "INTA-BUS-CHECK: FAIL (C INTA sequence is not CD D4 FE)"
  exit 1
}

iverilog -g2012 -o "$TMP/btrace" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/cosim_ctrace_tb.v
vvp "$TMP/btrace" +rom="$TMP/inta.hex" +trace="$TMP/events.txt" \
  +irq_after="$irq_after" +timecap=3000000 2>&1 | tee "$TMP/out"

grep -q "BTRACE-END" "$TMP/out" || {
  echo "INTA-BUS-CHECK: FAIL (typed C/HDL trace did not complete)"
  exit 1
}
echo "INTA-BUS-CHECK: PASS (vm80a/PIC matched C across 500 events; IA=CD D4 FE)"
