# Documentation map

The repository keeps current specifications and reproducible evidence, not a
chronological lab notebook. Superseded experiments remain available in Git
history.

## Living documents

- `../README.md` — project overview and honest current status.
- `../PLAN.md` — sole project-wide plan, priorities, milestones, and
  fabrication-release criteria.
- `crt-cvbs-simulation-plan.md` — subordinate execution plan for generating a
  loaded X7 voltage waveform, adapting the forked sample-domain receiver, and
  validating monitor lock before optional CRT presentation.
- `crt-decoder-baseline.md` — guarded clean-checkout build/CTest/synthetic-NTSC
  baseline plus fork-owned provenance, fixture policy, green Linux CI, and the
  pinned generic float32 WP1 and profile-driven receiver WP2 follow-ups.
- `architecture.md` — data flow and scope of each verification layer.
- `vision.md` — project invariant and source-of-truth policy.
- `hardware-map.md` — concise software-visible machine map and physical
  boundary.
- `photo-registration.md` — current photo-evidence workflow and accepted paths.
- `git-lfs-policy.md` — immutable original-photo policy, selective CI fetches,
  cache maintenance, and usage monitoring.
- `source-coverage-audit.md` — adopted external evidence and remaining source
  gaps.
- `factory-drawing-legibility.md` — complete overview/detail coverage audit
  and re-shoot disposition for the 2026-07-18 recovered drawing batch.
- `../ref/schematics/dgsh5-109-009-e3-notes.md` — reviewed, generated
  three-sheet `.009` electrical transcription and `.006` divergence audit.
- `d30-section-b-scan-chase.md` — exhausted sheet-1 trace audit for the two
  remaining D30 section-B conductors and the exact continuity closure required.
- `8286-pinout-audit.md` — physical D4/D107/D23-D25/D29/D100 channel pinouts
  and routed high-address/command permutation guard.
- `8282-pinout-audit.md` — complete physical D58 DRAM read-latch pinout,
  power, and routed data-channel guard.
- `package-endpoint-coverage.md` — repository-wide guard against undeclared
  signal, control, or off-board package endpoints.

## Current evidence

Most reports are outputs of scripts or checks; a few are consolidated durable
findings. Every status applies only to the boundary named by the report.

- Physical model: `board-fidelity-gap-ledger.md`,
  `ras-resistor-bank.md` (photo-closed R49-R56 placement and values),
  `native-resistor-values.md` (25 literal sheet/photo values; no axial holds),
  `native-capacitor-values.md` (C7/C8/C99 literal sheet values with nine
  target holds), `native-semiconductors.md` (VD1/VD4 target `КД521В` bodies,
  the restored reset-diode footprint, VT1/VT2/VD3/VD5 native markings,
  transistor E-C-B package pinouts, and generated PCB pad/net guards),
  `master-oscillator-boundary.md`,
  `unmodeled-footprint-inventory.md`, `d93-pin40-photo-chase.md`,
  `owner-measurement-shortlist.md`.
- Programmable parts: `firmware-gap-ledger.md`,
  `d15-d16-firmware-lineage.md` (factory designations, exact archival EktaSoft
  3.7 pair identity, and the still-open physical-content boundary),
  `d2-reconstruction-constraints.md`, `d94-reconstruction-constraints.md`,
  `d101-reconstruction-constraints.md` (datasheet-exact first-half select cases,
  D02 ladder, conditional D0-to-`/OE0` test, and four measured-pin boundaries),
  `reconstructed-prom-fallbacks.md`, `d6-physical-decode.md`,
  `d8-physical-decode.md` (exhaustive `.039` socket-select equations),
  `d6-input-continuity.md` (measured `/PC1`, `/PC0`, and A7 I/O-cycle routes),
  `d6-runtime-path-diagnostic.md` (all-mode B37A RAM-output boundary),
  `d6-firmware-mode-coverage.md`,
  `eprom-programming-images.md`, and
  `d2-physical-dump-and-continuity.md` (validated owner dump and synchronized
  connectivity adoption), `d2-physical-truth.md` (exact READY truth
  classification), `d2-ready-path-check.md` (executed open-collector D2-to-D30
  polarity guard), and `re3-physical-dumps.md` (independent D8/D94 captures
  from two physical boards, reader wiring, and validated content truth).
