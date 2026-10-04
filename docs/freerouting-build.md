# Custom freerouting build

Routing uses the user's custom fork pinned by the `external/freerouting`
submodule. Build its executable JAR for `.tools/freerouting/`; a stock release
does not carry the same compatibility fixes.

## Build and provenance

Run from the repository root with Bash, Git, `unzip`, and `shasum` available.
The Gradle wrapper may download Gradle and build dependencies on the first
build, so an uncached build needs network access.

```sh
git submodule update --init external/freerouting
scripts/build-freerouting.sh
```

The build requires a JDK 25+ for class-file version 69. It searches the recorded
Homebrew, macOS `java_home`, Gradle-managed and Linux JDK locations; use
`FREEROUTING_JDK=/path/to/jdk` explicitly when needed. The script builds the
checked-out submodule and records its commit and JAR SHA-256 in
`.tools/freerouting/PROVENANCE.txt`. Verify the submodule matches the root pin
before building; the build script does not reset an existing checkout. Also
check `git -C external/freerouting status --short`: the build includes local
source edits, while provenance records only `HEAD` and the resulting JAR hash,
not a dirty-tree diff. A commit label alone therefore does not identify those
inputs.

`run-freerouting.sh` checks for the custom `PolylineTrace.combine` marker and
rebuilds when the JAR is absent or lacks it. That marker distinguishes this
fork's build lineage; it does not prove that an already-installed JAR matches
the current submodule commit. Rebuild explicitly after a pin change and retain
its provenance with route evidence.

The build invokes `./gradlew executableJar -x test`, then checks the custom
marker and installs the JAR. It does not run the router’s test suite or prove
reproducible JAR bytes. `FREEROUTING_JDK` selects an executable Java location;
the helper does not validate its version, so check `bin/java -version` when
supplying it explicitly.

## Run and review

```sh
scripts/run-freerouting.sh -de kicad/juku.dsn \
  -do /tmp/juku-router-review.ses -mp 100
```

The wrapper forces headless Java and defaults to `-mt 1` unless a thread count
is supplied. Its runtime lookup is narrower than the build-script lookup:
use `FREEROUTING_JDK` or a compatible `java` on PATH on Linux.

Single-threaded execution and seeded random choices reduce variation but do
not guarantee identical routes or PCB hashes across source, algorithm,
configuration or toolchain changes. Record exact inputs and outputs and run
DRC/connectivity checks before promoting a route. Explicit `-mt N` selects a
different execution profile and needs its own evidence.

The main Juku route remains under [the routing hold](routed-refresh-audit.md).
An SES result alone does not close source-risk nets or authorize fabrication.

## Regenerate a DSN

The committed `kicad/juku.dsn` is a routed engineering snapshot. It must be
reviewed against current source connectivity before use. Export through the
matching KiCad Python API when the source board changes:

```sh
"$(scripts/find-kicad-python.sh)" -c \
  "import pcbnew; b=pcbnew.LoadBoard('kicad/juku.kicad_pcb'); assert pcbnew.ExportSpecctraDSN(b,'kicad/juku.dsn')"
```

Regenerate current evidence for changed inputs. Keep historical hash-bound
reports tied to their recorded artifacts; do not rewrite their identities to
match a later DSN. KiCad version, placement, zones and net definitions all form
part of the export context.

## Fork capabilities

The pinned fork carries bounded trace combining, headless/offline behavior and
KiCad-compatible SES identifiers and grammar. These capabilities permit the
repository workflow; they do not validate a particular routed board. Rev A/B
routing scripts also choose their own algorithm, seed and optimizer settings,
so use the board-specific workflow when regenerating those designs.
