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

| Pin | Role | Net | Source |
| ---: | --- | --- | --- |
| 10 | A0 | `BA0` | scan; direct owner continuity 2026-07-15 proves D94.10/A0 shares D93.5/A0 |
| 11 | A1 | `BA1` | scan; direct owner continuity 2026-07-15 proves D94.11/A1 shares D93.6/A1 and D27.8/A1 |
| 12 | A2 | `IORD` | scan sheet-1 full-resolution plus direct owner continuity 2026-07-15: D5.25 IORD runs into D7.9; D94.12/A2 joins D27.5/RD_N and D29.4. D29.4 conflicts with the older IOM_STATUS scan interpretation and is adopted from the physical board; recheck D29.4-D7.8, D29.4-D29.8, and D29.8-D27.5 later. D93.4 belongs only to D94.3 |
| 13 | A3 | `IOWR` | owner continuity 2026-07-19: D105 NAND output pin3 is the qualified active-low peripheral write rail. Exact .009 detail 101805510 shows D7.11/PROM_EN and D105.3 on distinct local strokes; the former output-output join claim was a tracing error. Its inputs are D7.8 I/O-cycle-active high and D13.4 CPU-write-active high. Directly confirmed endpoints are D94.13, D29.5, D10.2, D11.10, D26.36, and D27.36; existing sheet-derived PIT write endpoints remain on the same rail. D5.27 is the separate raw IOWR_N source into D7.10 |
| 14 | A4 | `D94_A4_D101_Q0` | owner continuity 2026-07-19 confirms D94.14/A4 reaches D101 К555КП12 Q0/pin7; the earlier R88 branch is retracted |
| 15 | E_N | `FDC_CS_N` | exact .009 sheet 1 draws D9.7 as CS7 to sheet 3; exact sheet 3 draws CS7 to D94 enable pin15 and D93 chip-select pin3. Direct owner continuity 2026-07-15 confirms D94.15 to D93.3 and isolates D94 output pin2 from this conductor |

## Output Pins

| Pin | Role | Net | Captured activity | Source |
| ---: | --- | --- | --- | --- |
| 1 | D0 | `D94_D0_BOUNDARY` | asserts at rows 03, 07, 11, 15 | exact .009 E3 sheet 1 PXL_20260718_101817644.jpg draws R8=2k from +5 V to -WREQ; sheet 3 PXL_20260718_101633062.jpg traces D94.1 through the top bundle to WREQ (1), establishing their intended source node. Owner continuity 2026-07-19 locally joins D94.1 to R8 and +5 V but found no other load in the measured scope; physical D94.1-to-D2.15/WREQ continuity remains unverified, so this owner boundary is not yet merged into WREQ_N. |
| 2 | D1 | `D94_D1_D99_A2N` | asserts at rows 04, 05, 06, 07, 08, 09, 10, 11, 20, 21, 22, 23, 24, 25, 26, 27 | owner continuity 2026-07-19 proves D94.2 reaches D99 К155АГ3 second-section active-low A input pin9 and R89.1; D94.2 does not reach D99.8 or GND, and R89.2 reaches +5 V Exact .009 Э3 sheet-3 overview PXL_20260718_101633062.jpg traces the D94.2 line across the top to D96.11 CLK2; detail PXL_20260718_101641055.jpg shows CLK2 crossing D28.10 without a junction. Owner solder crop 200506061 shows a candidate B.Cu route from registered D96.11 near (625,1994) to a joint near registered D28.11 (839,1996), which belongs to separate FDC_DRQ in the exact source; confirm both pin identities and continuity before changing either model net. |
| 3 | D2 | `FDC_RE_N` | asserts at rows 08, 09, 10, 24, 25, 26, 27 | owner continuity 2026-07-19 proves D94 output pin3 reaches D93 read-enable pin4 and R88.1; R88.2 is +5 V |
| 4 | D3 | `FDC_WE_N` | asserts at rows 04, 05, 06, 20, 21, 22, 23 | owner continuity 2026-07-19 proves D94 output pin4 reaches D93 write-enable pin2 and R87.1; R87.2 is +5 V |
| 5 | D4 | `NC` | invariant released | owner/photo-confirmed PCB no-connect |
| 6 | D5 | `D94_D5` | invariant released | owner continuity and exact-revision .009 E3 drawing review 2026-07-21 close D94.6 as electrically NC; registered component imagery proves only a local floating copper stub to the plated handoff |
| 7 | D6 | `D94_D6` | invariant released | owner continuity and exact-revision .009 E3 drawing review 2026-07-21 close D94.7 as electrically NC; registered imagery preserves its local floating copper departure without inventing a load |
| 9 | D7 | `D94_D7` | invariant released | owner continuity and exact-revision .009 E3 drawing review 2026-07-21 close D94.9 as electrically NC; registered imagery preserves its local floating copper departure without inventing a load |

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

