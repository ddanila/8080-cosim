#!/usr/bin/env bash
# VJUGA rev B minimum-tier bring-up check (Phase B1, T1.2). Boots the T1.1 bring-up
# ROM on BOTH the cosim reference and the minimum-tier modular twin (CPU + Memory +
# I/O with the real 8251, no Video card), and confirms the UART TX byte stream is
# identical -- i.e. the ROM behaves the same driven by the real USART TxRDY as under
# cosim, and the modular partition works with the framebuffer window unowned.
set -euo pipefail

MV="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$MV/../.." && pwd)"
TV="$MV/external/tv80/rtl/core"
REVB="$MV/hdl/revb"
BRDIR="$MV/roms/revb-bringup"
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
if [ ! -f "$TV/tv80s.v" ]; then echo "  SKIP tv80 submodule not initialized"; exit 0; fi
CC=${CC:-cc}
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

# Fast-range build (RAM test 0x4000..0x40FF) so the HDL twin's RAM test finishes
# quickly. The SAME binary runs on cosim and the twin, so the TX byte-identity
# stays meaningful; the full-range test is covered under cosim in T1.1.
echo "== build the bring-up ROM (fast sim variant) =="
python3 "$BRDIR/build_bringup.py" 0x41 "$TMP/fast.bin" >/dev/null
python3 -c "open('$TMP/br.hex','w').write(chr(10).join('%02x'%b for b in open('$TMP/fast.bin','rb').read())+chr(10))"

echo "== cosim reference TX stream (OUT 0x08) =="
$CC -O2 -I "$ROOT/cosim" -o "$TMP/trace" \
  "$ROOT/cosim/trace.c" "$ROOT/cosim/i8080.c" "$ROOT/cosim/juk_disk.c" "$ROOT/cosim/juku_fdc.c"
( cd "$ROOT/cosim" && JUKU_TRACE_IO=1 "$TMP/trace" "$TMP/fast.bin" 20000000 0 2>"$TMP/io.log" >/dev/null )
python3 -c "
import re
bs=[int(m,16) for m in re.findall(r'OUT port=0x08 value=0x([0-9A-Fa-f]{2})', open('$TMP/io.log').read())]
open('$TMP/ref.bin','wb').write(bytes(bs))
open('$TMP/n.txt','w').write(str(len(bs)))
print('   cosim TX bytes:', len(bs))
"
N=$(cat "$TMP/n.txt")

echo "== build + run minimum-tier twin (real 8251, no Video) =="
iverilog -g2012 \
  -Prevb_bringup_tb.rom_file="\"$TMP/br.hex\"" \
  -Prevb_bringup_tb.tx_log="\"$TMP/twin_tx.bin\"" \
  -Prevb_bringup_tb.expect_bytes="$N" \
  -o "$TMP/twin" \
  "$ROOT/hdl/vendor/vm80a.v" \
  "$TV/tv80_alu.v" "$TV/tv80_reg.v" "$TV/tv80_mcode.v" "$TV/tv80_core.v" "$TV/tv80s.v" \
  "$ROOT/hdl/devices.v" \
  "$REVB/revb_cpu_card.v" "$REVB/revb_mem_card.v" "$REVB/revb_video_card.v" \
  "$REVB/revb_io_card.v" "$REVB/revb_bus_monitor.v" \
  "$REVB/revb_backplane_top.v" "$REVB/revb_bringup_tb.v"
vvp "$TMP/twin" >"$TMP/run.log" 2>&1 || true

fail=0
if grep -q "REVB-BUS-CONFLICT" "$TMP/run.log"; then
  echo "  FAIL  bus-driver conflict during bring-up"; grep "REVB-BUS-CONFLICT" "$TMP/run.log" | head -2 | sed 's/^/        /'; fail=1
fi
if [ ! -s "$TMP/twin_tx.bin" ]; then
  echo "  FAIL  twin produced no TX bytes"; grep BRINGUP-TB "$TMP/run.log" | sed 's/^/        /'; fail=1
elif cmp -s "$TMP/twin_tx.bin" "$TMP/ref.bin"; then
  echo "  PASS  twin TX stream == cosim ($N bytes), real-8251 handshake"
  python3 -c "s=open('$TMP/ref.bin','rb').read().decode('latin1'); assert 'RAM PASS' in s, 'RAM PASS missing'; print('  PASS  stream contains RAM PASS')"
else
  echo "  FAIL  twin TX stream differs from cosim"
  echo "        cosim:" $(python3 -c "print(repr(open('$TMP/ref.bin','rb').read()[:48]))")
  echo "        twin :" $(python3 -c "print(repr(open('$TMP/twin_tx.bin','rb').read()[:48]))")
  fail=1
fi

if [ "$fail" = 0 ]; then echo "REVB-BRINGUP-CHECK: PASS"; else echo "REVB-BRINGUP-CHECK: FAIL"; exit 1; fi
