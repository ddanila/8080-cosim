# Processor-board physical evidence summary

This legacy filename is retained because generated reports refer to it. The
content is a settled evidence summary, not an experiment diary. Historical
guesses that were contradicted by the official `.009` parts list, schematics,
assembly drawing, or owner continuity measurements have been removed.

## Target and evidence order

- Target: processor module `7.102.158`, documented by
  `ДГШ5.109.009 ПЭЗ` in `ref/Juku_official_chip_BOM.pdf`.
- Primary electrical evidence: the three schematic sheets in
  `ref/schematics/`, the official parts list, and owner continuity readings.
- Physical placement evidence: `es101_emaplaat.pdf`, the 50 owner board photos
  in this directory, and the 26 owner photographs of the authoritative
  `ДГШ5.109.009 СБ` assembly drawing under `ref/photos/dgsh5-109-009-sb/`.
- The current normalized endpoint record is `kicad/juku.board.json`.

## Settled identity corrections

The `.009` parts list establishes the FDC-era identities below. Sheet 3 uses
some of the same D94-D108 reference numbers as the older tape-era drawing; the
two assemblies must not be mixed.

| Ref | `.009` identity | Current conclusion |
| --- | --- | --- |
| D2 | КР556РТ4, program `.037` | validated physical table adopted from four independent accepted reads; remaining work is the D30/H WAIT edge, not PROM content |
| D6 | КР556РТ4, program `.038` | validated physical table adopted from three independent matching reads; runnable joined-conductor timing remains bounded |
| D8 | К155РЕ3, program `.039` | validated physical table adopted from three independent matching reads; its contents select the ROM sockets in boot while D6 still supplies the functional enable |
| D9 | К555ИД7 | I/O chip-select decoder; physical D2 is not this decoder |
| D41-D43 | К555ИР16 | timing register plus two pixel serializers |
| D52 | К555КП14 | fifth DRAM/video address mux |
| D84-D91 | К565РУ5 | populated RAM bank on the `.158/.009` target |
| D92 | К555ЛЕ4 | memory/timing support logic |
| D93 | КР1818ВГ93 | FDC |
| D94 | К155РЕ3, program `.092` | validated physical table adopted from three independent matching reads; input pins 10-14, enable pin 15, and output D3-D7 destinations remain open; D4-D7 are invariant released in the adopted table |
| D95, D101 | К555КП12 | FDC quadrant multiplexers |
| D97, D99, D102 | К155АГ3 | FDC quadrant one-shots; owner photo shows the 8901 packages |
| D100 | КР580ВА87 | FDC data-bus buffer |
| D105 | К155ЛА3 | official wait/MRD gate; modeled and routed from sheet-1 evidence |
| D106 | К555ИЕ7 | FDC quadrant counter |
| D107 | КР580ВА86 | low-address bus buffer |

Required compact identity markers: **D2 = РТ4 .037**, **D6 = .038**,
**D94 = К155РЕ3 #2**, **progr. .092**, and **D105 = К155ЛА3**.

The drawing's D94-D108 are the К561 CMOS TAPE cluster. In the `.009` assembly,
sheet-3's D94-D108 refdes were re-used for the FDC-era parts. Consequently the
scanned `.113` and `.117` РЕ3 tables are not substitutes for D94 `.092`.

## D2 and D105 boundary

The D2 pin table from sheet 1 is:
`A0-A7=5/6/7/4/3/2/1/15`, `V1/V2=13/14`, and `D0=12`.

D105 two visible ЛА3 sections are `(9,10)->8` and `(4,5)->6`. Direct owner
continuity supersedes the false D2.12-to-D105.9 interpretation: D2.12 feeds
D30.2/R6 `READY_D`, while CPU D1.17 `DBIN` and pulled-up edge `H` feed
D105.9/.10; the second NAND drives D105.6 to D5.4. D2 V1/V2 are tied low.
The July-2026 paired
D2 and D4 solder fits trace D2 pins 1/3/5/6/7 to D4 pins 1/3/5/6/7
(`A10/A14/A12/A15/A9`). All D2 inputs are now modeled and routed in the
authoritative source PCB. Three matching reads, including a full power cycle,
preserve the physical `.037` table.
The factory symbol draws only D0/pin 12 on the RT4 output side; package outputs
pins 9-11 have no destination and are explicit no-connects in the board model.

The full-resolution sheet also proves three D2 address leads: `VIDEO CYCLE` to
A3/pin 4, `-XACK` to A5/pin 2, and `-WREQ` to A7/pin 15. It shows D105's other
two sections as `(1,2)->3` (D13.4 and MWR inputs) and `(12,13)->11` (tied-input
MEMW inverter). The paired board photographs subsequently close A0/A1/A2/A4/A6.
Only D0 is drawn on the factory symbol; D1-D3/pins 11/10/9 are explicit
no-connects.

