# D94 .092 reconstruction constraints

Status: **D94 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED**

This generated report records what the repo can currently prove about
the .009 FDC-era `D94` К155РЕ3 PROM (`ДГШ5.106.092`). Its repeated
physical table is validated for programming; connectivity holds remain.

## Command

```sh
python3 scripts/report_d94_reconstruction_constraints.py
```

The generator checks the physical-image hash and all 256 table bits,
board/DSN/source-PCB pin nets, recorded evidence fields, and HDL text markers.
It does not execute HDL or establish physical timing/continuity. Run
`sync/juku_top_periph_bus_check.sh` for the decoded-bus simulation.

## Address / Enable Pins

Board identity: D94 type is `RE3_PROM_092`.

Address summary: all five address inputs are owner-continuity-closed nets.

Detailed source and owner provenance is retained in each net’s `src`
field in [the board JSON](../kicad/juku.board.json). Physical holds are
summarized under Reconstruction Boundary below.

| Pin | Role | Net |
| ---: | --- | --- |
| 10 | A0 | `BA0` |
| 11 | A1 | `BA1` |
| 12 | A2 | `IORD` |
| 13 | A3 | `IOWR` |
| 14 | A4 | `D94_A4_D101_Q0` |
| 15 | E_N | `FDC_CS_N` |

## Output Pins

Captured activity lists decimal reader addresses.

| Pin | Role | Net | Captured activity |
| ---: | --- | --- | --- |
| 1 | D0 | `D94_D0_BOUNDARY` | asserts at rows 03, 07, 11, 15 |
| 2 | D1 | `D94_D1_D99_A2N` | asserts at rows 04, 05, 06, 07, 08, 09, 10, 11, 20, 21, 22, 23, 24, 25, 26, 27 |
| 3 | D2 | `FDC_RE_N` | asserts at rows 08, 09, 10, 24, 25, 26, 27 |
| 4 | D3 | `FDC_WE_N` | asserts at rows 04, 05, 06, 20, 21, 22, 23 |
| 5 | D4 | `NC` | invariant released |
| 6 | D5 | `D94_D5` | invariant released |
| 7 | D6 | `D94_D6` | invariant released |
| 9 | D7 | `D94_D7` | invariant released |

## KiCad DSN Cross-check

This table compares the current freerouting DSN against board JSON.
Board JSON and the regenerated KiCad schematic own connectivity.

| Pin | Role | DSN Net | Result |
| ---: | --- | --- | --- |
| 1 | D0 | `D94_D0_BOUNDARY` | PASS |
| 2 | D1 | `D94_D1_D99_A2N` | PASS |
| 3 | D2 | `FDC_RE_N` | PASS |
| 4 | D3 | `FDC_WE_N` | PASS |
| 5 | D4 | - | missing in DSN |
| 6 | D5 | `D94_D5` | PASS |
| 7 | D6 | `D94_D6` | PASS |
| 8 | GND | `GND` | PASS |
| 9 | D7 | `D94_D7` | PASS |
| 10 | A0 | `BA0` | PASS |
| 11 | A1 | `BA1` | PASS |
| 12 | A2 | `IORD` | PASS |
| 13 | A3 | `IOWR` | PASS |
| 14 | A4 | `D94_A4_D101_Q0` | PASS |
| 15 | E_N | `FDC_CS_N` | PASS |
| 16 | VCC | `P5V` | PASS |

## KiCad PCB Cross-check

This table checks D94 pad nets in `kicad/juku.kicad_pcb` against the
board model. It does not compare either routed variant or establish
routed placement/copper parity; see [placement parity](board-placement-parity.md).

| Pin | Role | PCB Net | Result |
| ---: | --- | --- | --- |
| 1 | D0 | `D94_D0_BOUNDARY` | PASS |
| 2 | D1 | `D94_D1_D99_A2N` | PASS |
| 3 | D2 | `FDC_RE_N` | PASS |
| 4 | D3 | `FDC_WE_N` | PASS |
| 5 | D4 | - | unnetted in PCB |
| 6 | D5 | `D94_D5` | PASS |
| 7 | D6 | `D94_D6` | PASS |
| 8 | GND | `GND` | PASS |
| 9 | D7 | `D94_D7` | PASS |
| 10 | A0 | `BA0` | PASS |
| 11 | A1 | `BA1` | PASS |
| 12 | A2 | `IORD` | PASS |
| 13 | A3 | `IOWR` | PASS |
| 14 | A4 | `D94_A4_D101_Q0` | PASS |
| 15 | E_N | `FDC_CS_N` | PASS |
| 16 | VCC | `P5V` | PASS |

