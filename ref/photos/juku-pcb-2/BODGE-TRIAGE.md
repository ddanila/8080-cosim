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
- Physical placement evidence: `es101_emaplaat.pdf` and the 22 owner photos in
  this directory.
- The current normalized endpoint record is `kicad/juku.board.json`.

## Settled identity corrections

The `.009` parts list establishes the FDC-era identities below. Sheet 3 uses
some of the same D94-D108 reference numbers as the older tape-era drawing; the
two assemblies must not be mixed.

| Ref | `.009` identity | Current conclusion |
| --- | --- | --- |
| D2 | КР556РТ4, program `.037` | bus/wait PROM; signal wiring and contents still open |
| D6 | КР556РТ4, program `.038` | memory-decode behavior reconstructed; original dump absent |
| D8 | К155РЕ3, program `.039` | ROM pager behavior reconstructed; original dump absent |
| D9 | К555ИД7 | I/O chip-select decoder; physical D2 is not this decoder |
| D41-D43 | К555ИР16 | timing register plus two pixel serializers |
| D52 | К555КП14 | fifth DRAM/video address mux |
| D84-D91 | К565РУ5 | populated RAM bank on the `.158/.009` target |
| D92 | К555ЛЕ4 | memory/timing support logic |
| D93 | КР1818ВГ93 | FDC |
| D94 | К155РЕ3, program `.092` | FDC-era PROM; enable, outputs, and contents still open |
| D95, D101 | К555КП12 | FDC quadrant multiplexers |
| D97, D99, D102 | КМ555АГ3 | FDC quadrant one-shots |
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

The D2 wiring region is on sheet 1, but the available read does not establish
every destination strongly enough to route it. D2 pin table from sheet 1:
`A0-A7=5/6/7/4/3/2/1/15`, `V1/V2=13/14`, and `D0=12`.

D105 two visible ЛА3 sections are `(9,10)->8` and `(4,5)->6`. Current evidence
indicates D2 pin 12 into D105 pin 9 and D2 V1/V2 tied low. The sheet's power
legend identifies D105 pin 10's `H` source as the derived −5 V rail. D105 pin
6's destination still requires continuity confirmation. The proved D2 leads
are modeled and routed; its other inputs and PROM contents remain deferred.

The full-resolution sheet also proves three D2 address leads: `VIDEO CYCLE` to
A3/pin 4, `-XACK` to A5/pin 2, and `-WREQ` to A7/pin 15. It shows D105's other
two sections as `(1,2)->3` (D13.4 and MWR inputs) and `(12,13)->11` (tied-input
MRD inverter). These reads reduce the trace boundary but do not yet establish
D2 A0/A1/A2/A4/A6 or every output destination.

The three КМ555АГ3 positions require 16-pin DIP footprints. This is consistent
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

| Wire | Measured endpoints | Meaning/state |
| ---: | --- | --- |
| 7 | D1.22 - D35.10 | PHI1 |
| 14 | D1.15 - D35.12 | PHI2 |
| 9 | D1.19 - D38.12 | SYNC |
| 8 | D5.1 - D38.8 | STSTB |
| 19 | D5.26 - D7.2 | MEMW branch |
| 12 | D13.2 - D37.4 | RAM output-enable path |
| 13 | D13.1 - D92.1 | ROE support path |
| 10 | D41.13 - D50.1 | video/CPU mux select |
| 11 | D7.1 - D92.13 | timing support path |
| 20 | D3.10 - X3.3 | serial `S_TTL` path |
| - | D26.23 - X9.9 | keyboard/tape connector line |
| 17/18 | D98.7 through 220 ohm, far endpoint unread | reset-chain follow-up |

The settled wire links are represented in the board model with endpoint
provenance. The unread reset-chain endpoint remains a boundary rather than an
invented connection.

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
PCB for fabrication. D2 and D94 remain incomplete, and 9 official IC
footprints (D28, D95-D99, D101, D102, and D106) remain outside the pin-level
model. D105 wait/MRD logic is modeled and routed; the FDC cluster and remaining
READY/WAIT revision boundaries are not complete. See `PLAN.md` and the generated
reconstruction/unmodeled-footprint reports.