The three photographed К155АГ3 positions require 16-pin DIP footprints. This is consistent
with the traced D56 АГ3 pinout on sheet 2, whose RC terminals explicitly use
pins 14 and 15; the former 14-pin placement-only packages were physically
incomplete and are not valid substitutes.

## D30 READY boundary

Sheet 1 proves the first half of D30 (`КМ555ТМ2`) rather than merely showing a
placement: pins 4 (`/PRE`) and 2 (`D`) are pulled high, pin 3 (`CLK`) receives
`PHI2TTL`, pin 1 (`/CLR`) receives `-SSTB`, and pin 5 (`Q`) drives D1 READY/pin
23 through R29 1 kΩ. This section and R5/R6/R29 are now in the pin-level board
model. The second half, pins 8-13, is present and visibly wired near the
D105/select-rail area, but its crossing rails are not yet resolved end-to-end;
that half remains an explicit design-release boundary.

## Factory wire-link evidence

The conspicuous insulated wires are documented assembly links, not an
undocumented repair campaign. Owner continuity readings and the assembly
drawing agree on these endpoints:

The factory table has two different number spaces: `Провод` is the conductor
position within assembly item 155, while `А:N` is the number printed at both
PCB endpoints. Earlier shorthand called the latter a "wire number"; the
explicit columns below remove that ambiguity.

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
| - | D26.23 - X9.9 | keyboard/tape connector line |
| 11 / А:17 | Component photo 200358952 at `(914,1154)` and solder photo 200509593 at `(2145,1155)` show the same dedicated tinned pad printed `17`; sheets 2-5 row 11 documents А:17 - S1:1, ~19 cm | promoted as `A17.1` on `RES_RC`; board position approximately `(115.8,27.1)` mm from the adjacent `(114.4,13.3)` mounting-hole transfer |
| 12 / А:18 | Validated component and solder fits place the white bracket-switch lead on D98.7 and show no PCB-copper departure from that pad; sheets 2-5 row 12 documents А:18 - S1:2, ~3 cm | promoted as `D98_Y3_S1_2`; the photographed 220-ohm part is the separately placed R94 below-left of D98, not the А:17 link |

The settled wire links are represented in the board model with endpoint
provenance and guarded by `kicad/check_factory_wire_links.py`. Sheet-1 assembly
photos `114556899` and `114600417` separate board-point labels 17 and 18,
correcting the earlier combined “17/18” shorthand.
The sheets 2-5 connection table (`ДУБЛИКАТ` scan) documents both far ends on
switch S1. The component photo plus package fit closes `А:18` as D98.7, while
matching labeled component/solder views close `А:17` as a dedicated board pad.

The `.009` assembly drawing identifies the vertical axial part below-left of
D98 as R94, and its photographed colour code gives 220 ohms. The registered
D98 component fit and uninterrupted visible copper close R94's upper terminal
to D98.3 (`D98_Y1_R94`). R94's lower terminal remains unresolved; the source
PCB therefore assigns only R94.1 and deliberately leaves R94.2 without a net.
This resistor is separate from the white wire-18 connection at D98.7.

S1 itself is mounted on the top connector bracket, as shown both by sheet 1
and owner component photograph `PXL_20260710_200402344.jpg`; it is not a
two-pin PCB header. The PCB-side objects are the remote wire landings `А:17`
and `А:18`, with `А:18` now proved at D98.7. The generated source PCB now
excludes S1 from its footprint set and includes the physical `A17` one-pad
landing; the switch remains in the schematic as an off-board harness component.

The same physical distinction applies to the keyboard ribbon. Factory sheets
4-5 map PCB points A45..A58 in reverse order to bracket connector X9 pins
14..1. The source PCB therefore carries numbered `A45`..`A58` one-pad
landings at the photographed cable exit, while X9 is retained only in the
schematic harness. This preserves all existing D26 keyboard nets and the two
+5 V conductors without depicting the remote connector body on the PCB.

Factory sheet 2 likewise separates the X8 bracket connector from PCB points
A59..A62. The four numbered landings now carry -12 V, +12 V, +5 V, and ground;
the schematic harness records the six 300 mm conductors, including the paired
+5 V and ground wires. The former provisional six-pad on-board X8 connector is
therefore removed.

