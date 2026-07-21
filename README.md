# 8080-cosim

Reconstruction of the Soviet/Estonian Juku E5104 processor board as both a
physical PCB and a runnable, headless digital model. The project’s distinctive
piece is an LVS-style check that compares the structural Verilog connectivity
with the machine-readable board model.

## Current result

- The C emulator and the structural `juku_top` model boot the real Juku ROM,
  render the same framebuffer, accept keyboard input, boot EKDOS from the
  vendored disk images, and reach disk BASIC `READY`. The deep value-level
  guard `sync/cosim_check.sh` compares `juku_top`'s memory reads byte-for-byte
  against the C emulator (`cosim`); the default 130,000-read trace now reaches
  `CTRACE-END` with no address or data divergence, including the BIOS RAM test.
- `sync/check.sh` currently compares 117 mapped instances and 309 nets with no
  KiCad/HDL mismatch.
- The promoted routed main-board artifact exactly matches the live
  321-footprint/2,434-pad source and contains 29,780 copper items across 412
  nets. Stable KiCad 9.0.8 reports zero opens, zero electrical blockers, and
  zero dangling tracks or vias. Its Gerber/drill package is machine-verified,
  but remains under the functional design hold and must not be uploaded or
  ordered. Current deterministic upload ZIP SHA256:
  `cada377a9b9f5626c4417432b962145bdd6e3f67a7abe4fa440f7ccabf8d1631`.
  Exact topology evidence is retained in
  `ref/routing/zero-open-promoted-topology.json`; the exact package snapshot is
  `ref/routing/zero-open-fabrication-package.json`, and fabrication/release
  gates are summarized in `docs/replica-manufacturing-readiness.md`.
  The separately preserved historical candidate still has 265 pad-net mismatches and 224 moved
  pads against the source; it is audit history, not the promoted board.
- The main board is **not released for fabrication**. Validated physical D2
  `.037`, D6 `.038`, D8 `.039`, and D94 `.092` tables are preserved from
  repeated reads (with D8/D94 provenance aliases counted only once); the measured D2/D30/D105 and
  D6/D13 continuity is adopted in the source model, HDL, and promoted route.
  D94 content truth and all five A0-A4 sources are owner-closed. D1-D3 reach
  D99/D93 with their measured pull-ups, while D4-D7 are owner/drawing-closed
  no-connects. The remaining D94 boundaries are the upstream source beyond the
  local pin15/D93.3 enable conductor and whether D0/pin1 has a hidden load
  beyond R8; the former BA11-BA15 input assignment was an unproved scaffold
  analogy and is retired. There are 3 official FDC-support ICs whose
  functional pin closure is still incomplete.
  Recovered sheet 3 closes D106 completely: its R78 preset pull-up, RAW READ
  load, D95 recovery clock, grounded clear, Q3 output, and five no-connects are
  now source-modeled and LVS-visible; R78 value/placement stays unresolved.
  Sheet 3 also closes D96's section-1 divide-by-two read-clock wiring. Primary
  device truth shows that WREQ asserts `/CLR1` and `/PRE1` together, producing
  Q1=/Q1=high and leaving restart phase undefined; `/Q` feedback still divides
  after release. A full-resolution reread restores D96 section 2 plus D28
  sections 5/6 and R93/R95 as the local DRQ/INTRQ path; D96.13 is drawn unused
  and the separately proved pin-8 test landing is retained. Primary SN74LS74A
  truth exposes the shared `/PRE2`/D2 wiring as set-only without a real pin13
  clear source. The copper is structural and LVS-visible, while D96.9/.11 and
  the functionally contradictory pin13 disposition remain verification gates.
  The source-closed D97/D102 delay cascade and D101 write-precompensation mux
  are also now structural and LVS-visible. Their recovered digital conductors
  are proved without assigning analog timing to the still-incomplete C16/C19
  markings or hiding D101.1/.3/.5/.6 behind simulation defaults.
  Source-closed D28 and D98 are likewise structural and LVS-visible, including
  all six D28 open-collector inverters, the five used D98 buffers, and the
  exact-revision omission of D98 buffer pair 4.
  The exact-revision sheet makes D97.13, D98.9/.10, and D102.4 intentional
  no-connects, leaving D96, D99, and D101 with open support-device functional pins.
  The measured D105 DBIN/H and MEMW paths are modeled in the source PCB and HDL;
  D6's validated physical table drives runnable memory selection directly and
  its chip-removed separate ROM/RAM outputs stay LVS-visible; the old functional
  decoder remains only as a non-LVS diagnostic comparison.
  A focused diagnostic now proves all eight physical modes leave D6.9 high at
  the `B37A` RAM-output failure, excluding mode selection and V1/V2 as causes
  across every raw A7..A5 row. Chip-removed continuity proves D6.12->D8.15
  and isolates D6.11 from D6.12, invalidating the earlier installed-PROM join.
  The report
  records the retired reader-order fault and the measurements that closed it;
  the promoted route carries the corrected topology with exact source parity.
  D30 READY sections A/B are modeled; owner continuity closes pin 8 to D29.7
  and pin 11 to the D105.2/D13.4/D11.20 clock conductor. Native sheet 1 plus
  the `.009` drawing and owner photo now close `H` as X1.107B/-BLOCK with its
  R1 2 kΩ pull-up. D7's physical SYNC/feedback strobe is
  preserved structurally while simulation uses a zero-delay-safe I/O activity oracle.
  In total, 45 modeled nets retain source-risk annotations requiring
  evidence or explicit redesign.
  See [PLAN.md](PLAN.md).

