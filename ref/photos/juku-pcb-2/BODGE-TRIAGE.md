# Processor-board physical evidence summary

This summary records the target board’s identity, source-supported topology,
and remaining physical boundaries.

## Target and evidence order

- Target: processor module `7.102.158`, documented by
  `ДГШ5.109.009 ПЭЗ` in `ref/Juku_official_chip_BOM.pdf`.
- Primary electrical evidence: the exact `.009` schematic photographs,
  official `.009` parts list, and owner continuity readings. The older `.006`
  scan under `ref/schematics/` requires revision reconciliation.
- Physical placement evidence: `es101_emaplaat.pdf`, the 52 owner board photos
  in this directory, and the 26 owner photographs of the authoritative
  `ДГШ5.109.009 СБ` assembly drawing under `ref/photos/dgsh5-109-009-sb/`.
- The current normalized endpoint record is `kicad/juku.board.json`.

## Settled identity corrections

The `.009` parts list establishes the FDC-era identities below. Sheet 3 uses
some of the same D94-D108 reference numbers as the older tape-era drawing; the
two assemblies must not be mixed.

| Ref | `.009` identity | Current conclusion |
| --- | --- | --- |
| D2 | КР556РТ4, program `.037` | validated physical table adopted from six independent accepted reads; the measured D30/D105/H handoff is in the model, while other source-risk nets remain open |
| D6 | КР556РТ4, program `.038` | validated physical table adopted from three independent matching reads; runnable joined-conductor timing remains bounded |
| D8 | К155РЕ3, program `.039` | validated physical table adopted from three independent matching reads; its contents select the ROM sockets in boot while D6 still supplies the functional enable |
| D9 | К555ИД7 | I/O chip-select decoder; physical D2 is not this decoder |
| D41-D43 | К555ИР16 | timing register plus two pixel serializers |
| D52 | К555КП14 | fifth DRAM/video address mux |
| D84-D91 | К565РУ5 | populated RAM bank on the `.158/.009` target |
| D92 | К555ЛЕ4 | memory/timing support logic |
| D93 | КР1818ВГ93 | FDC |
| D94 | К155РЕ3, program `.092` | validated physical table adopted from three independent matching reads; R87/R88/R89 pull up D94.4/D94.3/D94.2. The measured D94.1 branch includes R8 2 kΩ; its source-drawn WREQ continuation remains physically unverified. D4-D7 are NC and invariant released; D93.1 owns the visible open stub. |
| D95, D101 | К555КП12 | FDC quadrant multiplexers |
| D97, D99, D102 | К155АГ3 | FDC quadrant one-shots; owner photo shows the 8901 packages |
| D100 | КР580ВА87 | FDC drive-output buffer; D93 connects directly to DB0–DB7 |
| D105 | К155ЛА3 | official wait/MRD gate; modeled and routed from sheet-1 evidence |
| D106 | К555ИЕ7 | FDC quadrant counter |
| D107 | КР580ВА86 | low-address bus buffer |

The older `.006` drawing's D94-D108 are the К561 CMOS TAPE cluster. In the `.009` assembly,
sheet-3's D94-D108 refdes were re-used for the FDC-era parts. Consequently the
scanned `.113` and `.117` РЕ3 tables are not substitutes for D94 `.092`.

## D2 and D105 boundary

The D2 pin table from sheet 1 is:
`A0-A7=5/6/7/4/3/2/1/15`, `V1/V2=13/14`, and `D0=12`.

D105 two visible ЛА3 sections are `(9,10)->8` and `(4,5)->6`. Direct owner
continuity supersedes the false D2.12-to-D105.9 interpretation: D2.12 feeds
D30.2/R6 `READY_D`, while CPU D1.17 `DBIN` and pulled-up edge `H` feed
D105.9/.10; the second NAND drives D105.6 to D5.4. D2 V1/V2 are tied low.
D2 pad identities remain registered on both faces. The five
address routes remain modeled but lack a complete photo or exact `.009` source
chase; see `d2-d4-column-row-audit.json`. Repeated accepted captures preserve the physical `.037` table;
[the capture manifest](../../physical-proms/validated/d2_037.dump.json)
identifies the six independent reads and their aliases.
The factory symbol draws only D0/pin 12 on the RT4 output side; package outputs
pins 9-11 have no destination and are explicit no-connects in the board model.