## Textual / Photo Survey Leads

- The official .009 BOM trail identifies the FDC-era D94 as the second
  К155РЕ3, programmed as `ДГШ5.106.092`.
- Earlier D94 references in the sheet-3/tape-cluster survey are known
  refdes reuse history, not evidence for the FDC-era control PROM.
- The guarded firmware inspection establishes that `.113/.117` belong
  to the `.106.103`-family owner-scan evidence and are not a burnable
  D94 `.092` substitute. The repeated physical `.092` image is authoritative.
- Validated local package fits preserve D94.10-.14 coordinates on both sides.
  Socket-obscured copper does not independently prove their remote endpoints.
- D4/pin5 is a PCB no-connect; D93.1 owns a separate open stub.
  D5-D7 have local copper stubs but are electrically NC by owner continuity
  and exact-revision drawing review. D0's hidden load remains unresolved.
- CS7/D9.7 is the source-closed enable. The nearby `V3_RC` network
  (R17.1/C99.1/D9.6) has no D94 signal endpoint in JSON, DSN, or PCB.
- The programming-disk search is owned by
  [vendored disk catalog](vendored-disk-catalog.md); the physical dump
  supplies D94 contents independently of that negative search.

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

D94 is a 32 x 8 PROM. The table below uses reader input indices A4..A0;
the board mapping is now A0=BA0, A1=BA1, A2=IORD, A3=D105.3 qualified /WR,
and A4=D101.7. D5-D7 are owner/drawing-closed NC.

| Row | A4 | A3 | A2 | A1 | A0 | D7..D0 |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 00 | 0 | 0 | 0 | 0 | 0 | `FF` |
| 01 | 0 | 0 | 0 | 0 | 1 | `FF` |
| 02 | 0 | 0 | 0 | 1 | 0 | `FF` |
| 03 | 0 | 0 | 0 | 1 | 1 | `FE` |
| 04 | 0 | 0 | 1 | 0 | 0 | `F5` |
| 05 | 0 | 0 | 1 | 0 | 1 | `F5` |
| 06 | 0 | 0 | 1 | 1 | 0 | `F5` |
| 07 | 0 | 0 | 1 | 1 | 1 | `FC` |
| 08 | 0 | 1 | 0 | 0 | 0 | `F9` |
| 09 | 0 | 1 | 0 | 0 | 1 | `F9` |
| 10 | 0 | 1 | 0 | 1 | 0 | `F9` |
| 11 | 0 | 1 | 0 | 1 | 1 | `FC` |
| 12 | 0 | 1 | 1 | 0 | 0 | `FF` |
| 13 | 0 | 1 | 1 | 0 | 1 | `FF` |
| 14 | 0 | 1 | 1 | 1 | 0 | `FF` |
| 15 | 0 | 1 | 1 | 1 | 1 | `FE` |
| 16 | 1 | 0 | 0 | 0 | 0 | `FF` |
| 17 | 1 | 0 | 0 | 0 | 1 | `FF` |
| 18 | 1 | 0 | 0 | 1 | 0 | `FF` |
| 19 | 1 | 0 | 0 | 1 | 1 | `FF` |
| 20 | 1 | 0 | 1 | 0 | 0 | `F5` |
| 21 | 1 | 0 | 1 | 0 | 1 | `F5` |
| 22 | 1 | 0 | 1 | 1 | 0 | `F5` |
| 23 | 1 | 0 | 1 | 1 | 1 | `F5` |
| 24 | 1 | 1 | 0 | 0 | 0 | `F9` |
| 25 | 1 | 1 | 0 | 0 | 1 | `F9` |
| 26 | 1 | 1 | 0 | 1 | 0 | `F9` |
| 27 | 1 | 1 | 0 | 1 | 1 | `F9` |
| 28 | 1 | 1 | 1 | 0 | 0 | `FF` |
| 29 | 1 | 1 | 1 | 0 | 1 | `FF` |
| 30 | 1 | 1 | 1 | 1 | 0 | `FF` |
| 31 | 1 | 1 | 1 | 1 | 1 | `FF` |

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
- Runnable-model disposition: the behavioral FDC now consumes the
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
- D94 is now classified as an FDC control/decode PROM because its proved
  D2/D3 outputs terminate at D93 and D1 serves its support logic.
  It is not evidence for the separate
  shared-DRAM video-slot schedule.
- The 256-bit content ambiguity is closed. The remaining ambiguity is
  electrical: enable timing and the far ends/branches of output nets.
- The physical image is burnable, but that alone cannot release the FDC
  circuit or the replica PCB while those continuity boundaries remain.
- Do not reuse `.113` or `.117` as D94: those scans are guarded as
  `.106.103`-family evidence, not the processor-module `.092` content.
