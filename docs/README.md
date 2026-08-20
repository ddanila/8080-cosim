# Documentation map

The repository keeps current specifications and reproducible evidence, not a
chronological lab notebook. Superseded experiments remain available in Git
history.

## Living documents

- `../README.md` — project overview and honest current status.
- `../PLAN.md` — sole project-wide plan, priorities, milestones, and
  fabrication-release criteria.
- `automatic-completion-audit.md` — generated, fail-closed classification of
  every active unchecked item as evidence-, hardware-, procurement-, or
  authorization-gated.
- `crt-cvbs-simulation-plan.md` — subordinate execution plan for generating a
  loaded X7 voltage waveform, adapting the forked sample-domain receiver, and
  validating monitor lock before optional CRT presentation.
- `portable-c-host-plan.md` — subordinate implementation and qualification plan
  for a Linux-first portable C Janet/Fastboot/NetDisk/N4 host, an Open Watcom
  Windows 95 build, headless Wine-to-simulator automation, and eventual
  physical-COM validation.
- `portable-c-host-m0-contract.md` — frozen Python-era production modules,
  artifacts, wire vectors, and required C-host parity.
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
- `phi2ttl-d29-clock-route.md` — exact `.009` and owner-verified correction of
  the PHI2TTL branch through D30.3/D29.1 and the post-R35 D35.13 node; this
  supersedes the older reconstructed D29.1/MEMW attribution pending atomic
  replica migration.
- `8282-pinout-audit.md` — complete physical D58 DRAM read-latch pinout,
  power, and routed data-channel guard.
- `package-endpoint-coverage.md` — repository-wide guard against undeclared
  signal, control, or off-board package endpoints.

## Current evidence

Most reports are outputs of scripts or checks; a few are consolidated durable
findings. Every status applies only to the boundary named by the report.

- Physical model: `board-fidelity-gap-ledger.md`,
  `machine-deployment-status.md` and `machines/` (current CS00000/CS00014/
  CS00015/CS00024 locations, fitted-state profiles, and board-local open work),
  `cs00015-service-record.md` (Arvutimuuseum machine identity, D15 history,
  repaired D1, corrected D55 status, current Ekta4401/Jukuravi service ROM,
  and physical dual-network-drive validation),
  `jukuravi-d55-diagnostic-audit.md` (exact-sheet/8253 review, invalidation of
  the unclocked T15/T16/T31/T32 predicate, and clock-safe T34 fault matrix),
  `cs00024-t36-diagnosis.md` (complete T36 four-pattern 32 KiB physical proof,
  refresh interpretation, parser-margin separation, and D57 channel-2
  localization),
  `ras-resistor-bank.md` (photo-closed R49-R56 placement and values),
  `native-resistor-values.md` (25 literal sheet/photo values; no axial holds),
  `native-capacitor-values.md` (C7/C8/C99 literal sheet values with nine
  target holds), `native-semiconductors.md` (VD1/VD4 target `КД521В` bodies,
  the restored reset-diode footprint, VT1/VT2/VD3/VD5 native markings,
  transistor E-C-B package pinouts, and generated PCB pad/net guards),
  `master-oscillator-boundary.md`,
  `d40-d59-d92-d95-1mhz-route.md` (owner-continuity and exact-sheet closure of
  the D40.11/D59.5/D92.2/.3/D95.5/.6 1 MHz slot-clock route, including the
  guarded source/HDL/PCB correction and rejected tentative D96.6 join),
  `unmodeled-footprint-inventory.md`, `d93-pin40-photo-chase.md`,
  `owner-measurement-shortlist.md`.