The full-resolution sheet also proves three D2 address leads: `VIDEO CYCLE` to
A3/pin 4, `-XACK` to A5/pin 2, and `-WREQ` to A7/pin 15. D105's other
sections are `(1,2)->3` and `(12,13)->11` (tied-input MEMW inverter).
Owner continuity and the adopted model place D105.1 on D7.8/D6.15
`IO_CYCLE_H`, D105.2 on D13.4, and D105.3 on qualified peripheral `/WR`.
The source-drawn D1.24 WAIT-to-D105.1 path remains a separate continuity
question; see [the measurement shortlist](../../../docs/owner-measurement-shortlist.md).
The paired board photographs register A0/A1/A2/A4/A6 pad
locations but do not close their remote nets.

The three photographed К155АГ3 positions require 16-pin DIP footprints. This is consistent
with the traced D56 АГ3 pinout on sheet 2, whose RC terminals explicitly use
pins 14 and 15; the former 14-pin placement-only packages were physically
incomplete and are not valid substitutes.

## D30 READY/WAIT handoff

Sheet 1 and owner continuity establish both halves of D30 (`КМ555ТМ2`).
The active-low STB conductor from D38.8 joins pins 1 (`/CLR1`), 4 (`/PRE1`),
10 (`/PRE2`), and 12 (`D2`) with R5.2; R5.1 pulls it to +5 V. Pin 2 (`D1`)
has its separate R6 pull-up node, pin 3 (`CLK1`) receives `PHI2TTL`, and pin 5
(`Q1`) drives D1 READY/pin 23 through R29 1 kΩ. Owner continuity closes the
second half: D30.11 (`CLK2`) joins D13.4/D105.2/D11.20, D30.13 (`/CLR2`)
joins D105.11, and D30.8 (`/Q2`) drives D29.7. Pin 9 remains an explicit
no-connect. `docs/d30-section-b-scan-chase.md` records why the older scan alone
could not prove the two section-B routes; their target-board continuity is now
in the model. Other READY/WAIT release checks remain in the generated reports.

## Factory wire-link evidence

The conspicuous insulated wires are documented assembly links, not an
undocumented repair campaign. Owner continuity readings and the assembly
drawing agree on these endpoints:

The factory table has two different number spaces: `Провод` is the conductor
position within assembly item 155, while `А:N` is the number printed at both
PCB endpoints. Use both columns when identifying a link.

| Conductor position | Board point | Measured/guarded endpoints | Meaning/state |
| ---: | ---: | --- | --- |
| 3 | А:7 | D1.22 - D35.10 | PHI1 |
| 4 | А:8 | D5.1 - D38.8 | STSTB |
| 5 | А:9 | D1.19 - D38.12 | SYNC |
| 6 | А:10 | D41.13 - D50.1 | video/CPU mux select |
| 7 | А:11 | D7.1 - D92.13 | timing support path |
| 8 | А:12 | D13.2 - D37.4 | RAM output-enable path |
| 9 | А:13 | D13.1 - D92.1 | ROE support path |
| 10 | А:14 | D1.15 - D35.12 | PHI2 |
| 13 | А:19 | D5.26 - D7.2 | MEMW branch |
| 14 | А:20 | D3.10 - A23.1 - X3.3 | serial `S_TTL` path; owner read includes the installed X3 cable; enlarged sheet-1 review confirms the adjacent vertical package is D104, not D14 |
| 6 (keyboard item 153) | А:50 | D26.22 - A50.1 - X9.9 | CONTRDAT; D26.23 is a separate E8 boundary |
| 11 | А:17 | A17.1 - S1.1 | RES_RC, dedicated landing |
| 12 | А:18 | D98.7 - S1.2 | bracket-switch lead, no local PCB departure |

