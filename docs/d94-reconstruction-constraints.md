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

Address summary: all five address inputs are explicit continuity boundaries.
The former `BA11..BA15` mapping came from the original FDC scaffold's
same-as-D8 analogy, not from `.009` scan, photo, or owner continuity evidence.

| Pin | Role | Net | Source |
| ---: | --- | --- | --- |
| 10 | A0 | `BA0` | scan; direct owner continuity 2026-07-15 proves D94.10/A0 shares D93.5/A0 |
| 11 | A1 | `BA1` | scan; direct owner continuity 2026-07-15 proves D94.11/A1 shares D93.6/A1 and D27.8/A1 |
| 12 | A2 | `IORD` | scan sheet-1 full-resolution plus direct owner continuity 2026-07-15: D5.25 IORD runs into D7.9; D94.12/A2 joins D27.5/RD_N and D29.4. D29.4 conflicts with the older IOM_STATUS scan interpretation and is adopted from the physical board; recheck D29.4-D7.8, D29.4-D29.8, and D29.8-D27.5 later. D93.4 belongs only to D94.3 |
| 13 | A3 | `D94_A3_D104_X4_PULLUP` | direct owner continuity plus .009 factory identity and registered component/reflected-solder photos prove D94 address input pin13 reaches D104 К170УП2 fourth receiver input pin7 and R87.1; R87.2 enters the common +5 V rail. К170УП2 primary pinout confirms channel X4 is input7 -> output10 |
| 14 | A4 | `D94_A4_D101_Q0_PULLUP` | direct owner continuity plus .009 factory identity and registered component/reflected-solder photos prove D94.14/A4 reaches D101 К555КП12 Q0/pin7 and R88.1; R88.2 enters the common +5 V rail |
| 15 | E_N | `FDC_CS_N` | direct owner continuity 2026-07-15 proves D94 enable pin15 reaches D93 chip-select pin3, and explicitly proves D94 output pin2 is isolated from this conductor. The upstream source is retained separately for later continuity |

## Output Pins

| Pin | Role | Net | Captured activity | Source |
| ---: | --- | --- | --- | --- |
| 1 | D0 | `D94_D0_BOUNDARY` | asserts at rows 03, 07, 11, 15 | .009 factory drawing identifies R89 as the rightmost resistor adjacent to D94; registered component/reflected-solder photos join D94.1 to R89.1 and R89.2 to +5 V. No other trace or branch is observed; retain a guarded destination boundary because a hidden or missed branch cannot yet be excluded |
| 2 | D1 | `GND` | asserts at rows 04, 05, 06, 07, 08, 09, 10, 11, 20, 21, 22, 23, 24, 25, 26, 27 | scan; sheet-1 explicitly grounds CPU HOLD D1.13, system-controller BUSEN D5.22, and both always-enabled address-buffer OE pins D4.9/D107.9; sheet-2 control-bundle rail1 directly joins D39.2 and D43.1 to ground; July-2026 cross-photo full-package registration identifies the adjacent КМ555ТМ2 as D96 and continuous component copper directly ties D99.3 CLR_N to D96.7 GND; calibrated lower-FDC component copper directly joins R99.1 to D101.8 GND; two independent component photographs plus the factory position-159 detail show uninterrupted copper from D32.4 GND to D14.1; native sheet-2 power corner directly grounds rail E, including all DRAM pin-16 and strobe-pulldown endpoints |
| 3 | D2 | `FDC_RE_N` | asserts at rows 08, 09, 10, 24, 25, 26, 27 | direct owner continuity 2026-07-15 proves D94 output pin3 reaches D93 read-enable pin4, superseding the mirrored-pin photo interpretation |
| 4 | D3 | `FDC_WE_N` | asserts at rows 04, 05, 06, 20, 21, 22, 23 | direct owner continuity 2026-07-15 proves D94 output pin4 reaches D93 write-enable pin2, superseding the mirrored-pin photo interpretation; D93 pin1 is internally NC/back-bias but its separate socket pad is routed from D94.5 |
| 5 | D4 | `D94_D4` | invariant released | July-2026 exposed-socket photo PXL_20260710_202708344: independent affine D94/D93 fits identify D94.5 at (2477,1768.714) px and D93.1 at (2215,1810) px; uninterrupted front copper and the repaired socket entry join them. D93.1 is internally NC/back-bias on the controller but is not an unconnected PCB pad |
| 6 | D5 | `D94_D5` | invariant released | July-2026 registered component/solder local fits prove copper departs D94 output pin 6; far destination remains a boundary |
| 7 | D6 | `D94_D6` | invariant released | July-2026 registered component/solder fits prove copper departs D94 output pin 7; a suspected component-side handoff near (1915,1676) px is rejected because its two-sided projection lands on bare substrate, so the far destination remains a boundary |
| 9 | D7 | `D94_D7` | invariant released | July-2026 registered component/solder local fits prove copper departs D94 output pin 9; far destination remains a boundary |