- Programmable parts: `firmware-gap-ledger.md`,
  `d15-d16-firmware-lineage.md` (factory designations, exact archival EktaSoft
  3.7 pair identity, and the still-open physical-content boundary),
  `ektasoft-rombios-lineage.md` (serial-vs-RomBios-version identity of the
  vendored EktaSoft images, the two RomBios lines, and the homebrew #0043
  kinship/checksum analysis),
  `ekta37-netbios-notes.md` (byte-verified NetBios/Janet network-boot path in
  the adopted image: configurable D57-clocked 8251 line, odd-parity framing,
  TxEN-gated transmit; a round-trip-guarded annotated disassembly of the same
  image is maintained in `../disasm/`),
  `juku-serial-19200-investigation.md` (two-board receive-only 19,200 failure,
  exact D104/D11/D57 boundary analysis, and the ranked scope-first bench plan),
  `janet-fastboot.md` (stock-ROM-compatible 9600 stage plus retryable
  19200/8O1 bulk CP/M bootstrap, cosim evidence, command, and benchmark plan),
  `juku-rom-monitor-commands.md` (the decoded 15-command ROM monitor shared
  by every EktaSoft image and Monitor 3.3, the T/D/N-or-T boot dispatch
  tables, and the universal FF50h bootstrap vector),
  `ekta37-rom-map.md` (functional layout of the adopted 16 KiB image with
  sizes: console core 29%, NetBios 19%, disk 11%, font 10%, 1.7 KiB free),
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
  polarity guard), `d2-ready-cycle-analysis.md` (per-page wait classes and why
  the CS00015 A12 fetch/read premise is not physically expressible), and
  `re3-physical-dumps.md` (independent D8/D94 captures from two physical
  boards, reader wiring, and validated content truth).
- Fabrication package: `replica-manufacturing-readiness.md`,
  `replica-package-geometry-readiness.md`,
  `replica-fab-drc-disposition.md`, `replica-power-trace-readiness.md`,
  `replica-sourcing-readiness.md`,
  `replica-order-evidence-template.md` (vendor/order record), and
  `replica-first-article-record.md` (per-unit as-built configuration,
  instruments, acceptance, discrepancies, rework, and sign-off), plus
  `replica-candidate-parts-readiness.md` (guarded MK4564-12/FD1793B-01
  static compatibility with physical acceptance still held).
  Package readiness is not design release.
- Routed-board refresh: `routed-refresh-audit.md` — reproducible history from
  the stale candidate through the promoted exact-source zero-open route.
- Factory-wire routing: `factory-wire-route-fidelity.md` — distinguishes seven
  explicit wire/island splits from the three promoted-route copper substitutions
  still held on A9/A12/A13, and separately guards landing registration/fitting.
- Twin: `cosim-runtime-reference.md` (typed bus, focused interrupt-acknowledge,
  instruction-level, and uninterrupted top-level runtime guards),
  `juku-top-jbasic-verilator-probe.md` (uninterrupted HDL disk-BASIC `READY`),
  `fdc-readiness.md`, `d96-read-clock-readiness.md` (source-closed
  D96 wiring, undefined section-1 restart phase, and the exact section-2
  set-only contradiction),
  `video-slot-timing-audit.md`,
  `ir16-readiness.md` (datasheet-exact falling-edge LD/SH and active-high OC
  semantics for physical D41/D42/D43, while their board timing sources remain open),
  `kp14-readiness.md` (datasheet-exact inverting, three-state D48-D52 mux
  semantics with CPU-linear DRAM normalization; the adjacent D59.5/.6
  complementary E14-video/E13-CPU enable topology is driven by the guarded
  D40.11 1 MHz slot rail),
  `video-physical-probes.md` (executable controlled-stimulus probes for the
  source-proved D42/D43/D37 and D56/D34_SYNC contributors, with the shared-DRAM
  slot schedule and D34 signal input explicitly open),
  `video-pit-timing.md` (exact-ROM autonomous 15.625 kHz/313-line D54/D55/D56
  raster timing, independently matched to the 320x241 reference geometry),
  `d99-reconstruction-constraints.md` (grounded-clear constant section 1,
  D94-D1 access trigger, fitted RC timing, and five remote-pin boundaries),
  `video-readout-readiness.md`, `x7-output-stage-model.md` (guarded static
  emitter-follower transfer with a primary TI LS86 comparison driver plus an
  explicit exact-К555ЛП5 boundary),
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

Human-written summaries should describe outcomes and point to the command or
owning symbol. Keep generated totals, hashes, and source locations in their
machine-readable evidence instead of copying them into prose.

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