## Current Evidence Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Board identity names D94 as `.092`, not stale `.113` | PASS | `kicad/juku.board.json` type `RE3_PROM_092` |
| Every D94 address input is explicitly accounted | PASS | board JSON nets |
| Every D94 address input has reviewed two-sided photo coordinates | PASS | local-package-fit measurement rows for pins 10, 11, 12, 13, 14 |
| D94 address input sources are traced | PASS | direct owner continuity/source nets for pins 10-14 |
| Retired D94 BA11..BA15 mapping is absent from the source model | PASS | board JSON BA nets |
| Held freerouting DSN matches the current D94 mapping | PASS | `kicad/juku.dsn` is a routed engineering snapshot; authoritative connectivity is board JSON/schematic |
| Source PCB agrees with current board-model D94 output nets | PASS | `kicad/juku.kicad_pcb`; source pad-net comparison only |
| `V3_RC` is present but not D94 enable/output evidence | PASS | board nodes `R17.1`, `C99.1`, `D9.6`; DSN/PCB D94 signal pins are not on `V3_RC` |
| Enable pin D94.15 is traced | PASS | board JSON nets |
| Enable pin15 is isolated from output pin2 | PASS | direct owner continuity; distinct board nets |
| Any D94 output net is traced | PASS | `D94_D0_BOUNDARY`, `D94_D1_D99_A2N`, `FDC_RE_N`, `FDC_WE_N`, `NC`, `D94_D5`, `D94_D6`, `D94_D7` |
| Every D94 output pad has an explicit net/boundary | PASS | 8/8 output pins netted |
| D94 D5-D7 are owner/drawing-closed NC despite local copper stubs | PASS | owner continuity 2026-07-21 plus component-side observations for pins 4, 6, 7, 9 |
| Captured table asserts only D0-D3; D4-D7 stay released | PASS | exhaustive 32-row physical table classification |
| Minimized active-low equations reproduce all 256 captured bits | PASS | exhaustive address/output comparison against the physical image |
| Validated `.092` physical image exists and matches SHA256 | PASS | `ref/physical-proms/validated/d94_092.raw.bin` / `bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0` |
| Official .009 BOM/photo notes identify D94 as `.092` | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| Reused D94 refdes/tape-cluster history is guarded | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| `.113/.117` scans are guarded as not-D94 | PASS | `docs/re3-firmware-inspection.md` |
| Vendored programming disks have a guarded PROM-name/marker/exact-table audit | PASS | `docs/vendored-disk-catalog.md` |
| HDL adopts physical open-collector table | PASS | `hdl/devices.v::re3_prom_092` |
| Structural HDL records measured D94 A0-A4 mapping | PASS | `hdl/juku_top.v`; BA0, BA1, IORD, D105.3 qualified /WR, D101.7 |
| `juku_top` connects the three accepted local FDC controls | PASS | `hdl/juku_top.v` |
| Runnable HDL and bus-test markers cover D94 strobes | PASS | runnable A4 is held high; bus test forces A4 low separately; source-text checks only |
| Video slot audit does not rely on D94 | PASS | `docs/video-slot-timing-audit.md` |

## Minimized asserted-output logic

Define `S(Dn)=1` when the open-collector output is programmed active
(captured raw bit `0`), and define the shared qualifier
`Q = A4 | !A1 | !A0`. Exhaustive comparison against all 32 addresses
gives:

| Output | Exact asserted equation | Physical destination |
| --- | --- | --- |
| `S(D0)` | `!A4 & A1 & A0` | R8 2 kΩ pull-up-only boundary |
| `S(D1)` | `A3 xor A2` | D99.9 / R89 pull-up |
| `S(D2)` | `A3 & !A2 & Q` | D93 `/RE` |
| `S(D3)` | `!A3 & A2 & Q` | D93 `/WE` |
| `S(D4..D7)` | `0` | owner/drawing-closed NC outputs; always released |

These equations sharpen, but do not replace, continuity evidence:

- D2 `/RE` and D3 `/WE` are mutually exclusive and select opposite
  one-hot states of A3/A2. This proves the PROM is a cycle-control
  decoder rather than an address-only register decoder.
- A2 is owner-measured to active-low `IORD`. Therefore, while `Q` is
  true on a selected FDC register cycle, the equations require A3=1
  for a read (`IORD`=0 -> `/RE` asserted) and A3=0 for a write
  (`IORD`=1 -> `/WE` asserted). A3 must consequently be polarity-
  equivalent to active-low `IOWR` during those cycles. This is an exact
  polarity constraint, confirmed by owner continuity: D94.13 belongs
  to D105.3 qualified peripheral `/WR`, while D5.27 is the distinct raw
  `IOWR_N` input to D7.10. D104.7 is separate (~84 kΩ to D94.13).
