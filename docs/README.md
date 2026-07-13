# Documentation map

The repository keeps current specifications and reproducible evidence, not a
chronological lab notebook. Superseded experiments remain available in Git
history.

## Living documents

- `../README.md` — project overview and honest current status.
- `../PLAN.md` — sole plan, priorities, milestones, and fabrication-release
  criteria.
- `architecture.md` — data flow and scope of each verification layer.
- `vision.md` — project invariant and source-of-truth policy.
- `hardware-map.md` — concise software-visible machine map and physical
  boundary.
- `photo-registration.md` — current photo-evidence workflow and accepted paths.
- `source-coverage-audit.md` — adopted external evidence and remaining source
  gaps.
- `d30-section-b-scan-chase.md` — exhausted sheet-1 trace audit for the two
  remaining D30 section-B conductors and the exact continuity closure required.
- `8286-pinout-audit.md` — physical D4/D107/D23-D25/D29 channel pinouts and
  routed high-address/command permutation guard.

## Current evidence

Most reports are outputs of scripts or checks; a few are consolidated durable
findings. Every status applies only to the boundary named by the report.

- Physical model: `board-fidelity-gap-ledger.md`,
  `master-oscillator-boundary.md`,
  `unmodeled-footprint-inventory.md`, `d93-pin40-photo-chase.md`,
  `owner-measurement-shortlist.md`.
- Programmable parts: `firmware-gap-ledger.md`,
  `d2-reconstruction-constraints.md`, `d94-reconstruction-constraints.md`,
  `reconstructed-prom-fallbacks.md`, `d6-physical-decode.md`,
  `d6-firmware-mode-coverage.md` (physical PC4..PC2 versus emulator PC1..PC0),
  `eprom-programming-images.md`, and
  `d2-physical-dump-and-continuity.md` (validated owner dump and synchronized
  connectivity adoption), and `d2-physical-truth.md` (exact READY truth
  classification).
- Fabrication package: `replica-manufacturing-readiness.md`,
  `replica-package-geometry-readiness.md`,
  `replica-fab-drc-disposition.md`, and `replica-power-trace-readiness.md`.
  Package readiness is not design release.
- Twin: `fdc-readiness.md`, `video-slot-timing-audit.md`,
  `video-readout-readiness.md`, `serial-handoff.md`, and
  `beeper-readiness.md`.
- Media/software: `vendored-disk-catalog.md`, `basic-disk-extraction.md`, and
  `cartridge-basic-boundary.md`, plus the current disk-BASIC/Monitor guards.

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
- `factory-modification-disposition.md` — pin-mapping hold for factory Вид В cuts/patches at D56/D15/D14/D11.

## Status vocabulary

- **PASS/READY** means the specifically named check passes.
- **PACKAGE VERIFIED** means files, geometry, and checksums are coherent.
- **DESIGN HOLD** means fabrication is not authorized even if the package is
  coherent.
- **PENDING/BLOCKED** means evidence or an external action is still required.

Avoid global phrases such as “manufacturing ready” unless every design-release
criterion in `PLAN.md` is satisfied.
