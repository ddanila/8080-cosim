# Documentation map

Use the owning guide for current facts, limits and commands. This index keeps
navigation and status definitions; superseded experiments remain in Git history.

## Guides and plans

- [8080-cosim](../README.md)
- [Juku reconstruction plan](../PLAN.md)
- [Automatic completion audit](automatic-completion-audit.md)
- [Juku composite-video and CRT model contract](crt-cvbs-simulation-plan.md)
- [JukuNet C9 contract and physical result](network-rom-c9-plan.md)
- [JukuNet C10 video-release contract](network-rom-c10-plan.md)
- [C11 boot and NetDisk session recovery](c11-session-recovery.md)
- [C12 runtime console contract and physical qualification](c12-runtime-console.md)
- [Portable Juku host contract](portable-c-host-plan.md)
- [Frozen Python-era host baseline (M0)](portable-c-host-m0-contract.md)
- [Portable Juku host implementation](portable-c-host-implementation.md)
- [Portable C host M2 acceptance](portable-c-host-m2-acceptance.md)
- [Portable C host M2.1 physical acceptance](portable-c-host-m2.1-physical-acceptance.md)
- [Pocket8086 DOS host M2.2 desk acceptance](portable-c-host-m2.2-dos-acceptance.md)
- [Portable C host macOS physical check](portable-c-host-macos-physical-check.md)
- [Juku host configuration](jukuhost-config.md)
- [Windows Juku host user guide](windows-jukuhost-client.md)
- [Windows host implementation and qualification](windows-jukuhost-client-implementation.md)
- [Windows host Wine protocol acceptance](windows-jukuhost-client-wine-acceptance.md)
- [Windows 95 guest acceptance](windows-jukuhost-client-win95-acceptance.md)
- [CRT decoder fork baseline](crt-decoder-baseline.md)
- [Architecture and verification boundaries](architecture.md)
- [Development and verification workflow](development-workflow.md)
- [Project invariant: one evidence-rooted machine](vision.md)
- [Juku E5104 behavioral hardware map](hardware-map.md)
- [July 2026 photo registration](photo-registration.md)
- [Git LFS policy](git-lfs-policy.md)
- [Source coverage audit](source-coverage-audit.md)
- [Factory-drawing legibility audit](factory-drawing-legibility.md)
- [`ДГШ5.109.009 Э3` reviewed transcription and divergence audit](../ref/schematics/dgsh5-109-009-e3-notes.md)
- [D30 section-B clock and output connections](d30-section-b-scan-chase.md)
- [8286 transceiver pinout audit](8286-pinout-audit.md)
- [PHI2TTL and D29 command-buffer route](phi2ttl-d29-clock-route.md)
- [D58 8282 latch pinout audit](8282-pinout-audit.md)
- [Package endpoint coverage](package-endpoint-coverage.md)

## Evidence by area

Each result applies only to the inputs and scope named by its report.

### Physical model

- [Board fidelity gap ledger](board-fidelity-gap-ledger.md)
- [Juku machine deployment status](machine-deployment-status.md)
- [CS00000 service record](cs00000-service-record.md)
- [Diymore FT232BL adapter investigation](ft232bl-adapter-investigation.md)
- [Arvutimuuseum CS00015 service record](cs00015-service-record.md)
- [CS00024 construction-variant observations](cs00024-construction-variant.md)
- [Jukuravi D55 diagnostic audit](jukuravi-d55-diagnostic-audit.md)
- [CS00024 T36 desk diagnosis](cs00024-t36-diagnosis.md)
- [R49-R56 RAS resistor bank](ras-resistor-bank.md)
- [Native schematic resistor values](native-resistor-values.md)
- [Native schematic capacitor values](native-capacitor-values.md)
- [Native semiconductor designations and pinouts](native-semiconductors.md)
- [Master oscillator boundary](master-oscillator-boundary.md)
- [D40/D59/D92/D95 1 MHz route review](d40-d59-d92-d95-1mhz-route.md)
- [Unmodeled footprint inventory](unmodeled-footprint-inventory.md)
- [D93 pin-40 power-trace chase](d93-pin40-photo-chase.md)
- [FDC hardware handoff](fdc-hardware-handoff.md)
- [D93 reset and static-pin model boundary](../ref/schematics/fdc-controller-static-map.md)
- [Owner measurement shortlist](owner-measurement-shortlist.md)
- [Owner-measured facts](owner-measured-facts.md) — check before requesting measurements
- [Next bench checklist](next-bench-session-checklist.md)
- [Machine profiles](machines/README.md)

### Programmable parts