- At BA1:BA0=`11` with A4 low, `Q` becomes false, both D93 strobes
  release, and D0 asserts independently of A3/A2. A live D0 branch
  probe should therefore target exactly that row condition.
  Conversely, A4 high restores the normal D93 read/write strobes at
  register 3. Because A4 cancels out of `Q` at every other BA1:BA0
  value, D101.Q0 is exactly a register-3 transfer-steering qualifier;
  this does not identify the alternate D0 load or D101's broader role.
- D4-D7 cannot change digital behavior for any captured address. Owner
  continuity closes D5-D7 as NC; photographed local stubs remain layout evidence.
- A3's electrical source is owner-closed to D105.3 qualified peripheral
  `/WR`. A4's physical endpoint is likewise closed to D101.7, but its
  runtime mux semantics and D0's far endpoint remain functional/source
  boundaries rather than inferred nets.

## Address Space

D94 is a 32 x 8 PROM, indexed by reader inputs A4..A0. The raw bytes
are retained in [the hexadecimal table](../ref/physical-proms/validated/d94_092.raw.hex).
The board mapping is A0=BA0, A1=BA1, A2=IORD, A3=D105.3 qualified /WR,
and A4=D101.7.

## Reconstruction Boundary

- Known: D94 is present in the .009 FDC quadrant and all five address
  inputs have direct owner-continuity mappings.
- Known control destinations: D94 enable pin15 reaches D93.3 CS; D1/pin2
  reaches D99.9/R89; D2/pin3 reaches D93.4/R88 RE; and D3/pin4
  reaches D93.2/R87 WE. D4/pin5 is a PCB no-connect, while
  D93.1 owns a separate open stub.
  D5-D7/pins6,7,9 are also NC by exact-revision drawing review and
  owner continuity on 2026-07-21.
  D0/pin1 has only R8 2 kΩ to +5 V in the measured scope.
- Known content: three matching reads including a power-cycled read yield
  raw SHA256 `bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0`.
- R87/R88/R89 are modeled as 6.2 kΩ; direct photo reads and the
  separately designated BOM's corroboration limits are recorded in
  [upper assembly placement](fdc-upper-assembly-placement.md#d94-pull-up-row).
- Closed CS/enable upstream source: D9.7 `CS7` reaches D94.15 and D93.3
  on exact .009 sheets 1 and 3; owner continuity confirms the local branch.
- Unknown: D0 hidden-branch status.
- Closed A3 source: D94.13 belongs to D105.3 qualified peripheral `/WR`.
  D5.27 is the distinct raw `IOWR_N` input to D7.10; a simultaneous
  operating-level capture is useful corroboration, not a missing join.
- Runnable-model disposition: the behavioral FDC consumes the
  physical table's `/RE` and `/WE`. A3 consumes the owner-closed D105.3
  `iowr_n` conductor. The CS7 decoded enable is source-closed; only
  pulled-high A4 runtime behavior remains a simulation fit. Yosys/LVS preserves the
  physical boundary nets separately.
  The fast bus guard also forces A4 low on register 3 and proves D0
  asserts while both D93 strobes release, without assigning D0 a load.
- D5-D7 are electrically NC. Registered component-side photographs show
  only local copper departures, which continuity does not extend to a load.
- D4-D7 are program-inert: raw bits 4-7 remain one
  (open-collector released) at all 32 captured rows. D1-D3 are active
  with closed destinations; D0 is active and destination-unresolved.
- The traced `V3_RC` RC network is a negative cross-check here, not a
  replacement source for D94: its current nodes are `R17.1`, `C99.1`,
  and `D9.6`, with no D94 signal endpoint in JSON, DSN, or PCB.
- D94 is classified as an FDC control/decode PROM because its proved
  D2/D3 outputs terminate at D93 and D1 serves its support logic.
  It is not evidence for the separate
  shared-DRAM video-slot schedule.
- The 256-bit content ambiguity is closed. The remaining ambiguity is
  electrical: enable timing and the far ends/branches of output nets.
- The physical image is burnable, but that alone cannot release the FDC
  circuit or the replica PCB while those continuity boundaries remain.
- Do not reuse `.113` or `.117` as D94: those scans are guarded as
  `.106.103`-family evidence, not the processor-module `.092` content.
