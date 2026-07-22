# D94 .092 reconstruction constraints

Status: **D94 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED**

This generated report records what the repo can currently prove about
the .009 FDC-era `D94` К155РЕ3 PROM (`ДГШ5.106.092`). Its repeated
physical table is now burnable truth; unresolved connectivity is kept separate.

## Command

```sh
python3 scripts/report_d94_reconstruction_constraints.py
```

## Address / Enable Pins

Board identity: D94 type is `RE3_PROM_092`.

Address summary: all five address inputs are owner-continuity-closed nets.
The former `BA11..BA15` mapping came from the original FDC scaffold's
same-as-D8 analogy, not from `.009` scan, photo, or owner continuity evidence.

| Pin | Role | Net | Source |
| ---: | --- | --- | --- |
| 10 | A0 | `BA0` | scan; direct owner continuity 2026-07-15 proves D94.10/A0 shares D93.5/A0 |
| 11 | A1 | `BA1` | scan; direct owner continuity 2026-07-15 proves D94.11/A1 shares D93.6/A1 and D27.8/A1 |
| 12 | A2 | `IORD` | scan sheet-1 full-resolution plus direct owner continuity 2026-07-15: D5.25 IORD runs into D7.9; D94.12/A2 joins D27.5/RD_N and D29.4. D29.4 conflicts with the older IOM_STATUS scan interpretation and is adopted from the physical board; recheck D29.4-D7.8, D29.4-D29.8, and D29.8-D27.5 later. D93.4 belongs only to D94.3 |
| 13 | A3 | `IOWR` | owner continuity 2026-07-19: D105 NAND output pin3 is the qualified active-low peripheral write rail. Its inputs are D7.8 I/O-cycle-active high and D13.4 CPU-write-active high. Directly confirmed endpoints are D94.13, D29.5, D10.2, D11.10, D26.36, and D27.36; existing sheet-derived PIT write endpoints remain on the same rail. D5.27 is the separate raw IOWR_N source into D7.10 |
| 14 | A4 | `D94_A4_D101_Q0` | owner continuity 2026-07-19 confirms D94.14/A4 reaches D101 К555КП12 Q0/pin7; the earlier R88 branch is retracted |
| 15 | E_N | `FDC_CS_N` | direct owner continuity 2026-07-15 proves D94 enable pin15 reaches D93 chip-select pin3, and explicitly proves D94 output pin2 is isolated from this conductor. The upstream source is retained separately for later continuity |

## Output Pins

| Pin | Role | Net | Captured activity | Source |
| ---: | --- | --- | --- | --- |
| 1 | D0 | `D94_D0_BOUNDARY` | asserts at rows 03, 07, 11, 15 | owner continuity 2026-07-19: D94.1 joins R8 through approximately 2 kohm to +5 V; no other connection was found |
| 2 | D1 | `D94_D1_D99_A2N` | asserts at rows 04, 05, 06, 07, 08, 09, 10, 11, 20, 21, 22, 23, 24, 25, 26, 27 | owner continuity 2026-07-19 proves D94.2 reaches D99 К155АГ3 second-section active-low A input pin9 and R89.1; D94.2 does not reach D99.8 or GND, and R89.2 reaches +5 V |
| 3 | D2 | `FDC_RE_N` | asserts at rows 08, 09, 10, 24, 25, 26, 27 | owner continuity 2026-07-19 proves D94 output pin3 reaches D93 read-enable pin4 and R88.1; R88.2 is +5 V |
| 4 | D3 | `FDC_WE_N` | asserts at rows 04, 05, 06, 20, 21, 22, 23 | owner continuity 2026-07-19 proves D94 output pin4 reaches D93 write-enable pin2 and R87.1; R87.2 is +5 V |
| 5 | D4 | `NC` | invariant released | owner/photo-confirmed PCB no-connect |
| 6 | D5 | `D94_D5` | invariant released | owner continuity and exact-revision .009 E3 drawing review 2026-07-21 close D94.6 as electrically NC; registered component imagery proves only a local floating copper stub to the plated handoff |
| 7 | D6 | `D94_D6` | invariant released | owner continuity and exact-revision .009 E3 drawing review 2026-07-21 close D94.7 as electrically NC; registered imagery preserves its local floating copper departure without inventing a load |
| 9 | D7 | `D94_D7` | invariant released | owner continuity and exact-revision .009 E3 drawing review 2026-07-21 close D94.9 as electrically NC; registered imagery preserves its local floating copper departure without inventing a load |

