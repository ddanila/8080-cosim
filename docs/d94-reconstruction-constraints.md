# D94 .092 reconstruction constraints

Status: **D94 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED**

This generated report records what the repo can currently prove about
the .009 FDC-era `D94` К155РЕ3 PROM (`ДГШ5.106.092`) before attempting
any reverse-engineered or burnable replacement table.

## Command

```sh
python3 scripts/report_d94_reconstruction_constraints.py
```

## Address / Enable Pins

Board identity: D94 type is `RE3_PROM_092`.

Address summary: D94.10-D94.14 map to `BA11..BA15` in the board JSON.

| Pin | Role | Net | Source |
| ---: | --- | --- | --- |
| 10 | A0 | `BA11` | scan |
| 11 | A1 | `BA12` | scan |
| 12 | A2 | `BA13` | scan |
| 13 | A3 | `BA14` | scan |
| 14 | A4 | `BA15` | scan |
| 15 | E_N | `D94_EN_BOUNDARY` | July-2026 registered component/solder local fits identify D94 enable pin 15 and exposed fanout, but the onward source cannot be uniquely followed across the adjacent tile |

## Output Pins

| Pin | Role | Net | Source |
| ---: | --- | --- | --- |
| 1 | D0 | `FDC_RE_N` | July-2026 two-sided local fit + continuous component copper |
| 2 | D1 | `FDC_CS_N` | July-2026 two-sided local fit + continuous component copper |
| 3 | D2 | `FDC_WE_N` | July-2026 two-sided local fit + continuous component copper |
| 4 | D3 | `D94_D3` | July-2026 registered component photo: continuous copper leaves D94 output pin 4 and reaches a distinct terminal via/layer handoff near board (236.74,96.30) mm; far-side destination remains a boundary |
| 5 | D4 | `D94_D4` | July-2026 registered component/solder local fits prove copper departs D94 output pin 5; far destination remains a boundary |
| 6 | D5 | `D94_D5` | July-2026 registered component/solder local fits prove copper departs D94 output pin 6; far destination remains a boundary |
| 7 | D6 | `D94_D6` | July-2026 registered component/solder fits prove copper departs D94 output pin 7; a suspected component-side handoff near (1915,1676) px is rejected because its two-sided projection lands on bare substrate, so the far destination remains a boundary |
| 9 | D7 | `D94_D7` | July-2026 registered component/solder local fits prove copper departs D94 output pin 9; far destination remains a boundary |

## KiCad DSN Cross-check

The routed DSN independently exposes only D94 power/ground and address
connections. It does not provide the missing enable/output nets.

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
| 10 | A0 | `BA11` | PASS |
| 11 | A1 | `BA12` | PASS |
| 12 | A2 | `BA13` | PASS |
| 13 | A3 | `BA14` | PASS |
| 14 | A4 | `BA15` | PASS |
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
| 10 | A0 | `BA11` | PASS |
| 11 | A1 | `BA12` | PASS |
| 12 | A2 | `BA13` | PASS |
| 13 | A3 | `BA14` | PASS |
| 14 | A4 | `BA15` | PASS |
| 15 | E_N | `D94_EN_BOUNDARY` | PASS |
| 16 | VCC | `P5V` | PASS |

## Current Evidence Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Board identity names D94 as `.092`, not stale `.113` | PASS | `kicad/juku.board.json` type `RE3_PROM_092` |
| Address pins D94.10-D94.14 are traced | PASS | board JSON nets |
| DSN agrees on D94 power/address and lacks output nets | PASS | `kicad/juku.dsn` D94 pins |
| PCB agrees with current board-model D94 output nets | PASS | `kicad/juku.kicad_pcb` D94 footprint pads |
| `V3_RC` is present but not D94 enable/output evidence | PASS | board nodes `R17.1`, `C99.1`, `D9.6`; DSN/PCB D94 signal pins are not on `V3_RC` |
| Enable pin D94.15 is traced | FAIL | board JSON nets |
| Enable pad/fanout is represented as an unresolved boundary | PASS | `D94_EN_BOUNDARY` |
| Any D94 output net is traced | PASS | `FDC_RE_N`, `FDC_CS_N`, `FDC_WE_N`, `D94_D3`, `D94_D4`, `D94_D5`, `D94_D6`, `D94_D7` |
| Every D94 output pad has an explicit net/boundary | PASS | 8/8 output pins netted |
| Every unresolved D94 output has a photographed copper departure | PASS | component-side local-fit observations for pins 4, 5, 6, 7, 9 |
| `.092` firmware artifact exists | FAIL | `ref/firmware/` has no `.092` artifact |
| Repository-wide `.092` artifact filename exists | FAIL | no `.092` / `106.092` artifact filename under ref/roms/media/docs/hdl/kicad/scripts/sync |
| Official .009 BOM/photo notes identify D94 as `.092` | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| Reused D94 refdes/tape-cluster history is guarded | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| `.113/.117` scans are guarded as not-D94 | PASS | `docs/re3-firmware-inspection.md` |
| Vendored programming disks have a guarded PROM-name/marker audit | PASS | `docs/vendored-disk-catalog.md` |
| HDL placeholder is explicitly inert | PASS | `hdl/devices.v::re3_prom_092` |
| `juku_top` connects the three accepted local FDC controls | PASS | `hdl/juku_top.v` |
| Video slot audit does not rely on D94 | PASS | `docs/video-slot-timing-audit.md` |
| D94 row alias with PIT2/FDC groups is guarded | PASS | ports `18-1B` and `1C-1F` both select D94 row `00011`; D9.Y6/Y7 distinguish the groups |

