#!/usr/bin/env bash
# R5.I6: exact production-ROM execution plus the revised I/O-card clock paths.
set -euo pipefail

MV="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$MV/../.." && pwd)"
REVB="$MV/hdl/revb"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }

echo "== R5.I6: reproducible ROM set and early no-stack contract =="
python3 "$MV/roms/check_revb_rom_set.py"

echo "== R5.I6: C10 exact D57/USART/POF sequence in all clock-source modes =="
for source in 1 0 2; do
  iverilog -g2012 -s revb_c10_io_tb \
    -Prevb_c10_io_tb.CLK_SOURCE="$source" -o "$TMP/c10-$source" \
    "$ROOT/hdl/devices.v" "$REVB/revb_io_card.v" "$REVB/revb_c10_io_tb.v"
  output="$(vvp "$TMP/c10-$source")"
  printf '%s\n' "$output"
  grep -q "REVB-C10-IO: PASS source=$source" <<<"$output"
done

echo "== R5.I6: production NETC10 and DIAG observability/failure ordering =="
python3 "$MV/sim/check_revb_rom_system.py" --self-test

echo "== R5.I6: exact ABI 1.4 request/reply at the TTL connector =="
"$MV/sim/revb_serial_console_check.sh"

echo "== R5.I6: C9 blank-video control and C10 visible-output correction =="
cc -O2 -I "$ROOT/cosim" -o "$TMP/trace" \
  "$ROOT/cosim/trace.c" "$ROOT/cosim/i8080.c" \
  "$ROOT/cosim/juk_disk.c" "$ROOT/cosim/juku_fdc.c"
python3 "$ROOT/tests/network_first_rom_c10_video_test.py" "$TMP/trace"

# This is the long CPU/Memory/Video integration leg. The default is the full
# acceptance run; CI may split it into modes and ttl jobs using the existing
# revb_boot_check interface without changing either oracle.
EKTA_PHASE="${REVB_I6_EKTA_PHASE:-all}"
echo "== R5.I6: EKTA3.7 framebuffer equivalence (phase=$EKTA_PHASE) =="
REVB_BOOT_PHASE="$EKTA_PHASE" "$MV/sim/revb_boot_check.sh"

echo "REVB-ROM-SYSTEM-CHECK(I6): PASS"