- [Firmware gap ledger](firmware-gap-ledger.md)
- [D15/D16 firmware lineage](d15-d16-firmware-lineage.md)
- [EktaSoft serial/RomBios lineage notes](ektasoft-rombios-lineage.md)
- [ekta37 NetBios/Janet boot-path notes](ekta37-netbios-notes.md)
- [Juku 19,200 receive investigation](juku-serial-19200-investigation.md)
- [Stock-ROM bootstrap and recovery](janet-fastboot.md)
- [Juku ROM monitor command reference](juku-rom-monitor-commands.md)
- [ekta37 ROM layout map](ekta37-rom-map.md)
- [D2 .037 reconstruction constraints](d2-reconstruction-constraints.md)
- [D94 .092 reconstruction constraints](d94-reconstruction-constraints.md)
- [D101 first-half reconstruction constraints](d101-reconstruction-constraints.md)
- [Reconstructed PROM fallback images](reconstructed-prom-fallbacks.md)
- [Physical D6 `.038` decode](d6-physical-decode.md)
- [D8 `.039` physical ROM-pager decode](d8-physical-decode.md)
- [D6 input continuity correction](d6-input-continuity.md)
- [D6 runnable-path diagnostic](d6-runtime-path-diagnostic.md)
- [D6 firmware mode coverage](d6-firmware-mode-coverage.md)
- [D15/D16 EPROM programming images](eprom-programming-images.md)
- [D2 physical dump and local continuity](d2-physical-dump-and-continuity.md)
- [Physical D2 `.037` truth](d2-physical-truth.md)
- [D2 READY polarity simulation check](d2-ready-path-check.md)
- [D2 READY wait classes and the A12 fetch/read premise](d2-ready-cycle-analysis.md)
- [D8/D94 physical RE3 dumps](re3-physical-dumps.md)

### Fabrication package

- [Replica release evidence packet](replica-release-evidence-package.md)
- [Replica manufacturing readiness](replica-manufacturing-readiness.md)
- [Replica package geometry readiness](replica-package-geometry-readiness.md)
- [Replica fab DRC disposition](replica-fab-drc-disposition.md)
- [Replica power-trace readiness](replica-power-trace-readiness.md)
- [Replica sourcing readiness](replica-sourcing-readiness.md)
- [Replica order evidence template](replica-order-evidence-template.md)
- [Replica first-article acceptance record](replica-first-article-record.md)
- [Replica candidate-part readiness](replica-candidate-parts-readiness.md)

### Routing

- [Routed PCB refresh audit](routed-refresh-audit.md)
- [Factory insulated-wire route fidelity](factory-wire-route-fidelity.md)

### Twin

- [Cosim runtime and CPU-bus reference](cosim-runtime-reference.md)
- [juku_top uninterrupted JBASIC READY probe](juku-top-jbasic-verilator-probe.md)
- [FDC readiness](fdc-readiness.md)
- [D96 FDC read-clock readiness](d96-read-clock-readiness.md)
- [Video slot timing audit](video-slot-timing-audit.md)
- [К555ИР16 primitive readiness](ir16-readiness.md)
- [К555КП14 / КР531КП14 primitive readiness](kp14-readiness.md)
- [Physical video contributor probes](video-physical-probes.md)
- [ROM-programmed Juku video timing](video-pit-timing.md)
- [D99 trigger and timing reconstruction constraints](d99-reconstruction-constraints.md)
- [Video readout readiness](video-readout-readiness.md)
- [VIDEO_OUT output-stage static model](x7-output-stage-model.md)
- [Serial handoff](serial-handoff.md)
- [Beeper readiness](beeper-readiness.md)
- [Factory keyboard matrix — `ДГШ5.104.015 Э3`](factory-keyboard-matrix.md)

### Media/software

- [Vendored disk catalog](vendored-disk-catalog.md)
- [BASIC disk extraction](basic-disk-extraction.md)
- [Monitor cartridge BASIC boundary](cartridge-basic-boundary.md)
- [Cartridge BASIC firmware-lineage audit](cartridge-basic-firmware-lineage.md)
- [Monitor 2.2 reconstruction audit](jmon22-reconstruction.md)

## Regenerating reports

Report writers live under `scripts/`, `kicad/` and `sync/`. Use the command named
by the report. The [regeneration guide](../sync/README.md#regenerating-reports)
defines the selected `regen_all.sh` sets and its index-relative `--check` behavior.
Path-selected CI jobs cover their configured reports; a green job does not
establish freshness or runtime coverage for every document.

Keep detailed measurements, hashes and source locations in the owning evidence.
Human-written summaries should link there and state the relevant boundary.

## Reference guides

- [Juku E5101/E5104 ROM set (vendored)](../roms/README.md)
- [Juku disk images](../media/disks/README.md)
- [Juku system binaries](../media/system/README.md)
- [Juku processor-module factory drawings](../ref/schematics/README.md)
- [Baltijets Juku E5104 technical documentation](../ref/baltijets-tech-docs/README.md)
- [EKDOS source references](../ref/ekdos-source/README.md)
- [WD1772 / VG93 reverse-engineering reference](../ref/wd1772-vg93/README.md)
- [ДГШ5.109.009 СБ extraction audit](assembly-drawing-extraction.md)
- [Official .009 IC census](official-009-ic-census.md)
- [Factory modification disposition](factory-modification-disposition.md)

## Status vocabulary

- **PASS/READY** means the specifically named check passed for its recorded
  inputs and scope. Recheck changed inputs before treating that result as current.
- **PACKAGE VERIFIED** means the named report's package checks passed. The
  upload runbook checks files, ZIP metadata, checksums and evidence markers;
  it does not rerun geometry checks or authorize design release.
- **DESIGN HOLD** means fabrication is not authorized even if the package is
  coherent.
- **PENDING/BLOCKED** means evidence or an external action is still required.

Avoid global phrases such as “manufacturing ready” unless every design-release
criterion in `PLAN.md` is satisfied.
