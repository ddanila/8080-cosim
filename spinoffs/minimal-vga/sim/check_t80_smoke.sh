#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

while IFS= read -r f; do
  ghdl -a --workdir="$tmp" --std=08 -fsynopsys "$f"
done < <(sed 's#^../external#external#' hdl/t80-vhdl.files)

ghdl -a --workdir="$tmp" --std=08 -fsynopsys hdl/z80_minimal_top.vhd
ghdl -a --workdir="$tmp" --std=08 -fsynopsys hdl/z80_minimal_tb.vhd
ghdl -e --workdir="$tmp" --std=08 -fsynopsys z80_minimal_tb
ghdl -r --workdir="$tmp" --std=08 -fsynopsys z80_minimal_tb --assert-level=error