## KiCad DSN Cross-check

The held routed DSN predates this provenance correction and still carries
the retired BA11..BA15 scaffold mapping. It is retained as stale-package
evidence, not independent proof of the D94 input sources.

| Pin | Role | DSN Net | Result |
| ---: | --- | --- | --- |
| 1 | D0 | - | missing in DSN |
| 2 | D1 | - | missing in DSN |
| 3 | D2 | - | missing in DSN |
| 4 | D3 | - | missing in DSN |
| 5 | D4 | - | missing in DSN |
| 6 | D5 | - | missing in DSN |
| 7 | D6 | - | missing in DSN |
| 8 | GND | `GND` | PASS |
| 9 | D7 | - | missing in DSN |
| 10 | A0 | `BA11` | STALE scaffold mapping |
| 11 | A1 | `BA12` | STALE scaffold mapping |
| 12 | A2 | `BA13` | STALE scaffold mapping |
| 13 | A3 | `BA14` | STALE scaffold mapping |
| 14 | A4 | `BA15` | STALE scaffold mapping |
| 15 | E_N | - | missing in DSN |
| 16 | VCC | `P5V` | PASS |

## KiCad PCB Cross-check

The authoritative source PCB includes accepted photo-traced outputs; the
older routed DSN remains a held engineering snapshot until cluster reroute.

