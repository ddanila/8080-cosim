#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "== HDL WD1793 synthetic-sector check =="
iverilog -g2012 -o "$TMP/fdc_1793_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/sim/fdc_1793_tb.v
out=$(vvp "$TMP/fdc_1793_tb")
echo "$out"
grep -q "FDC-1793: PASS" <<<"$out" || { echo "FDC-CHECK: FAIL"; exit 1; }

echo "== HDL WD1793 vendored-media check =="
disk_out=$(vvp "$TMP/fdc_1793_tb" +disk=media/disks/JUKU1.CPM +disk_heads=2 +expect_disk)
echo "$disk_out"
grep -q "FDC-1793: PASS" <<<"$disk_out" || { echo "FDC-CHECK: FAIL"; exit 1; }

echo "== juku_top decoded peripheral bus check =="
sync/juku_top_periph_bus_check.sh

cat > docs/fdc-readiness.md <<'EOF'
# FDC readiness

Status: **BOOT-SCOPED HDL FDC READY**

`sync/fdc_check.sh` guards the FDC behavior needed by the proven Juku boot
path. It does not claim a complete WD1793/VG93 implementation or complete
physical D93/D94 wiring.

## Passing scope

- Restore, seek, step, step-in, step-out, read-sector, track/sector/data
  registers, BUSY/DRQ/INTRQ, side select, and motor-not-ready behavior.
- A 512-byte synthetic sector transfer and bytes from vendored
  `media/disks/JUKU1.CPM`.
- Read-only-backend write-track rejection with WRITE PROTECT instead of an
  endless BUSY state.
- Direct decoded `juku_top` keyboard/PIC/PPI/FDC bus access through
  `sync/juku_top_periph_bus_check.sh`.
- The committed uninterrupted Verilator report
  `docs/juku-top-fdc-verilator-probe.md` drains all 10,752 FDC data-register
  reads and reaches the EKDOS `A>` bitmap; `sync/juku_top_fdc_prompt_check.sh`
  checks that evidence and can opt into the expensive rerun.
- `docs/juku-top-fdc-alignment.md` summarizes the current reset-to-prompt
  boundary against the C oracle.

## Commands

```sh
sync/fdc_check.sh
sync/ekdos_fdc_probe.py
sync/juku_top_fdc_prompt_check.sh
```

Checkpoint tools remain available for narrowing a regression, but their old
intermediate reports are not milestones now that uninterrupted reset-to-prompt
evidence exists.

## Remaining boundaries

- The model is a Juku boot/media shim, not a general WD1793 conformance model.
- Physical D93 INTRQ/DRQ, reset, clock, and D100 OE/T still require the targeted
  continuity checks in `docs/fdc-hardware-handoff.md`.
- D94 `.092` enable/output wiring and contents are unknown and block main-board
  design release.
- Adopt a larger upstream controller core only if a concrete required command
  or timing behavior exceeds this guarded scope; re-evaluate license and
  adapter cost at that time.
EOF

echo "FDC-CHECK: PASS"
echo "Wrote docs/fdc-readiness.md"
