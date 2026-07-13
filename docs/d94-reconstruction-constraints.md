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
| 10 | A0 | `D94_A0_BOUNDARY` | D94 .009 input continuity boundary: the retired BA11 assignment came only from the July-2026 FDC scaffold's same-as-D8 assumption, not a scan, photo trace, or owner measurement |
| 11 | A1 | `D94_A1_BOUNDARY` | D94 .009 input continuity boundary: the retired BA12 assignment came only from the July-2026 FDC scaffold's same-as-D8 assumption, not a scan, photo trace, or owner measurement |
| 12 | A2 | `D94_A2_BOUNDARY` | D94 .009 input continuity boundary: the retired BA13 assignment came only from the July-2026 FDC scaffold's same-as-D8 assumption, not a scan, photo trace, or owner measurement |
| 13 | A3 | `D94_A3_BOUNDARY` | D94 .009 input continuity boundary: the retired BA14 assignment came only from the July-2026 FDC scaffold's same-as-D8 assumption, not a scan, photo trace, or owner measurement |
| 14 | A4 | `D94_A4_BOUNDARY` | D94 .009 input continuity boundary: the retired BA15 assignment came only from the July-2026 FDC scaffold's same-as-D8 assumption, not a scan, photo trace, or owner measurement |
| 15 | E_N | `D94_EN_BOUNDARY` | July-2026 registered component/solder local fits identify D94 enable pin 15 and exposed fanout, but the onward source cannot be uniquely followed across the adjacent tile |

## Output Pins

| Pin | Role | Net | Captured activity | Source |
| ---: | --- | --- | --- | --- |
| 1 | D0 | `FDC_RE_N` | asserts at rows 03, 07, 11, 15 | July-2026 two-sided local fit + continuous component copper |
| 2 | D1 | `FDC_CS_N` | asserts at rows 04, 05, 06, 07, 08, 09, 10, 11, 20, 21, 22, 23, 24, 25, 26, 27 | July-2026 two-sided local fit + continuous component copper |
| 3 | D2 | `FDC_WE_N` | asserts at rows 08, 09, 10, 24, 25, 26, 27 | July-2026 two-sided local fit + continuous component copper |
| 4 | D3 | `D94_D3` | asserts at rows 04, 05, 06, 20, 21, 22, 23 | July-2026 registered component photo: continuous copper leaves D94 output pin 4 and reaches a distinct terminal via/layer handoff near board (236.74,96.30) mm; far-side destination remains a boundary |
| 5 | D4 | `D94_D4` | invariant released | July-2026 registered component/solder local fits prove copper departs D94 output pin 5; far destination remains a boundary |
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
| 1 | D0 | `FDC_RE_N` | PASS |
| 2 | D1 | `FDC_CS_N` | PASS |
| 3 | D2 | `FDC_WE_N` | PASS |
| 4 | D3 | `D94_D3` | PASS |
| 5 | D4 | `D94_D4` | PASS |
| 6 | D5 | `D94_D5` | PASS |
| 7 | D6 | `D94_D6` | PASS |
| 8 | GND | `GND` | PASS |
| 9 | D7 | `D94_D7` | PASS |
| 10 | A0 | `D94_A0_BOUNDARY` | PASS |
| 11 | A1 | `D94_A1_BOUNDARY` | PASS |
| 12 | A2 | `D94_A2_BOUNDARY` | PASS |
| 13 | A3 | `D94_A3_BOUNDARY` | PASS |
| 14 | A4 | `D94_A4_BOUNDARY` | PASS |
| 15 | E_N | `D94_EN_BOUNDARY` | PASS |
| 16 | VCC | `P5V` | PASS |

## Current Evidence Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Board identity names D94 as `.092`, not stale `.113` | PASS | `kicad/juku.board.json` type `RE3_PROM_092` |
| Every D94 address input is explicitly accounted | PASS | board JSON nets |
| Every D94 address input has reviewed two-sided photo coordinates | PASS | local-package-fit measurement rows for pins 10, 11, 12, 13, 14 |
| D94 address input sources are traced | FAIL | pins 10-14 remain continuity boundaries |
| Retired D94 BA11..BA15 mapping is absent from the source model | PASS | board JSON BA nets |
| Held routed DSN is identified with the retired input mapping | PASS | `kicad/juku.dsn` D94 pins |
| PCB agrees with current board-model D94 output nets | PASS | `kicad/juku.kicad_pcb` D94 footprint pads |
| `V3_RC` is present but not D94 enable/output evidence | PASS | board nodes `R17.1`, `C99.1`, `D9.6`; DSN/PCB D94 signal pins are not on `V3_RC` |
| Enable pin D94.15 is traced | FAIL | board JSON nets |
| Enable pad/fanout is represented as an unresolved boundary | PASS | `D94_EN_BOUNDARY` |
| Any D94 output net is traced | PASS | `FDC_RE_N`, `FDC_CS_N`, `FDC_WE_N`, `D94_D3`, `D94_D4`, `D94_D5`, `D94_D6`, `D94_D7` |
| Every D94 output pad has an explicit net/boundary | PASS | 8/8 output pins netted |
| Every unresolved D94 output has a photographed copper departure | PASS | component-side local-fit observations for pins 4, 5, 6, 7, 9 |
| Captured table asserts only D0-D3; D4-D7 stay released | PASS | exhaustive 32-row physical table classification |
| Validated `.092` physical image exists and matches SHA256 | PASS | `ref/physical-proms/validated/d94_092.raw.bin` / `bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0` |
| Official .009 BOM/photo notes identify D94 as `.092` | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| Reused D94 refdes/tape-cluster history is guarded | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| `.113/.117` scans are guarded as not-D94 | PASS | `docs/re3-firmware-inspection.md` |
| Vendored programming disks have a guarded PROM-name/marker audit | PASS | `docs/vendored-disk-catalog.md` |
| HDL adopts physical open-collector table | PASS | `hdl/devices.v::re3_prom_092` |
| HDL keeps D94 A0-A4 off the retired BA mapping | PASS | `hdl/juku_top.v` boundary vector |
| `juku_top` connects the three accepted local FDC controls | PASS | `hdl/juku_top.v` |
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
  `.037`/`.038`/`.039`/`.092`/RT4/RE3 marker. An unidentified binary
  table remains possible, so this is negative search evidence rather than
  proof that the programming bytes are absent from every unlabelled blob.