| Pin | Role | PCB Net | Result |
| ---: | --- | --- | --- |
| 1 | D0 | `D94_D0_BOUNDARY` | PASS |
| 2 | D1 | `GND` | PASS |
| 3 | D2 | `FDC_RE_N` | PASS |
| 4 | D3 | `FDC_WE_N` | PASS |
| 5 | D4 | `D94_D4` | PASS |
| 6 | D5 | `D94_D5` | PASS |
| 7 | D6 | `D94_D6` | PASS |
| 8 | GND | `GND` | PASS |
| 9 | D7 | `D94_D7` | PASS |
| 10 | A0 | `BA0` | PASS |
| 11 | A1 | `BA1` | PASS |
| 12 | A2 | `IORD` | PASS |
| 13 | A3 | `D94_A3_D104_X4_PULLUP` | PASS |
| 14 | A4 | `D94_A4_D101_Q0_PULLUP` | PASS |
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
| Held routed DSN is identified with the retired input mapping | PASS | `kicad/juku.dsn` D94 pins |
| PCB agrees with current board-model D94 output nets | PASS | `kicad/juku.kicad_pcb` D94 footprint pads |
| `V3_RC` is present but not D94 enable/output evidence | PASS | board nodes `R17.1`, `C99.1`, `D9.6`; DSN/PCB D94 signal pins are not on `V3_RC` |
| Enable pin D94.15 is traced | PASS | board JSON nets |
| Enable pin15 is isolated from output pin2 | PASS | direct owner continuity; distinct board nets |
| Any D94 output net is traced | PASS | `D94_D0_BOUNDARY`, `GND`, `FDC_RE_N`, `FDC_WE_N`, `D94_D4`, `D94_D5`, `D94_D6`, `D94_D7` |
| Every D94 output pad has an explicit net/boundary | PASS | 8/8 output pins netted |
| Every unresolved D94 output has a photographed copper departure | PASS | component-side local-fit observations for pins 4, 5, 6, 7, 9 |
| Captured table asserts only D0-D3; D4-D7 stay released | PASS | exhaustive 32-row physical table classification |
| Minimized active-low equations reproduce all 256 captured bits | PASS | exhaustive address/output comparison against the physical image |
| Validated `.092` physical image exists and matches SHA256 | PASS | `ref/physical-proms/validated/d94_092.raw.bin` / `bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0` |
| Official .009 BOM/photo notes identify D94 as `.092` | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| Reused D94 refdes/tape-cluster history is guarded | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| `.113/.117` scans are guarded as not-D94 | PASS | `docs/re3-firmware-inspection.md` |
| Vendored programming disks have a guarded PROM-name/marker/exact-table audit | PASS | `docs/vendored-disk-catalog.md` |
| HDL adopts physical open-collector table | PASS | `hdl/devices.v::re3_prom_092` |
| HDL adopts measured D94 A0-A4 mapping | PASS | `hdl/juku_top.v`; BA0, BA1, IORD, D104.7/pull-up, D101.7/pull-up |
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
  enable pin15 reaches D93.3 CS, D1/pin2 reaches D99.8/GND,
  D2/pin3 reaches D93.4 /RE, and D3/pin4 reaches D93.2 /WE.
  Address inputs A0/A1/A2/A3/A4 reach BA0, BA1, IORD,
  D104.7+R87 pull-up, and D101.7+R88 pull-up respectively. The registered
  R89 pull-up closes D94.1 locally; D0's hidden load and D5-D7 destinations
  remain open while physical
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
  exposed-socket view closes D4/pin5 to the internally NC/back-bias
  D93.1 socket contact. D5/pin6 reaches a proved plated layer handoff
  at (2266,1828) px, but independent D93/D94 cross-side projections
  disagree by 54.2 px. D5-D7 retain far-destination boundaries. D0/pin1 is also
  destination-unresolved. The captured program keeps D4-D7 released
  at every row; D0 and the now-closed D3 are behaviorally active.
- The nearby `V3_RC` RC node is traced as `R17.1`, `C99.1`, and `D9.6`
  in board JSON/DSN, but D94 pin 15 and D3-D7 are not tied to it in
  board JSON, DSN, or PCB evidence. It cannot substitute for the missing
  D94 input/enable/output continuity.
- A 2026-07-11 high-resolution recheck projected D93.2 and D93.4 from
  the validated reflected D94 solder fit into the same source image.
  Neither pad shows an obvious solder-side fanout. Owner continuity now
  closes D94.15->D93.3 and D94.2->D99.8/GND, demonstrating why the
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
false source claim. Remaining decode work is the upstream enable source,
D0 hidden-load status, and guarded D29.4/IORD recheck.

## Minimized asserted-output logic

Define `S(Dn)=1` when the open-collector output is programmed active
(captured raw bit `0`), and define the shared qualifier
`Q = A4 | !A1 | !A0`. Exhaustive comparison against all 32 addresses
gives:

| Output | Exact asserted equation | Physical destination |
| --- | --- | --- |
| `S(D0)` | `!A4 & A1 & A0` | R89 pull-up / hidden-branch boundary |
| `S(D1)` | `A3 xor A2` | grounded through D99.8 |
| `S(D2)` | `A3 & !A2 & Q` | D93 `/RE` |
| `S(D3)` | `!A3 & A2 & Q` | D93 `/WE` |
| `S(D4..D7)` | `0` | physically routed but always released |