**11 / А:17:** Component photo 200358952 at `(914,1154)` and solder photo
200509593 at `(2145,1155)` show the dedicated tinned pad printed `17`.
Factory row 11 documents А:17 - S1:1, approximately 19 cm. It is modeled as
`A17.1` on `RES_RC`, near `(115.8,27.1)` mm using the adjacent
`(114.4,13.3)` mounting-hole transfer.

**12 / А:18:** Validated component and solder fits place the white
bracket-switch lead on D98.7 with no visible PCB-copper departure. Factory
row 12 documents А:18 - S1:2, approximately 3 cm. The model net is
`D98_Y3_S1_2`. The separate 220-ohm body below-left of D98 is unassigned,
not the А:17 link and not R94.

The settled wire links are represented in the board model with endpoint
provenance and guarded by `kicad/check_factory_wire_links.py`. Sheet-1 assembly
photos `114556899` and `114600417` separate board-point labels 17 and 18,
correcting the earlier combined “17/18” shorthand.
The sheets 2-5 connection table (`ДУБЛИКАТ` scan) documents both far ends on
switch S1. The component photo plus package fit closes `А:18` as D98.7, while
matching labeled component/solder views close `А:17` as a dedicated board pad.

Owner inspection and continuity identify R94 as the 10k pull-up immediately
above D28, from D28.11/D93.38 to +5 V; the video cable can obscure it.
The unassigned 220-ohm component below-left of D98 is separate from R94
and the white wire-18 connection at D98.7. Its retained photo observations
are in `r94-photo-exhaustion.json`; that record's R94 identification is superseded.

S1 itself is mounted on the top connector bracket, as shown both by sheet 1
and owner component photograph `PXL_20260710_200402344.jpg`; it is not a
two-pin PCB header. The PCB-side objects are the remote wire landings `А:17`
and `А:18`, with `А:18` at D98.7. The generated source PCB
excludes S1 from its footprint set and includes the physical `A17` one-pad
landing; the switch remains in the schematic as an off-board harness component.

The same physical distinction applies to the keyboard ribbon. Factory sheets
4-5 map PCB points A45..A58 in reverse order to bracket connector X9 pins
14..1. The source PCB therefore carries numbered `A45`..`A58` one-pad
landings at the photographed cable exit, while X9 is retained only in the
schematic harness. This preserves all existing D26 keyboard nets and the two
+5 V conductors without depicting the remote connector body on the PCB.

Factory sheet 2 likewise separates the X8 bracket connector from PCB points
A59..A62. The four numbered landings carry -12 V, +12 V, +5 V, and ground;
the schematic harness records the six 300 mm conductors, including the paired
+5 V and ground wires. X8 has no on-board connector footprint.

The X3 serial connector is also bracket-mounted. Registered component and
solder views show its twelve cable wires terminating in one PCB row labeled
A21..A32, while factory sheets 4-5 map those points to X3.1..X3.12. Sheet 1
also corrects two former reads: DTP is A31 (not 51), and SIN is A24 (not 33).
It proves all three D104 К170УП2 receivers: SIN 4->13, CTS 5->12, and DSR
6->11, closing D11 RxD/CTS/DSR. Exact `.009` sheet 1 and the assembly identify **R101** as the
120-ohm pull-up from A21/X3.1 to +5 V. **R104** is the separate 470-ohm
pull-up at D12.5/`X2_IRQ0`; installed resistance and remote continuity remain
open. See [the source correction](../../../docs/r101-r104-d12-exact-source-correction.md). Source junction dots tie A22/X3.2 to the same OC SOUT
node as A32/X3.12 and D12.3. A27/A28 show no solder-side copper departure and
are absent from the older circuit sheet. The source model retains X3.7/.8 as
cable-only harness nets. Owner continuity identifies X3.7 as signal ground on
CS00015; that does not establish the photographed target's A27 rail connection.
See [the serial handoff](../../../docs/serial-handoff.md) for this distinction.
The source-drawn OC SOUT bias network is also restored: assembly and owner
photos identify R18 as the diagonal 33k link from `S_OC` to `SER_TXD`/D3.11,
and R30 as the long vertical 33k link from `S_OC` to ground. Their fitted
10.16 mm and 12.7 mm footprints match the photographed terminals.
The same source block shows SER_TXD feeding both D3.11 and D3.9; D3.8 then
drives tied D12.1/.2 before D12.3 produces OC SOUT. That physical inverter
stage is represented in the model.

