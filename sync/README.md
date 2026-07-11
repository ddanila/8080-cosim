# Verification entry points

`sync/` contains the LVS comparison, fast behavioral regressions, and focused
subsystem/deep diagnostics. Reports under `docs/` are evidence outputs, not
independent specifications.

## Connectivity

```sh
sync/check.sh
```

The script regenerates the KiCad schematic from `kicad/juku.board.json`,
elaborates `hdl/juku_top.v` with Yosys, and compares mapped endpoint
partitions. It uses a real KiCad netlist when compatible `kicad-cli` is
available and the board JSON directly otherwise.

Current scope: 99 mapped instances and 234 compared nets. Placement-only
footprints, unnetted pins, analog passives, and explicit simulation-only ports
are outside this result.

Key files:

- `lvs.py` — comparison and diagnostics.
- `netlist_from_kicad.py`, `netlist_from_yosys.py`,
  `netlist_from_board.py` — normalizers.
- `map.json` — refdes/instance and physical-pin/logical-port mapping.
- `provenance.py` — source annotation summary for `board.json`.

## Fast behavioral checks

```sh
sync/boot_check.sh
sync/cosim_check.sh
sync/juk_disk_check.sh
sync/fdc_check.sh
sync/video_timing_check.sh
sync/video_readout_check.sh
sync/beeper_check.sh
sync/serial_check.sh
sync/basic_cart_check.sh
```

These cover the real-ROM boot/framebuffer path, structural/oracle agreement,
raw disk geometry, the bounded WD1793 boot subset, raster/serializer behavior,
beeper and USART slices, and the BASIC cartridge window.

## Current user-visible oracles

- `ekdos_fdc_probe.py` — ROMBIOS `TDD` to EKDOS `A>` in the C oracle.
- `juku_top_fdc_prompt_check.sh` — committed uninterrupted HDL EKDOS prompt
  evidence; set its documented deep-rerun option to refresh the long trace.
- `ekdos_jbasic_command_probe.py` and `juku_top_jbasic_prompt_check.sh` — disk
  BASIC command and uninterrupted HDL `READY` evidence.
- `jmon33_ready_probe.py`, `jmon33_command_probe.py`, and
  `jmon33_hdl_probe.sh` — Monitor 3.3 reference and structural checks.
- `jmon33_checkpoint_deep_check.sh` — long checkpoint-resumed cursor/A/B/FDC-T
  checks, kept out of push CI because of runtime. Its superseded cursor
  intermediate is written to a temporary file.

Checkpoint load/resume tools remain useful for narrowing regressions, but their
old intermediate report files are not project milestones. The uninterrupted
reset-to-prompt reports are the stronger evidence where both exist.

## Reference and generated-evidence checks

- `reference_artifact_check.sh` verifies checksums for vendored factory,
  firmware, media, and WD1772/VG93 references.
- Scripts under `scripts/report_*.py` regenerate constraint and boundary
  reports used by CI.
- `scripts/check_documentation_consistency.py` ensures user-facing status and
  package hashes do not contradict the active design blockers.

## Limits

The FDC, USART, PIT/PPI/PIC, memory timing, and video helpers are scoped to
guarded Juku behavior. They are not complete drop-in models of every original
chip. Most importantly, behavioral success cannot supply the missing D2/D94
wiring and PROM truth, D30 section B, or the functional connectivity of the 9
FDC-support ICs; those are fabrication-release blockers tracked in `PLAN.md`.
