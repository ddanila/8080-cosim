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
  echo "BASIC-CART-CHECK: FAIL (physical D8 did not keep D22 released)"
  exit 1
fi

first=$(od -An -tx1 -N1 "$TMP/ref_cart.bin" | tr -d ' \n')
if [ "$first" != "c3" ]; then
  echo "BASIC-CART-CHECK: FAIL (expected cosim to read jbasic11 first byte c3, got $first)"
  exit 1
fi

cat > docs/basic-cart-readiness.md <<'EOF'
# BASIC cartridge readiness

Status: **PHYSICAL D8 CARTRIDGE WINDOW CLOSED / COSIM OPTION BOUNDED**

This guard records a now-proved hardware/emulator distinction for the optional
`jbasic11.bin` cartridge path:

- cosim loads `JUKU_CART=roms/jbasic11.bin` and exposes it in memory mode 2 at
  `0x4000..0xBFFF`.
- The repeated physical D8 `.039` table returns `0xFF` for the `0x4000` row,
  so every socket select including D22 remains released. The HDL unit test
  proves that a populated D22 therefore cannot drive the bus in this state.
- `tests/cart_window.hex` copies a tiny routine to RAM, switches to mode 2,
  reads byte `0x4000` from the cartridge, switches to mode 3, and writes the
  byte to VRAM under cosim. That behavior is an explicit MAME-compatible option,
  not a claim about the stock physical `.039` program.

## Command

```sh
sync/basic_cart_check.sh
```

## Evidence

| Check | Result |
| --- | --- |
| cosim `JUKU_CART` byte visible at `0x4000` | `0xC3` |
| HDL physical D8 row at `0x4000` | `0xFF` |
| HDL D22 bus contribution | released (`Z`) |

## Remaining Boundary

- Monitor 3.3 cartridge BASIC remains an artifact/procedure/configuration
  boundary summarized in `docs/cartridge-basic-boundary.md`. A different PROM,
  strap, expander decode, or procedure may be required. Disk-side BASIC is
  independently proven and this optional branch is not a fabrication blocker.
EOF

echo "BASIC-CART-CHECK: PASS"
echo "Wrote docs/basic-cart-readiness.md"
