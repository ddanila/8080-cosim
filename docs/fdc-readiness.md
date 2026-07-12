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
- Physical D93 INTRQ/DRQ, reset, D100 OE/T, and the upstream D99 one-shot
  timing network still require the targeted continuity checks in
  `docs/fdc-hardware-handoff.md`; D99.13 to D93.24 CLK is now photo-proved.
- D94 `.092` pins 1-3 are now wired to the three accepted local FDC controls;
  pin 15, outputs D3-D7, and PROM contents remain unknown and block main-board
  design release.
- Adopt a larger upstream controller core only if a concrete required command
  or timing behavior exceeds this guarded scope; re-evaluate license and
  adapter cost at that time.
