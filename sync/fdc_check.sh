#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

echo "== HDL WD1793 synthetic-sector check =="
iverilog -g2012 -o "$TMP/fdc_1793_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/sim/fdc_1793_tb.v
out=$(vvp "$TMP/fdc_1793_tb")
echo "$out"
if ! printf '%s\n' "$out" | grep -q "FDC-1793: PASS"; then
  echo "FDC-CHECK: FAIL"
  exit 1
fi

echo "== HDL WD1793 vendored-media check =="
disk_out=$(vvp "$TMP/fdc_1793_tb" +disk=media/disks/JUKU1.CPM +disk_heads=2 +expect_disk)
echo "$disk_out"
if ! printf '%s\n' "$disk_out" | grep -q "FDC-1793: PASS"; then
  echo "FDC-CHECK: FAIL"
  exit 1
fi

cat > docs/fdc-readiness.md <<'EOF'
# FDC readiness

Status: **HDL WD1793 VENDORED-MEDIA SECTOR READY**

This guard proves the first HDL-side WD1793 behavior slice needed by WS-B1:

- `hdl/devices.v` implements D93-compatible restore, seek, read-sector,
  status, track, sector, data register, DRQ, and INTRQ behavior in
  `fdc_1793`.
- `hdl/sim/fdc_1793_tb.v` mirrors the C-side synthetic media guard:
  restore returns to track 0, seek copies the data register to the track
  register, read-sector streams 512 bytes, side select changes the stream,
  and motor-off read reports not-ready.
- The same testbench also runs with `+disk=media/disks/JUKU1.CPM +disk_heads=2`
  and verifies that the HDL WD1793 path reads real bytes from the vendored raw
  disk image.
- `docs/fdc-core-survey.md` records why this remains a bounded boot shim rather
  than a growing manual replacement for a full upstream ВГ93/WD1793 core.

## Command

```sh
sync/fdc_check.sh
```

## Evidence

| Check | Result |
| --- | --- |
| Restore command clears transfer and returns to track 0 | PASS |
| Seek command copies data register to track register | PASS |
| Read-sector command asserts BUSY/DRQ and streams 512 bytes | PASS |
| Side select affects the synthetic sector stream | PASS |
| Vendored `JUKU1.CPM` sector 2 bytes are streamed through the HDL FDC | PASS |
| DRQ asserts during the sector transfer and INTRQ asserts on completion | PASS |
| Motor-off read reports NOT READY | PASS |

## Remaining Boundary

- Drive the full `ROMBIOS 3.43` `<T>, <D>, <D>` path through `juku_top` with
  `+disk=media/disks/JUKU1.CPM` and promote the HDL boundary from sector-ready
  to EKDOS-prompt-ready.
- Preserve the Arti `JUKU1.CPM` cosim proof from
  `docs/ekdos-media-acquisition.md` as the disk-backed reference.
- If deeper controller behavior becomes the blocker, decide whether GPL
  Sorgelig-lineage `wd1793.sv` is acceptable to vendor/adapt.
- Confirm D93 INTRQ/DRQ, MR, CLK, and D100 OE/T wiring during the owner session.
EOF

echo "FDC-CHECK: PASS"
echo "Wrote docs/fdc-readiness.md"
