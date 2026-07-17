#!/usr/bin/env bash
# VJUGA rev B per-card unit tests (Phase B0). Drives each card in isolation with
# the bus-functional model (revb_bus_bfm.vh) and checks its bus behavior. Also
# proves the harness can fail (mem card with +injectfail must report FAIL).
set -euo pipefail

MV="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$MV/../.." && pwd)"
TV="$MV/external/tv80/rtl/core"
REVB="$MV/hdl/revb"
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
fail=0

# Synthetic ROM for the mem-card TB: byte0=0x3C, byte1=0x4D, rest 0x00.
python3 -c "
lines=['3c','4d']+['00']*(16384-2)
open('$TMP/memtest.hex','w').write(chr(10).join(lines)+chr(10))"

run() {  # name  expect(PASS|FAIL)  tag  extra_iverilog_args...  -- extra_vvp_args...
  local name="$1" expect="$2" tag="$3"; shift 3
  local ivargs=() vvpargs=() seen=0
  for a in "$@"; do if [ "$a" = "--" ]; then seen=1; continue; fi
    if [ "$seen" = 0 ]; then ivargs+=("$a"); else vvpargs+=("$a"); fi; done
  iverilog -g2012 -I "$REVB" -o "$TMP/$name" ${ivargs[@]+"${ivargs[@]}"} 2>"$TMP/$name.log" || {
    echo "  FAIL  $name did not compile"; cat "$TMP/$name.log"; fail=1; return; }
  local out; out=$(vvp "$TMP/$name" ${vvpargs[@]+"${vvpargs[@]}"} 2>/dev/null || true)
  if echo "$out" | grep -q "$tag: PASS"; then got=PASS; else got=FAIL; fi
  if [ "$got" = "$expect" ]; then
    echo "  ok    $name -> $got (expected $expect)"
  else
    echo "  FAIL  $name -> $got (expected $expect)"; echo "$out" | sed 's/^/        /'; fail=1
  fi
}

echo "== per-card unit TBs =="
run mem PASS REVB-MEM-CARD-TB \
  -Prevb_mem_card_tb.rom_file="\"$TMP/memtest.hex\"" \
  "$ROOT/hdl/vendor/vm80a.v" "$ROOT/hdl/devices.v" \
  "$REVB/revb_mem_card.v" "$REVB/revb_mem_card_tb.v"
run io PASS REVB-IO-CARD-TB "$REVB/revb_io_card.v" "$REVB/revb_io_card_tb.v"
run video PASS REVB-VIDEO-CARD-TB "$REVB/revb_video_card.v" "$REVB/revb_video_card_tb.v"
run cpu PASS REVB-CPU-CARD-TB \
  "$TV/tv80_alu.v" "$TV/tv80_reg.v" "$TV/tv80_mcode.v" "$TV/tv80_core.v" "$TV/tv80s.v" \
  "$REVB/revb_cpu_card.v" "$REVB/revb_cpu_card_tb.v"

echo "== negative control (harness must catch a bad expectation) =="
run mem_inject FAIL REVB-MEM-CARD-TB \
  -Prevb_mem_card_tb.rom_file="\"$TMP/memtest.hex\"" \
  "$ROOT/hdl/vendor/vm80a.v" "$ROOT/hdl/devices.v" \
  "$REVB/revb_mem_card.v" "$REVB/revb_mem_card_tb.v" -- +injectfail

if [ "$fail" = 0 ]; then echo "REVB-CARD-TB-CHECK: PASS"; else echo "REVB-CARD-TB-CHECK: FAIL"; exit 1; fi