## KiCad DSN Cross-check

This table records the held freerouting DSN. It intentionally predates the
2026-07-19 corrections; mismatches are migration evidence, not accepted
connectivity. Board JSON and the regenerated KiCad schematic are authoritative.

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

This table records the authoritative source PCB used by the promoted route.
Its D94 pad nets are checked directly against the board model; the routed
candidate identity gate separately proves the promoted board has the same pads.

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
| Source PCB agrees with current board-model D94 output nets | PASS | `kicad/juku.kicad_pcb`; promoted route has exact source-pad identity |
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
| HDL adopts measured D94 A0-A4 mapping | PASS | `hdl/juku_top.v`; BA0, BA1, IORD, D105.3 qualified /WR, D101.7 |
| `juku_top` connects the three accepted local FDC controls | PASS | `hdl/juku_top.v` |
| Runnable FDC consumes and cycle-checks physical D94 strobes | PASS | simulation-only upstream fits remain explicit in `hdl/juku_top.v`; `hdl/sim/juku_top_periph_bus_tb.v` |
| Video slot audit does not rely on D94 | PASS | `docs/video-slot-timing-audit.md` |

## Textual / Photo Survey Leads

- The official .009 BOM trail identifies the FDC-era D94 as the second
  К155РЕ3, programmed as `ДГШ5.106.092`.
- Earlier D94 references in the sheet-3/tape-cluster survey are known
  refdes reuse history, not evidence for the FDC-era timing PROM.
- The guarded firmware inspection establishes that `.113/.117` belong
  to the `.106.103`-family owner-scan evidence and are not a burnable
  D94 `.092` substitute. The repeated physical `.092` image is authoritative.
- The guarded `JUKPROG1`/`JUKPROG2`/`JUKPROGX` audit finds no active
  candidate filename, recoverable deleted filename, or strong raw ASCII
  `.037`/`.038`/`.039`/`.092`/RT4/RE3 marker. It also finds no exact
  validated raw/asserted table in full images or reconstructed active files
  under byte, reversed-address, ASCII/Intel-hex, or packed-nibble encodings.
  Proprietary, permuted, compressed, or otherwise transformed data remains
  possible, so this is negative search evidence rather than proof of absence.
- A 2026-07-13 indexed-web search for exact `ДГШ5.106.092`,
  `ДГШ5.106.092 Juku`, `Juku К155РЕ3 092 dump`, and
  `Juku ES-101 floppy PROM D94` returned no programming table, binary,
  scan, repository, or collector listing for this artifact. Generic Juku
  history and generic К155РЕ3 references do not constrain its contents.
- Direct owner continuity supersedes the mirrored-pin local interpretation:
  enable pin15 reaches D93.3 CS; D1/pin2 reaches D99.9 and R89;
  D2/pin3 reaches D93.4 /RE and R88; D3/pin4 reaches D93.2 /WE and R87.
  Address inputs A0/A1/A2/A3/A4 reach BA0, BA1, IORD,
  D105.3 qualified /WR, and D101.7 respectively. R8 is the 2 kohm
  pull-up-only D94.1 branch; D0's hidden load remains open, while
  owner continuity and exact-revision drawing review close D5-D7 as NC. Physical
  captures now provide the PROM contents.
- Git history proves the former A0-A4=`BA11..BA15` assignment entered in
  commit `ed69b9d` as an FDC scaffold explicitly described as the same
  convention as D8. No `.009` electrical source was cited. Direct owner
  continuity now replaces all five scaffold inputs with measured nets.
- Validated local package fits now preserve exact original-image coordinates
  for D94.10-.14 on both sides. Component copper is socket-obscured and
  the solder crop has no uniquely traceable remote endpoints, so these are
  reviewed measurement records rather than promoted electrical nets.