Sheet 1 also explicitly ties D10 PIC SP/EN pin 16 to the `A` (+5 V) rail,
selecting standalone master mode. Exact `.009` source evidence assigns IR0 to
X2.214 and IR1 to X2.218/D27 PB7, separately from the FDC conditioner. D11
RxRDY/TxRDY directly drive IR2/IR3; the off-sheet IR0/IR1 labels do not justify
a direct D93 INTRQ/DRQ assignment. See [the serial handoff](../../../docs/serial-handoff.md).

## Factory solder-side cuts and patches

The `ДГШ5.109.009 СБ` factory `Вид В` details document operations at D56,
D15, D14 and D11. The original close-ups `PXL_20260711_114626340.jpg`,
`114633498.jpg` and `114638730.MP.jpg` are preserved in the assembly-photo
archive. Only D15 explicitly says `Разрезать`; note 11 identifies position
150 as tubing fitted at solder locations. Position 159's material remains
unresolved. These are factory assembly instructions, but the drawing alone
does not prove every resulting electrical endpoint.

| Area | Accepted local evidence | Remaining boundary |
| --- | --- | --- |
| D15 | Auxiliary cut separates the D15.8/A2 and D15.9/A1 landings; the source model keeps those nets separate | Auxiliary-hole drill coordinates are not fabrication-qualified |
| D56 | Marked AG3 package is registered; D56.1/.9 are photo-grounded and D56.5/.12 functional nets are owner-closed | Position-159 material and auxiliary-annulus disposition |
| D14 | Local copper closes D32.4/GND to D14.1 and D14.4 to the fifth auxiliary annulus | Remote conductor, remaining traces and target-board continuity |
| D11 | Four component-side solder locations and auxiliary field are registered | Unique cross-face match, bridge, pin/net and remote endpoints |

The [factory modification report](../../../docs/factory-modification-disposition.md)
owns the source identities, fits, coordinates and detailed dispositions.
Preserve the resulting topology when reconstructing artwork; registration
coordinates alone do not qualify a trace or drill for fabrication.

## Placement conclusions retained

- Board outline: `310 x 266 mm` from the owner-measured physical target.
- The DRAM rows use roughly `11.25 mm` horizontal and `25 mm` vertical pitch.
- The `.158/.009` target populates D84-D91; empty D60-D83 footprints are real
  expansion sockets, not missing ICs from the official populated-parts list.
- D105 is horizontal below D13.
- The connector and mounting geometry is captured by the generated KiCad
  source; values and positions that remain uncertain are reported by the
  generated boundary/readiness documents.

## Release consequence

This evidence closes several old identity disputes, but it does not release the
PCB for fabrication. All four small-PROM contents are now preserved physical
truth; the measured D2/D30/D105 handoff is adopted, while D94/FDC
connectivity remains incomplete. The
[current inventory](../../../docs/unmodeled-footprint-inventory.md) identifies
four modeled FDC devices with untraced or continuity-boundary functional pins. D105 wait/MRD logic is modeled and routed; the FDC
cluster and other source-risk boundaries are not complete. See
`PLAN.md` and the generated reconstruction/unmodeled-footprint reports.
