#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "== C disk/FDC and ekta37 ROMBIOS write-loop check =="
sync/juk_disk_check.sh

echo "== HDL WD1793 synthetic-sector check =="
iverilog -g2012 -o "$TMP/fdc_1793_tb" hdl/vendor/vm80a.v hdl/devices.v hdl/sim/fdc_1793_tb.v
out=$(vvp "$TMP/fdc_1793_tb")
echo "$out"
grep -q "FDC-1793: PASS" <<<"$out" || { echo "FDC-CHECK: FAIL"; exit 1; }

echo "== HDL WD1793 vendored-media check =="
disk_out=$(vvp "$TMP/fdc_1793_tb" +disk=media/disks/JUKU1.CPM +disk_heads=2 +expect_disk)
echo "$disk_out"
grep -q "FDC-1793: PASS" <<<"$disk_out" || { echo "FDC-CHECK: FAIL"; exit 1; }

echo "== HDL WD1793 writable-copy write-sector check =="
cp media/disks/JUKU1.CPM "$TMP/JUKU1-writable.CPM"
writable_out=$(vvp "$TMP/fdc_1793_tb" \
  +disk="$TMP/JUKU1-writable.CPM" +disk_heads=2 +disk_writable \
  +expect_disk +expect_writable)
echo "$writable_out"
grep -q "FDC-1793: PASS" <<<"$writable_out" || { echo "FDC-CHECK: FAIL"; exit 1; }

echo "== juku_top decoded peripheral bus check =="
sync/juku_top_periph_bus_check.sh

cat > docs/fdc-readiness.md <<'EOF'
# FDC readiness

Status: **BOOT-SCOPED HDL FDC READY**

`sync/fdc_check.sh` guards the FDC behavior needed by the proven Juku boot
path. It does not claim a complete WD1793/VG93 implementation or complete
physical D93/D94 wiring.

## Passing scope

- Restore, seek, step, step-in, step-out, read-sector, write-sector,
  track/sector/data registers, BUSY/DRQ/INTRQ, side select, and
  motor-not-ready behavior.
- A 512-byte synthetic sector transfer and bytes from vendored
  `media/disks/JUKU1.CPM`.
- The exact ROMBIOS `0xA0/0xA2` write-sector path writes 512 bytes to an
  explicitly writable temporary image and reads them back byte-for-byte.
  Repository media stays read-only by default; HDL needs `+disk_writable`,
  and cosim needs `JUKU_DISK_WRITABLE=1`, on a caller-provided copy.
- The C guard executes the exact `ekta37` ROM bytes at `0xE69F..0xE6C1` on
  the 8080 core, observes command `0xA2` plus 512 accepted data writes, checks
  the ROM-written zero `ERRC`, and verifies persisted sector readback. It stops
  before the separate monitor-service epilogue at `0xE6C2`.
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

## Write-path provenance

- Vendored `EKDOS30.ASM` defines `DKWR=0x12` and passes it to the ROMBIOS
  `RWFLOPPY` entry at `0xFF59`.
- Exact `roms/ekta37.bin` disassembly branches on request `0x12` at `0xE67C`,
  selects WD1793 command `0xA0` or `0xA2` at `0xE69F/0xE6A4`, writes the
  command to port `0x1C` at `0xE6AB`, and loops 512 bytes from memory to the
  data register at port `0x1F` from `0xE6AF`.
- `tests/rombios_fdc_write_test.c` executes that command/data loop directly
  from the vendored ROM instead of duplicating it as test-side port writes.
- The implementation intentionally stops at that firmware-proved single-sector
  contract; it does not claim general WD1793 write-track or timing conformance.

## Commands

```sh
sync/juk_disk_check.sh
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
- D94 `.092` uses the validated physical table; direct continuity closes its
  enable to D93.CS, D1 to ground, D2 to D93.RE, D3 to D93.WE, and D4 to the
  D93 back-bias/NC socket contact. The runnable model consumes the physical
  D2/D3 strobes under explicit simulation-only enable, A3, and A4 fits. Their
  upstream physical sources plus D0/D5-D7 branches still block board release.
- Adopt a larger upstream controller core only if a concrete required command
  or timing behavior exceeds this guarded scope; re-evaluate license and
  adapter cost at that time.
EOF

echo "FDC-CHECK: PASS"
echo "Wrote docs/fdc-readiness.md"
