#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null
command -v vvp >/dev/null

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/network-rom/build_network_rom.py --check
python3 - "$tmp/network-rom.hex" <<'PY'
from pathlib import Path
import sys

image = Path(
    "spinoffs/jukuravi/network-rom/juku-network-rom-abi1.bin"
).read_bytes()
Path(sys.argv[1]).write_text("\n".join(f"{byte:02x}" for byte in image) + "\n")
PY

PYTHONPATH=spinoffs/jukuravi/network-rom python3 - "$tmp/network-rom-abi.hex" <<'PY'
from pathlib import Path
import sys
import build_network_rom

image, _ = build_network_rom.build(abi_selftest=True)
Path(sys.argv[1]).write_text("\n".join(f"{byte:02x}" for byte in image) + "\n")
PY

PYTHONPATH=spinoffs/jukuravi/network-rom python3 - "$tmp/network-rom-netdisk.hex" <<'PY'
from pathlib import Path
import sys
import build_network_rom

image, _ = build_network_rom.build(
    abi_selftest=True, netdisk_selftest=True,
)
Path(sys.argv[1]).write_text("\n".join(f"{byte:02x}" for byte in image) + "\n")
PY

iverilog -g2012 -o "$tmp/network-first-rom-tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
  hdl/sim/network_first_rom_tb.v
output=$(vvp "$tmp/network-first-rom-tb" +rom="$tmp/network-rom.hex")
printf '%s\n' "$output"
grep -q "NETWORK-FIRST-ROM-HDL: PASS" <<<"$output"
if grep -q "NETWORK-FIRST-ROM-HDL: FAIL" <<<"$output"; then
  exit 1
fi

iverilog -g2012 -o "$tmp/network-first-rom-abi-tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
  hdl/sim/network_first_rom_abi_tb.v
output=$(vvp "$tmp/network-first-rom-abi-tb" \
  +rom="$tmp/network-rom-abi.hex")
printf '%s\n' "$output"
grep -q "NETWORK-FIRST-ROM-ABI-HDL: PASS" <<<"$output"
if grep -q "NETWORK-FIRST-ROM-ABI-HDL: FAIL" <<<"$output"; then
  exit 1
fi

output=$(vvp "$tmp/network-first-rom-abi-tb" \
  +rom="$tmp/network-rom-netdisk.hex" +netdisk)
printf '%s\n' "$output"
grep -q "NETWORK-FIRST-ROM-ABI-HDL: PASS" <<<"$output"
grep -q "netdisk_dma=128" <<<"$output"
if grep -q "NETWORK-FIRST-ROM-ABI-HDL: FAIL" <<<"$output"; then
  exit 1
fi