- Fabrication package: `replica-manufacturing-readiness.md`,
  `replica-package-geometry-readiness.md`,
  `replica-fab-drc-disposition.md`, and `replica-power-trace-readiness.md`.
  Package readiness is not design release.
- Routed-board refresh: `routed-refresh-audit.md` — reproducible history from
  the stale candidate through the promoted exact-source zero-open route.
- Factory-wire routing: `factory-wire-route-fidelity.md` — distinguishes seven
  explicit wire/island splits from the three promoted-route copper substitutions
  still held on A9/A12/A13, and separately guards landing registration/fitting.
- Twin: `fdc-readiness.md`, `d96-read-clock-readiness.md` (source-closed
  D96 wiring, undefined section-1 restart phase, and the exact section-2
  set-only contradiction),
  `video-slot-timing-audit.md`,
  `video-physical-probes.md` (executable controlled-stimulus probes for the
  source-proved D42/D43/D37 and D56/D34_SYNC contributors, with the shared-DRAM
  slot schedule and D34 signal input explicitly open),
  `video-pit-timing.md` (exact-ROM autonomous 15.625 kHz/313-line D54/D55/D56
  raster timing, independently matched to the 320x241 reference geometry),
  `d99-reconstruction-constraints.md` (grounded-clear constant section 1,
  D94-D1 access trigger, fitted RC timing, and five remote-pin boundaries),
  `video-readout-readiness.md`, `x7-output-stage-model.md` (guarded static
  emitter-follower transfer plus an explicit К555ЛП5 drive-current boundary),
  `serial-handoff.md`, and
  `beeper-readiness.md`, plus `factory-keyboard-matrix.md` (the complete
  `.104.015` matrix/X1 transcription and exact cosim/HDL coordinate contract).
- Media/software: `vendored-disk-catalog.md`, `basic-disk-extraction.md`, and
  `cartridge-basic-boundary.md` and the generated
  `cartridge-basic-firmware-lineage.md` and `jmon22-reconstruction.md`, plus
  the current disk-BASIC/Monitor guards.

The producing scripts live under `scripts/`, `kicad/`, or `sync/`. CI reruns
the reports that guard active boundaries and fails if their committed output
changes.

## Reference-area READMEs

Provenance for vendored inputs belongs beside the inputs:

- `../roms/README.md`
- `../media/disks/README.md`
- `../media/system/README.md`
- `../ref/schematics/README.md`
- `../ref/baltijets-tech-docs/README.md`
- `../ref/ekdos-source/README.md`
- `../ref/wd1772-vg93/README.md`
- `assembly-drawing-extraction.md` — guarded extraction and checksums for the photographed `ДГШ5.109.009 СБ` sheet 1 and the ДУБЛИКАТ scan of its sheets 2-6 (wire table).
- `official-009-ic-census.md` — complete two-page `ДГШ5.109.009 ПЭЗ` IC transcription, owner-board substitutions, and board-model identity guard.
- `factory-modification-disposition.md` — photo-closed D15 cut, partial D14 ground-link closure, registered D11 four-landing field, and the remaining factory Вид В holds.

## Status vocabulary

- **PASS/READY** means the specifically named check passes.
- **PACKAGE VERIFIED** means files, geometry, and checksums are coherent.
- **DESIGN HOLD** means fabrication is not authorized even if the package is
  coherent.
- **PENDING/BLOCKED** means evidence or an external action is still required.

Avoid global phrases such as “manufacturing ready” unless every design-release
criterion in `PLAN.md` is satisfied.