- A 2026-07-13 indexed-web search for exact `ДГШ5.106.092`,
  `ДГШ5.106.092 Juku`, `Juku К155РЕ3 092 dump`, and
  `Juku ES-101 floppy PROM D94` returned no programming table, binary,
  scan, repository, or collector listing for this artifact. Generic Juku
  history and generic К155РЕ3 references do not constrain its contents.
- Local two-sided fits and continuous copper now establish D0-D2 as the
  private `FDC_RE_N`, `FDC_CS_N`, and `FDC_WE_N` rails. Textual sources
  still do not provide A0-A4, pin 15, or D3-D7 destinations; physical
  captures now provide the PROM contents.
- Git history proves the former A0-A4=`BA11..BA15` assignment entered in
  commit `ed69b9d` as an FDC scaffold explicitly described as the same
  convention as D8. No `.009` electrical source or owner measurement was
  cited. The source PCB now represents pins 10-14 as measurement boundaries.
- Validated local package fits now preserve exact original-image coordinates
  for D94.10-.14 on both sides. Component copper is socket-obscured and
  the solder crop has no uniquely traceable remote endpoints, so these are
  reviewed measurement records rather than promoted electrical nets.
- Registered component-side local fits show copper departing every remaining
  output pad D3-D7 (pins 4-7 and 9), now represented by explicit boundary
  nets. Their far destinations remain unknown, so none may be removed from
  the PCB as NC. The captured program nevertheless keeps D4-D7 released at
  every row; only D3 among those five can affect circuit behavior.
- The nearby `V3_RC` RC node is traced as `R17.1`, `C99.1`, and `D9.6`
  in board JSON/DSN, but D94 inputs A0-A4, pin 15, and D3-D7 are not tied to it in
  board JSON, DSN, or PCB evidence. It cannot substitute for the missing
  D94 input/enable/output continuity.
- A 2026-07-11 high-resolution recheck projected D93.2 and D93.4 from
  the validated reflected D94 solder fit into the same source image.
  Neither pad shows an obvious solder-side fanout, while D94.15 still
  cannot be followed to a unique endpoint across the adjacent tile.
  This is useful negative photo evidence, not a substitute for continuity.

## Input-mapping correction and control constraint

The three proved output destinations and physical table reject the old
scaffold mapping as a closed physical claim:

- D94.D0 and D94.D2 terminate at the separate active-low D93 `/RE` and
  `/WE` inputs. An FDC register must support both reads and writes at the
  same port address.
- If A0-A4 were only `BA11..BA15`, the same PROM row would drive both cycle
  directions and could not independently select `/RE` versus `/WE`.
- That mapping was never measured; it was copied by analogy from D8. The
  contradiction therefore narrows the next work to the actual D94 input
  sources, plus any wired/open-collector branches at D93.2/.4 and pin 15.

This does not refute the accepted local D94-to-D93 copper. It removes a
false source claim and makes the required measurement explicit: map pins
10-15 and every branch from D93.2/.4 before assigning row semantics.

## Address Space

D94 is a 32 x 8 PROM. The table below uses reader input indices A4..A0;
it intentionally makes no claim about their board signal sources. Unknown
input wiring or D3-D7 destinations do not make captured bits unknown.

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

- Known: D94 is present in the .009 FDC quadrant; all five address input
  pads are modeled, but their remote sources are not yet known.
- Known output destinations: D0-D2 drive the private D93 read/select/write
  controls `FDC_RE_N`, `FDC_CS_N`, and `FDC_WE_N`.
- Known content: three matching reads including a power-cycled read yield
  raw SHA256 `bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0`.
- Unknown: D94 A0-A4/pins 10-14, pin 15's upstream source, and D3-D7 far
  destinations remain unresolved behind explicit boundary nets.
- D3-D7 are destination-unknown, not unused: registered component-side
  photographs prove copper leaves all five output pads.
- D4-D7 are physically wired but program-inert: raw bits 4-7 remain one
  (open-collector released) at all 32 captured rows. D3 is the only
  behaviorally active output whose far destination is still unknown.
- The traced `V3_RC` RC network is a negative cross-check here, not a
  replacement source for D94: its current nodes are `R17.1`, `C99.1`,
  and `D9.6`, with no D94 signal endpoint in JSON, DSN, or PCB.
- D94 is now classified as an FDC control/decode PROM because its only
  proved outputs terminate at D93. It is not evidence for the separate
  shared-DRAM video-slot schedule.
- The 256-bit content ambiguity is closed. The remaining ambiguity is
  electrical: enable timing and the far ends/branches of output nets.
- The physical image is burnable, but that alone cannot release the FDC
  circuit or the replica PCB while those continuity boundaries remain.
- Do not reuse `.113` or `.117` as D94: those scans are guarded as
  `.106.103`-family evidence, not the processor-module `.092` content.