These equations sharpen, but do not replace, continuity evidence:

- D2 `/RE` and D3 `/WE` are mutually exclusive and select opposite
  one-hot states of A3/A2. This proves the PROM is a cycle-control
  decoder rather than an address-only register decoder.
- A2 is owner-measured to active-low `IORD`. Therefore, while `Q` is
  true on a selected FDC register cycle, the equations require A3=1
  for a read (`IORD`=0 -> `/RE` asserted) and A3=0 for a write
  (`IORD`=1 -> `/WE` asserted). A3 must consequently be polarity-
  equivalent to active-low `IOWR` during those cycles. This is an exact
  firmware-derived functional constraint, not proof that D94.13/D104.7
  shares copper directly with D5.27 `IOWR`.
- Test that prediction first with power-off continuity between
  D94.13/D104.7 and D5.27. If they are not continuous, capture both
  nodes during known FDC port reads and writes: their logic levels must
  still match at the PROM sampling point for the physical table to drive
  the proved D93 `/RE` and `/WE` inputs correctly.
- At BA1:BA0=`11` with A4 low, `Q` becomes false, both D93 strobes
  release, and D0 asserts independently of A3/A2. A live D0 branch
  probe should therefore target exactly that row condition.
  Conversely, A4 high restores the normal D93 read/write strobes at
  register 3. Because A4 cancels out of `Q` at every other BA1:BA0
  value, D101.Q0 is exactly a register-3 transfer-steering qualifier;
  this does not identify the alternate D0 load or D101's broader role.
- D4-D7 cannot change digital behavior for any captured address, even
  though their physical copper must remain preserved for 1:1 fidelity.
- The equations constrain A3's selected-cycle function but do not prove
  its electrical source; A4 semantics and D0's far endpoint likewise
  remain electrical/source boundaries rather than inferred nets.

## Address Space

D94 is a 32 x 8 PROM. The table below uses reader input indices A4..A0;
the board mapping is now A0=BA0, A1=BA1, A2=IORD, A3=D104.7/pull-up,
and A4=D101.7/pull-up. Unknown D5-D7 destinations do not make captured bits unknown.

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
  is grounded through D99.8; D2/pin3 reaches D93.4 RE; and D3/pin4
  reaches D93.2 WE. D4/pin5 reaches the internally NC/back-bias D93.1
  socket contact. D0/pin1 remains destination-unresolved.
- Known content: three matching reads including a power-cycled read yield
  raw SHA256 `bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0`.
- Known pull-up values: alternate-angle owner photography reads `6К2` on
  R87 and R88; R89 is partly socket-obscured but visually identical. The
  equipment list's separately designated `ДГШ5.087.009` group contains
  exactly three МЛТ-0,125 6.2 kΩ ±5% parts as corroboration. The readable
  target-board pair and identical third body close R87/R88/R89 as 6.2 kΩ.
- Unknown: the shared CS/enable upstream source, D0 hidden-branch status, and D5-D7
  far destinations remain unresolved behind explicit boundary nets.
- Firmware-derived prediction: D94 A3 must equal active-low `IOWR` on
  selected FDC cycles. Confirm by continuity to D5.27 or simultaneous
  operating-level capture; do not merge the nets from this constraint.
- Runnable-model disposition: the behavioral FDC now consumes the
  physical table's `/RE` and `/WE`. Its decoded enable, A3=`IOWR`, and
  pulled-high A4 sources are simulation-only fits; Yosys/LVS keeps the
  measured physical nets separate and unresolved.
  The fast bus guard also forces A4 low on register 3 and proves D0
  asserts while both D93 strobes release, without assigning D0 a load.
- D5-D7 are destination-unknown, not unused: registered component-side
  photographs prove copper leaves all three output pads.
- D4-D7 are physically wired but program-inert: raw bits 4-7 remain one
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
