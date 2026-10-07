# VJUGA Rev A fabrication notes

Status: **PACKAGE REGENERATION REQUIRED / DESIGN HOLD**.

Rev A is a routed workbench experiment. [Source DRC](../docs/rev-a-drc-readiness.md)
binds the recorded zero-error, zero-unconnected result to the exact PCB hash.
[Manufacturing readiness](../docs/rev-a-manufacturing-readiness.md) owns the
release requirements. The [Rev B five-board plan](../docs/rev-b-five-board-order-plan.md)
is the current order target.

## Current physical baseline

- 200 x 200 mm, four copper layers: `F.Cu`, `In1.Cu`, `In2.Cu`, and `B.Cu`.
- 119 footprints, 133 PCB nets, and 2,887 tracks/vias in the current source.
- Parts and functional-block borders are aligned to a 0.2" (5.08 mm) grid;
  capacitor positions follow the [placement rules](../docs/rev-a-placement-rules.md).
  In1.Cu is a filled GND plane and In2.Cu a filled VCC plane; F.Cu/B.Cu carry
  the signal routing.
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

The historical package predates source corrections, and its upload ZIP is
absent from the current workspace. Regenerate it from the accepted source;
vendor upload preview, stock/capability checks and independent human review
remain open afterward. See [manufacturing readiness](../docs/rev-a-manufacturing-readiness.md).

The exporter requires `kicad-cli` and Python `pcbnew` from the same KiCad major
version and verifies that Python can load the board before writing package
output. The retained PCB requires KiCad 10 or newer. The repository locators
prefer working Flatpak wrappers, then probe other installed tools; they do not
pin the selected version to the recorded DRC run. Use `KICAD_CLI` and
`KICAD_PYTHON` to select a coherent installation.

Export writes into the existing output directory; it does not clear old outputs
or roll back partial results on failure. By default it runs the behavioral, ERC
and error-level DRC gates before fabrication output. The `MINIMAL_VGA_ALLOW_*`
overrides permit design-held debug exports and do not qualify a release.
`MINIMAL_VGA_REUSE_BEHAVIORAL_REPORT=1` checks PASS markers and input modification
times; it does not bind the reused report to input hashes.

Per-report `READY` states describe the scope named by that report. They are not
design-release or purchase authorization. The top-level status is tracked in
`../docs/rev-a-manufacturing-readiness.md`.

## Release scope

Source DRC, simulated boot, timing checks and static part contracts are
separate evidence. Physical board acceptance, GAL programming, full-board LVS,
selected-part review and package release remain governed by
[manufacturing readiness](../docs/rev-a-manufacturing-readiness.md).

## Validation and export commands

Run from the repository root. The broad simulation aggregate includes Rev B
checks and can overwrite `cosim/vram.bin`; see the
[simulation guide](../sim/README.md) for dependencies and scope.

```sh
spinoffs/minimal-vga/sim/check.sh
spinoffs/minimal-vga/sync/check.sh
spinoffs/minimal-vga/kicad/check_rev_a_physical.sh
spinoffs/minimal-vga/kicad/check_rev_a_pcb.sh
spinoffs/minimal-vga/kicad/export_fab.sh
```

The router regenerates and overwrites the tracked `rev-a-physical.kicad_pcb`
before routing, then imports the session and refills planes. A failed run can
leave that file replaced or partly processed. Review the diff and require fresh
DRC and connectivity checks before accepting a new route. `BOARD_JSON`, `PCB`
and `OUT` select alternative source, PCB and scratch-output paths.

## Router toolchain (Linux and macOS)

`route_rev_a_pcb.sh` needs the **ddanila/freerouting fork** (branch `custom`,
vendored as the `external/freerouting` submodule) and **Java 25**. Build the
repository-pinned submodule revision with a Java runtime available through
`JAVA_HOME` or `PATH` to start Gradle:

```sh
git submodule update --init external/freerouting
(cd external/freerouting && ./gradlew --no-daemon executableJar)
```

The retained routing recipe seeds the J3 USB-C GND shield jumpers and two
decode debug taps to J95 (`RE3_D0`, `DEC_RAM_N`):

```sh
SEED_ROUTES=1 SEED_NETS=GND,RE3_D0,DEC_RAM_N \
  spinoffs/minimal-vga/kicad/route_rev_a_pcb.sh
```

The seeds (`seed_rev_a_routes.py`) add: two short F.Cu jumpers from J3's SMD
ground contacts to its adjacent shell tabs, and left-margin B.Cu paths from the
RE3/decode pull-ups (R36/R33) into J95.5/J95.2. The remaining connections are left to the router.

Gradle's toolchain resolver can provision the required JDK 25 when it is absent.
The route script probes `.tools/jre25`, matching JDKs under `~/.gradle/jdks/`
and `~/.jdks/`, then falls back to `java` on `PATH`. Its fallback does not check
the Java version before regenerating the PCB, so verify runtime compatibility
first. Overrides: `JAVA_BIN` for the runtime, `FREEROUTING_JAR` for the jar.
The maintained `freerouting-router` algorithm is selected explicitly, with the optimizer off
so machine-global defaults cannot change the production route. The fork retains
bounded trace combining, headless/offline defaults, and KiCad-compatible SES
identifiers/grammar. Route results must pass the current board's DRC and connectivity checks.

`JAVA_HEAP=auto` selects the script's calculated heap limit. Set an explicit
limit appropriate to the machine, such as `JAVA_HEAP=4096m` when at least
that much memory is available for the router. Historical route runtime and
peak-memory observations are not guarantees for a new source or machine.

## Assembly outputs

Use [the sourcing policy](../docs/rev-a-sourcing-plan.md) for socket insertion,
manual placements, selected-part checks and order-time stock/process review.
The assembly exporter writes its CSVs and readiness report before rejecting
footprints missing engineering BOM rows. Require a successful exporter exit;
an existing `assembly-readiness.md`, even with `READY`, is insufficient.
Never reuse an exported ZIP after schematic, footprint, net or routing changes.
