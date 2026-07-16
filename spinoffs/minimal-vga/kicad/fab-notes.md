# VJUGA Rev A fabrication notes

Status: **PACKAGE BASELINE EXISTS / DESIGN HOLD**.

The current Rev A board is a routed physical experiment generated from
`rev-a-physical.board.json`. KiCad reports zero error-level DRC violations and
zero unconnected items. Those checks establish file coherence for modeled
nets; they do not prove the proposed computer will boot or that the design is
safe to order.

## Current physical baseline

- 200 x 200 mm, four copper layers: `F.Cu`, `In1.Cu`, `In2.Cu`, and `B.Cu`.
- 119 footprints, 135 PCB nets, and 2,525 tracks in the current checked board.
- Parts and functional-block borders are aligned to a 0.2" (5.08 mm) grid;
  decoupling caps sit at each chip's short side. In1.Cu is a filled GND plane and
  In2.Cu a filled VCC plane; the two board layers carry the signal routing.
- Four corner mounting holes and two-sided assembly/silkscreen review output.
- Factory-assembly exports are drafts. Socketed ICs are intended for owner
  insertion; factory files primarily describe sockets, passives, connectors,
  protection, and diagnostics.

The stackup (In1.Cu GND / In2.Cu VCC inner planes, F.Cu/B.Cu signals) is an
experiment, not a production recommendation. Return paths, voltage drop,
transient current, and actual vendor stackup require human review before any
release. (FreeRouting receives a deliberately zone-free board; the source-model
GND/VCC plane zones are restored and filled after SES import.)

## Generated package

`export_fab.sh` can produce, under ignored `fab/minimal-vga/`:

- Gerbers and Excellon drill;
- deterministic Gerber/drill ZIP and SHA256 list;
- schematic and assembly-review PDFs;
- engineering BOM and draft assembly BOM/CPL;
- manual-install and post-assembly-insertion lists; and
- mechanical, ERC, DRC, package-integrity, and vendor-preview check reports.

Per-report `READY` states describe the scope named by that report. They are not
design-release or purchase authorization. The top-level status is tracked in
`../docs/rev-a-manufacturing-readiness.md`.

## Design blockers

- T80 and tv80 spin-off tops boot the patched real Juku ROM framebuffer-identical
  to cosim; this simulation result does not validate the stale routed copper.
- U5 decode behavior is simulated in both jumper modes. U24's corrected
  Gray-coded pin/timing contract meets vendored MK4564-12 limits at 4 MHz;
  neither GAL has been compiled, programmed, or bench-tested on the chosen device.
- VGA timing activity is proven, but no real-ROM prompt/banner is rendered from
  the shared DRAM path.
- Actual oscillator, reset supervisor, DRAM, ROM, GAL, socket, fuse, TVS,
  connector, and assembly-process choices require datasheet/footprint review.
- The autorouted copper and power/return strategy need independent review.

## Regeneration commands

```sh
spinoffs/minimal-vga/sim/check.sh
spinoffs/minimal-vga/sync/check.sh
spinoffs/minimal-vga/kicad/check_rev_a_physical.sh
spinoffs/minimal-vga/kicad/check_rev_a_pcb.sh
spinoffs/minimal-vga/kicad/export_fab.sh
```

Routing changes must be regenerated from the source model and then rechecked;
do not hand-edit a generated artifact and treat it as source truth.

## Router toolchain (Linux and macOS)

`route_rev_a_pcb.sh` needs the **ddanila/freerouting fork** (branch `custom`,
vendored as the `external/freerouting` submodule) and **Java 25**. One-time
setup, identical on both platforms:

```sh
git submodule update --init external/freerouting
cd external/freerouting && ./gradlew --no-daemon executableJar
```

With the USB-C connector (J3) rotated to the board edge, freerouting cannot tie
its shield tabs to the ground contacts through the inset GND plane, so route
with the GND shield seed:

```sh
SEED_ROUTES=1 SEED_NETS=GND spinoffs/minimal-vga/kicad/route_rev_a_pcb.sh
```

The seed (`seed_rev_a_routes.py`, `GND`) adds two short F.Cu jumpers from J3's
SMD ground contacts to its adjacent shell tabs; everything else routes normally.

Gradle's toolchain support auto-provisions a Temurin JDK 25 into
`~/.gradle/jdks/` on the first build (no system Java install needed), and the
route script probes that home-folder JDK automatically — both the Linux layout
(`eclipse_adoptium-25-*/bin/java`) and the macOS bundle layout
(`eclipse_adoptium-25-*/jdk-25*/Contents/Home/bin/java`). Overrides: `JAVA_BIN`
for the runtime, `FREEROUTING_JAR` for the jar. The stock freerouting jar is a
fallback only — the default `freerouting-router-v19` algorithm requires the
fork (PolylineTrace.combine fix, headless settings application, dense-board
stagnation tuning, headless v1.9 router selection). Verified on macOS arm64:
Temurin 25.0.3 auto-provisioned, fork jar built and smoke-tested (2026-07-16).

## Future assembly policy

If the design hold is eventually cleared:

- recheck all stock-sensitive CPNs and vendor capabilities immediately before
  ordering;
- mount socketed/vintage/programmed ICs only according to the final insertion
  list;
- confirm DIP widths, pin 1, polarized parts, USB-C/terminal pinout, and every
  cable-facing connector from the selected parts' datasheets;
- save vendor DFM/preview settings and final checksums with the private order
  record; and
- never reuse the current ZIP after any schematic, footprint, net, or routing
  change.