## Textual / Photo Survey Leads

- The official .009 BOM trail identifies the FDC-era D94 as the second
  К155РЕ3, programmed as `ДГШ5.106.092`.
- Earlier D94 references in the sheet-3/tape-cluster survey are known
  refdes reuse history, not evidence for the FDC-era timing PROM.
- The guarded firmware inspection establishes that `.113/.117` belong
  to the `.106.103`-family owner-scan evidence and are not a burnable
  D94 `.092` substitute.
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
  still do not provide pin 15's source, D3-D7 destinations, or PROM contents.
- Registered component-side local fits show copper departing every remaining
  output pad D3-D7 (pins 4-7 and 9), now represented by explicit boundary
  nets. Their far destinations remain unknown,
  but none may be reconstructed as an unused/NC PROM output.
- The nearby `V3_RC` RC node is traced as `R17.1`, `C99.1`, and `D9.6`
  in board JSON/DSN, but D94 pin 15 and the remaining D3-D7 are not tied to it in
  board JSON, DSN, or PCB evidence. It cannot substitute for the missing
  D94 enable/output continuity.
- A 2026-07-11 high-resolution recheck projected D93.2 and D93.4 from
  the validated reflected D94 solder fit into the same source image.
  Neither pad shows an obvious solder-side fanout, while D94.15 still
  cannot be followed to a unique endpoint across the adjacent tile.
  This is useful negative photo evidence, not a substitute for continuity.

## Control-feasibility constraint

The three proved outputs create a circuit-level constraint that the PROM
dump alone cannot resolve:

- D94's five proved row inputs are only buffered address bits `BA11..BA15`.
- D94.D0 and D94.D2 terminate at the separate active-low D93 `/RE` and
  `/WE` inputs. An FDC register must support both reads and writes at the
  same port address.
- A 32 x 8 combinational PROM row selected only by those five address bits
  has the same D0/D2 values for a read and a write to that address. Its one
  common active-low enable cannot independently select the read output on
  one cycle and the write output on the other.
- Therefore the currently visible direct D94-to-D93 copper is not a complete
  functional explanation. At least one missing fact must exist: additional
  wired/open-collector branches at D93.2/.4, a direction-dependent D94.15
  network with further gating, a wrong address/pin premise, or another
  target-revision circuit detail hidden by the photographs.

This does not refute the accepted local copper paths. It proves that a
`.092` byte dump by itself is insufficient to release the FDC interface;
continuity from D93.2, D93.4, and D94.15 must include every branch, not just
the visible local segment.

## Port-group row constraint

On the 8080 I/O cycle the port byte is mirrored onto the buffered high
address byte used by this decode cluster. D94 sees `BA11..BA15`, i.e.
port bits 3..7, while D9 additionally sees `BA10` (port bit 2). Therefore:

| Port group | D9 output | D94 row BA15..BA11 |
| --- | --- | --- |
| `18-1B` PIT2 | `D9.Y6` / `CS_D57` | `00011` |
| `1C-1F` FDC | `D9.Y7` / `CS_FDC` | `00011` |

D94 cannot distinguish those two groups from its five row inputs. Its
pin-15 enable, or an equivalent missing branch, must therefore carry the
D9 group distinction if D94 is to affect only the FDC. This makes
`CS_FDC` a strong continuity candidate for D94.15, but not a promoted net:
the photographs do not yet prove that connection. Even if D94.15 is
`CS_FDC`, the common enable still cannot distinguish `/RE` from `/WE`;
direction-dependent branches at D93.2/.4 remain required.