The X3 serial connector is also bracket-mounted. Registered component and
solder views show its twelve cable wires terminating in one PCB row labeled
A21..A32, while factory sheets 4-5 map those points to X3.1..X3.12. Sheet 1
also corrects two former reads: DTP is A31 (not 51), and SIN is A24 (not 33).
It proves all three D104 К170УП2 receivers: SIN 4->13, CTS 5->12, and DSR
6->11, closing D11 RxD/CTS/DSR. The same sheet and photo identify R104 as the
120-ohm pull-up from A21/X3.1 to +5 V; its fitted 12.7 mm-pitch footprint now
replaces that boundary. Source junction dots tie A22/X3.2 to the same OC SOUT
node as A32/X3.12 and D12.3. A27/A28 show no solder-side copper departure and
are absent from the older circuit sheet, so their installed X3.7/.8 wires are
intentional cable-only reserved contacts rather than missing PCB traces.
The source-drawn OC SOUT bias network is also restored: assembly and owner
photos identify R18 as the diagonal 33k link from `S_OC` to `SER_TXD`/D3.11,
and R30 as the long vertical 33k link from `S_OC` to ground. Their fitted
10.16 mm and 12.7 mm footprints match the photographed terminals.
The same source block shows SER_TXD feeding both D3.11 and D3.9; D3.8 then
drives tied D12.1/.2 before D12.3 produces OC SOUT. That physical inverter
stage is now modeled instead of the former direct SER_TXD-to-D12 shortcut.

Sheet 1 also explicitly ties D10 PIC SP/EN pin 16 to the `A` (+5 V) rail,
selecting standalone master mode. This is now modeled. Its older RxRDY/TxRDY
IR0/IR1 labels conflict with the FDC-era target assignment and are retained as
a revision boundary rather than overwriting the current D93 interrupt nets.

## Factory solder-side cuts and patches

The new `ДГШ5.109.009 СБ` photographs settle another class of apparent
“bodge.” Its factory `Вид В` detail explicitly calls out positions 150 and 159
on the mounting side and draws the cut/patch areas at D56, D15, D14, and D11.
Close-ups `PXL_20260711_114626340.jpg`, `114633498.jpg`, and
`114638730.MP.jpg` preserve those instructions. These features are therefore
revision-controlled assembly operations, not owner-board damage or optional
cleanup candidates.

The detail is authoritative for the existence and locality of each operation,
but it is not a copper schematic and does not by itself prove every endpoint.
The replica must preserve the resulting electrical topology; any future
artwork reconstruction must reconcile the unmodified copper with the factory
cuts/patches before replacing them with an equivalent clean trace.

The enlarged D15 detail (`114633498`) further shows that its explicit
`Разрезать` mark is on an auxiliary vertical trace between the second and third
drawn vias beside the package, approximately between the eighth and ninth
visible D15 pad levels. It is not a cut made directly at a D15 lead. The net of
that via-to-via segment remains to be identified from continuity or sheets 2-6.

The D14 detail likewise cannot yet be reduced to a package pin number. It
draws five holes in the auxiliary/left field beside a four-pad right package
row; the position-159 leader enters that auxiliary field. Three long
replacement traces terminate toward the lower field and a separate dogleg
reaches a right-row pad. Until the solder-side view is locally registered or
the connection table is obtained, assigning those features to D14 pins 1/2/7
would be an unsupported mirror/orientation guess.

For D11, Вид В draws a single 14-pad package column beside a separate
four-hole auxiliary field; position 159 marks the bridge into that field. A
reflected package-local fit in `PXL_20260710_200506061.jpg` now uses D11 corner
pads 1/15 and holds pads 14/28 out at 2.375 px error. It places the visibly
scraped/reworked copper beside package pins 4-6, correcting the board-level
projection that was displaced about 100 px onto adjacent copper. The rework
obscures the individual bridge landings, so neither an exact D11 pin nor any of
the four auxiliary-hole destinations is promoted without continuity or the
missing connection table.

## Placement conclusions retained

- Board outline: `310 x 266 mm` from the owner-measured physical target. An
  earlier scan-frame interpretation of the assembly drawing produced 279 mm
  and is not used by the PCB generator.
- The DRAM rows use roughly `11.25 mm` horizontal and `25 mm` vertical pitch.
- The `.158/.009` target populates D84-D91; empty D60-D83 footprints are real
  expansion sockets, not missing ICs from the official populated-parts list.
- D105 is horizontal below D13. A former extra `LA3B` sighting was a duplicate
  and is not a real part.
- The connector and mounting geometry is captured by the generated KiCad
  source; values and positions that remain uncertain are reported by the
  generated boundary/readiness documents.

## Release consequence

This evidence closes several old identity disputes, but it does not release the
PCB for fabrication. All four small-PROM contents are now preserved physical
truth; the D2/D30 WAIT edge and D94/FDC connectivity remain incomplete, and 9
official IC footprints (D28, D95-D99, D101, D102, and D106) still lack complete
pin-level functional nets. D105 wait/MRD logic is modeled and routed; the FDC
cluster and remaining READY/WAIT revision boundaries are not complete. See
`PLAN.md` and the generated reconstruction/unmodeled-footprint reports.