That last distinction matters: a clean DRC and a green LVS prove only the
connectivity represented in those checks. They do not prove omitted pins,
unmodeled footprints, reconstructed PROM contents, or analog/timing assumptions.

## Evidence and source hierarchy

1. Factory drawings, board photographs, dumps, and owner measurements under
   `ref/` are the historical evidence.
2. `kicad/juku.board.json` is the current machine-readable connectivity model.
3. `kicad/juku.kicad_sch`, the PCB files, and fabrication outputs are derived
   from or checked against that model.
4. `hdl/juku_top.v` is independently maintained structural Verilog and is
   checked against the modeled connectivity by `sync/`.
5. `cosim/` and the current upstream MAME Juku driver are behavioral oracles;
   they are not substitutes for missing physical wiring evidence.

## Board previews

These renders show the current routed engineering artifact, not a fabrication
release.

| 3D | 2D |
| --- | --- |
| ![3D top](renders/board_3d_top.png) | ![component side](renders/board_2d_front.png) |
| ![3D perspective](renders/board_3d_persp.png) | ![solder side](renders/board_2d_back.png) |

## Useful entry points

- [PLAN.md](PLAN.md) — remaining work and release criteria.
- [docs/README.md](docs/README.md) — documentation map and generated-report
  policy.
- [docs/development-workflow.md](docs/development-workflow.md) — canonical
  branch, intermediate commit, and direct-push policy.
- [docs/git-lfs-policy.md](docs/git-lfs-policy.md) — preservation and
  bandwidth policy for original reference photographs.
- [docs/architecture.md](docs/architecture.md) — model boundaries and data flow.
- [docs/source-coverage-audit.md](docs/source-coverage-audit.md) — adopted
  external evidence and remaining source gaps.
- [sync/README.md](sync/README.md) — verification commands.
- [docs/replica-manufacturing-readiness.md](docs/replica-manufacturing-readiness.md)
  — fabrication-package integrity and the current design hold.

## Quick checks

```sh
sync/check.sh
sync/boot_check.sh
sync/cosim_check.sh
python3 scripts/check_documentation_consistency.py
```

The long reset-to-EKDOS/BASIC and Monitor 3.3 diagnostics are intentionally
separate from the fast default checks; `sync/README.md` identifies their entry
points.

## Layout

| Path | Purpose |
| --- | --- |
| `ref/` | Factory drawings, photographs, firmware evidence, and external references |
| `kicad/` | Board model, generated schematic, source/routed PCB, zero-open audit candidate, and fabrication tooling |
| `hdl/` | Structural runnable model and device behavior |
| `cosim/` | Independent software emulator/oracle |
| `sync/` | LVS, behavioral comparisons, and subsystem guards |
| `roms/`, `media/` | Vendored preservation inputs with provenance/checksums |
| `docs/` | Current specifications and generated evidence reports |
| `spinoffs/minimal-vga/` | Independent VJUGA experiment; not on the replica critical path |