## Address Space

D94 is a 32 x 8 PROM. The address pins are traced, so the reachable
rows are mechanically known, but every row byte is still unknown because
the `.092` programming table/dump is absent and D3-D7 destinations remain unknown.

| Row | BA15 | BA14 | BA13 | BA12 | BA11 | D7..D0 |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 00 | 0 | 0 | 0 | 0 | 0 | unknown |
| 01 | 0 | 0 | 0 | 0 | 1 | unknown |
| 02 | 0 | 0 | 0 | 1 | 0 | unknown |
| 03 | 0 | 0 | 0 | 1 | 1 | unknown |
| 04 | 0 | 0 | 1 | 0 | 0 | unknown |
| 05 | 0 | 0 | 1 | 0 | 1 | unknown |
| 06 | 0 | 0 | 1 | 1 | 0 | unknown |
| 07 | 0 | 0 | 1 | 1 | 1 | unknown |
| 08 | 0 | 1 | 0 | 0 | 0 | unknown |
| 09 | 0 | 1 | 0 | 0 | 1 | unknown |
| 10 | 0 | 1 | 0 | 1 | 0 | unknown |
| 11 | 0 | 1 | 0 | 1 | 1 | unknown |
| 12 | 0 | 1 | 1 | 0 | 0 | unknown |
| 13 | 0 | 1 | 1 | 0 | 1 | unknown |
| 14 | 0 | 1 | 1 | 1 | 0 | unknown |
| 15 | 0 | 1 | 1 | 1 | 1 | unknown |
| 16 | 1 | 0 | 0 | 0 | 0 | unknown |
| 17 | 1 | 0 | 0 | 0 | 1 | unknown |
| 18 | 1 | 0 | 0 | 1 | 0 | unknown |
| 19 | 1 | 0 | 0 | 1 | 1 | unknown |
| 20 | 1 | 0 | 1 | 0 | 0 | unknown |
| 21 | 1 | 0 | 1 | 0 | 1 | unknown |
| 22 | 1 | 0 | 1 | 1 | 0 | unknown |
| 23 | 1 | 0 | 1 | 1 | 1 | unknown |
| 24 | 1 | 1 | 0 | 0 | 0 | unknown |
| 25 | 1 | 1 | 0 | 0 | 1 | unknown |
| 26 | 1 | 1 | 0 | 1 | 0 | unknown |
| 27 | 1 | 1 | 0 | 1 | 1 | unknown |
| 28 | 1 | 1 | 1 | 0 | 0 | unknown |
| 29 | 1 | 1 | 1 | 0 | 1 | unknown |
| 30 | 1 | 1 | 1 | 1 | 0 | unknown |
| 31 | 1 | 1 | 1 | 1 | 1 | unknown |

## Reconstruction Boundary

- Known: D94 is present in the .009 FDC quadrant and its five address
  inputs are wired to `BA11..BA15`.
- Known output destinations: D0-D2 drive the private D93 read/select/write
  controls `FDC_RE_N`, `FDC_CS_N`, and `FDC_WE_N`.
- Unknown: D94 pin 15's upstream source and D3-D7 far destinations remain
  unresolved behind explicit boundary nets, and no
  `ДГШ5.106.092` programming table or dump is present under the
  repository artifact scan.
- D3-D7 are destination-unknown, not unused: registered component-side
  photographs prove copper leaves all five output pads.
- The traced `V3_RC` RC network is a negative cross-check here, not a
  replacement source for D94: its current nodes are `R17.1`, `C99.1`,
  and `D9.6`, with no D94 signal endpoint in JSON, DSN, or PCB.
- D94 is now classified as an FDC control/decode PROM because its only
  proved outputs terminate at D93. It is not evidence for the separate
  shared-DRAM video-slot schedule.
- Content ambiguity alone is 256 unknown bits (`2^256` possible 32-byte
  PROM tables) before even assigning those bits to physical destination
  nets or enable timing.
- Therefore a burnable D94 image is not derivable from current repo
  evidence. The correct next automatic action is to keep this constraint
  report fresh; the next data-unlocking action is an owner dump or a
  recovered programming-disk `.092` table.
- Do not reuse `.113` or `.117` as D94: those scans are guarded as
  `.106.103`-family evidence, not the processor-module `.092` content.
