# freerouting: use our custom submodule build (not stock)

**Routing in this repo must use the custom freerouting built from the
`external/freerouting` submodule (branch `custom`). Never drop a stock
freerouting release into `.tools/freerouting/`.** The stock jar looks
interchangeable but is missing fixes we depend on and will fail or misbehave on
this board.

## Why

The `custom` branch (submodule `external/freerouting`) carries:

- **Bounded `PolylineTrace.combine()`** — stock recurses with no progress
  guarantee and hits `StackOverflowError` on degenerate/overlapping trace
  geometry (e.g. hand-placed locked wires imported from a DSN), so a headless
  routing job never completes (it then polls the job at 0% CPU forever). The
  custom build bounds the loop.
- Stagnation-stop tuning for our dense board (40-pass patience, 0.05 threshold).
- Headless v1.9 router selection + serialized headless output.

## Use it

```sh
# builds from the submodule if needed, then routes HEADLESS (no GUI):
scripts/run-freerouting.sh -de kicad/juku.dsn -do out.ses -mp 10 -mt 10
```

`run-freerouting.sh` refuses to run a stock jar: it checks the installed
`.tools/freerouting/freerouting.jar` for a custom-only marker string and rebuilds
from the submodule if it is missing or stock. Build explicitly with:

```sh
scripts/build-freerouting.sh   # -> .tools/freerouting/freerouting.jar (+ PROVENANCE.txt)
```

## Fresh checkout

The jar (~59 MB) is gitignored; the **submodule commit is the source of truth**:

```sh
git submodule update --init external/freerouting
scripts/build-freerouting.sh
```

Needs a JDK 25+ (the jar targets class-file 69.0). The scripts find Homebrew
`openjdk@25`/`@26` or `java_home`; override with `FREEROUTING_JDK=/path/to/jdk`.
`.tools/freerouting/PROVENANCE.txt` records the submodule commit the installed
jar was built from and its sha256.

## Custom-build behavior (branch `custom`)

- **Telemetry hardwired off** — no analytics or update-check network calls
  regardless of config, and no 1 s analytics startup sleep. Offline by default.
- **GUI forced off when headless** — `gui.enabled` is set false under
  `GraphicsEnvironment.isHeadless()`, so the "Couldn't get screen resolution"
  warning no longer prints on every headless/CI run.
- **Deterministic routing** — the RNG is already seeded (`new Random(0)` /
  `setSeed(ripup_costs)`). Verified: two `-mt 1` runs of the same DSN produce a
  **byte-identical `.ses`**, so single-threaded routing is reproducible
  (→ stable `board_sha256` for the pinned fabrication evidence). Multi-threaded
  runs (`-mt >1`) trade that reproducibility for speed.

## Speed

The core autoroute pass is effectively single-threaded (`-mt` mainly helps
fanout/optimize), so it is single-core bound: ~2 min/pass on an M4 Pro for the
full source board, converging over several passes with the last few nets
hand-finished.