- Registered component-side local fits show copper departing D3-D7
  (pins 4-7 and 9). Direct continuity closes D3/pin4 to D93.2; the
  full-resolution exposed-socket recheck separates D4/pin5 from D93.1.
  D93.1 owns the visible open stub; D4/pin5 is a PCB no-connect.
  D5/pin6 reaches a proved plated local handoff
  at (2266,1828) px, but independent D93/D94 cross-side projections
  disagree by 54.2 px. Owner continuity and the exact `.009 E3` drawing
  now close D5-D7 as electrically NC despite those local stubs. D0/pin1 is
  destination-unresolved. The captured program keeps D4-D7 released
  at every row; D0 and the now-closed D3 are behaviorally active.
- The nearby `V3_RC` RC node is traced as `R17.1`, `C99.1`, and `D9.6`
  in board JSON/DSN, but D94 pin 15 and D3-D7 are not tied to it in
  board JSON, DSN, or PCB evidence. It cannot substitute for the missing
  remaining D94 enable/D0 boundary continuity.
- A 2026-07-11 high-resolution recheck projected D93.2 and D93.4 from
  the validated reflected D94 solder fit into the same source image.
  Neither pad shows an obvious solder-side fanout. Owner continuity now
  closes D94.15->D93.3 and corrects D94.2 to D99.9/R89, demonstrating why the
  earlier local mirrored-pin interpretation was insufficient.

## Input-mapping correction and control constraint

The three proved output destinations and physical table reject the old
scaffold mapping as a closed physical claim:

- D94.D2 and D94.D3 terminate at the separate active-low D93 `/RE` and
  `/WE` inputs. An FDC register must support both reads and writes at the
  same port address.
- If A0-A4 were only `BA11..BA15`, the same PROM row would drive both cycle
  directions and could not independently select `/RE` versus `/WE`.
- That mapping was never measured; it was copied by analogy from D8.
  Owner continuity now supplies the actual five input sources.

This does not refute the accepted local D94-to-D93 copper. It removes a
false source claim. Remaining decode work is the upstream enable source
and D0 hidden-load status; D29.4/IORD is only a guarded corroboration recheck.

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
  firmware-derived prediction is now physically closed: D94.13 belongs
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
- Known pull-up values: alternate-angle owner photography reads `6К2` on
  R87 and R88; R89 is partly socket-obscured but visually identical. The
  equipment list's separately designated `ДГШ5.087.009` group contains
  exactly three МЛТ-0,125 6.2 kΩ ±5% parts as corroboration. The readable
  target-board pair and identical third body close R87/R88/R89 as 6.2 kΩ.
- Unknown: the shared CS/enable upstream source and D0 hidden-branch status.
- Closed A3 source: D94.13 belongs to D105.3 qualified peripheral `/WR`.
  D5.27 is the distinct raw `IOWR_N` input to D7.10; a simultaneous
  operating-level capture is useful corroboration, not a missing join.
- Runnable-model disposition: the behavioral FDC now consumes the
  physical table's `/RE` and `/WE`. A3 consumes the owner-closed D105.3
  `iowr_n` conductor. Only the decoded enable and pulled-high A4 runtime
  behavior are simulation fits; Yosys/LVS preserves their measured
  physical boundary nets separately.
  The fast bus guard also forces A4 low on register 3 and proves D0
  asserts while both D93 strobes release, without assigning D0 a load.
- D5-D7 are electrically NC. Registered component-side photographs show
  only local copper departures, which continuity does not extend to a load.
- D4-D7 are program-inert: raw bits 4-7 remain one
  (open-collector released) at all 32 captured rows. D3 is the only
  closed active output; D0 is behaviorally active and destination-unknown.
- The traced `V3_RC` RC network is a negative cross-check here, not a
  replacement source for D94: its current nodes are `R17.1`, `C99.1`,
  and `D9.6`, with no D94 signal endpoint in JSON, DSN, or PCB.
- D94 is now classified as an FDC control/decode PROM because its proved
  functional outputs and D4's inert/back-bias route terminate at D93.
  It is not evidence for the separate
  shared-DRAM video-slot schedule.
- The 256-bit content ambiguity is closed. The remaining ambiguity is
  electrical: enable timing and the far ends/branches of output nets.
- The physical image is burnable, but that alone cannot release the FDC
  circuit or the replica PCB while those continuity boundaries remain.
- Do not reuse `.113` or `.117` as D94: those scans are guarded as
  `.106.103`-family evidence, not the processor-module `.092` content.
