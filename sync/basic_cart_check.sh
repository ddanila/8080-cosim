#!/usr/bin/env bash
# Guard the optional BASIC/cartridge ROM window without making the normal boot
# depend on a populated expansion socket.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
CC=${CC:-cc}
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== generate cartridge readmemh image =="
python3 - <<'PY'
from pathlib import Path
rom = Path("roms/jbasic11.bin").read_bytes()
Path("hdl/sim/jbasic11.hex").write_text("\n".join(f"{byte:02x}" for byte in rom) + "\n")
PY

echo "== build cosim =="
$CC -O2 -I cosim -o "$TMP/trace" cosim/trace.c cosim/i8080.c cosim/juk_disk.c cosim/juku_fdc.c

echo "== cosim cartridge-window reference =="
( cd cosim && JUKU_CART=../roms/jbasic11.bin "$TMP/trace" ../tests/cart_window.hex 1000000 1 >/dev/null 2>&1 )
cp cosim/vram.bin "$TMP/ref_cart.bin"

echo "== HDL D8/D22 cartridge-window check =="
iverilog -g2012 -o "$TMP/basic_cart_window_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/sim/basic_cart_window_tb.v
if ! vvp "$TMP/basic_cart_window_tb" +cart=hdl/sim/jbasic11.hex | grep -q "BASIC-CART-WINDOW: PASS"; then
  echo "BASIC-CART-CHECK: FAIL (D8/D22 cartridge window did not expose jbasic11)"
  exit 1
fi

first=$(od -An -tx1 -N1 "$TMP/ref_cart.bin" | tr -d ' \n')
if [ "$first" != "c3" ]; then
  echo "BASIC-CART-CHECK: FAIL (expected cosim to read jbasic11 first byte c3, got $first)"
  exit 1
fi

cat > docs/basic-cart-readiness.md <<'EOF'
# BASIC cartridge readiness

Status: **BASIC CARTRIDGE WINDOW READY**

This guard proves the optional MAME-compatible expansion cartridge window used by
`jbasic11.bin`:

- cosim loads `JUKU_CART=roms/jbasic11.bin` and exposes it in memory mode 2 at
  `0x4000..0xBFFF`.
- `juku_top` keeps D17-D21 passive and can populate D22 with `+cart=<readmemh>`
  for the traced `0x4000..0x5FFF` BASIC socket; the HDL unit test checks D8's
  pager byte and D22's driven byte directly.
- `tests/cart_window.hex` copies a tiny routine to RAM, switches to mode 2,
  reads byte `0x4000` from the cartridge, switches to mode 3, and writes the
  byte to VRAM under cosim. The HDL unit independently checks the same D8/D22
  window and both paths must expose `0xC3`, the first byte of `jbasic11.bin`.

## Command

```sh
sync/basic_cart_check.sh
```

## Evidence

| Check | Result |
| --- | --- |
| cosim `JUKU_CART` byte visible at `0x4000` | `0xC3` |
| HDL D8 pager selects D22 for `0x4000..0x5FFF` | `0xF7` |
| HDL D22 drives `jbasic11.bin[0]` | `0xC3` |

## Remaining Boundary

- Resolve the Monitor 3.3 cartridge BASIC path to a live prompt. `sync/basic_launch_probe.py` now
  documents that Monitor 3.3 reads both `jbasic11.bin` and the legacy BAS0-3
  image from the cartridge overlay and then executes in the `0x4000..0xBFFF`
  RAM window. The launch probe records this as a compatibility boundary because
  the local MAME source warns about Monitor 3.3/JBASIC compatibility and both
  BASIC images enter with absolute `JMP 0x0107`.
EOF

echo "BASIC-CART-CHECK: PASS"
echo "Wrote docs/basic-cart-readiness.md"
