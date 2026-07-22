# Board #2 photo survey

Target: processor module `7.102.158`, 50 owner photographs taken in 2026.

## Confirmed observations

- A top-center **К155РЕ3** timing PROM is **SOCKETED** and therefore
  dumpable. The exact refdes/program identity must still be established before
  treating a dump as D8 or D94 evidence.
- `PXL_20260710_200402344.jpg` clearly shows a populated **КР1818ВГ93**.
  The processor visible elsewhere on the board is not evidence that the FDC is
  absent. The earlier non-FDC classification is withdrawn.
- The July component-side grid clearly shows a populated eight-chip
  **КР565РУ5** bank, consistent with D84-D91, while the other DRAM expansion
  positions are empty.
- D2, D6, D8, and the D15-D22 ROM positions are socketed according to the
  combined drawing/photo evidence.
- X1 is a 3x32 СНП59-family connector. X2 is a 30-contact СНП connector. The
  bracket carries reset, video, a high-density D-sub connector, and the smaller
  tape/serial connector.
- X8 mask labels expose `-12V`, `+12V`, `+5V`, and `GND`; the power rails use
  thick tinned traces rather than copper pours.
- The board is two-layer. The insulated wires correspond to documented
  assembly links summarized in `BODGE-TRIAGE.md`.
- Independent May/July component views close two red axial diode bodies as
  `КД521В`: the direct designation face plus corroborating populated position
  for VD1 in the reset-RC corner, and the direct designation plus independent
  grade-В reverse face for VD4 in the traced beeper clamp.
  VD1 is visibly populated at the sheet-1 +5 V/reset-RC position; this corrects
  its former omission from the board model rather than treating the empty model
  as target-board evidence.
- The nominally "missing" ЛЕ4 package is present but decapped, with die and
  bond wires visible.
- The clock/video corner visibly includes ИЕ17/74S169-class, ИР16, ЛП5, ЛА3,
  ИЕ10, and ЛА1 devices. Refdes and exact role come from the official documents
  and board model, not package sighting alone.
- The 2026-07-10 batch adds a complete overlapping solder-side grid. Reviewed
  two-sided copper establishes D2.1/.3/.5/.6/.7 to
  `A10/A14/A12/A15/A9` and D94.1/.2/.3 to
  `FDC_RE_N/FDC_CS_N/FDC_WE_N`; these paths are now in
  `kicad/juku.board.json`.
- Seven later 2026-07-10 component-side photographs show the same FDC-equipped
  board with the КР1818ВГ93 temporarily removed. In particular,
  `PXL_20260710_202708344.jpg` exposes the footprint and component-side copper
  normally obscured by the package. The view improves package registration but
  does not by itself establish the remaining VG93 pin destinations.

## 2026-07-22 supplemental photos — X3 connector identity

Two additional owner photographs (outside the original 50-photo session)
close the X3 serial connector's physical identity:

- `x3-bracket-face-20260722.jpg` — bracket edge-on view of X4 and X3. The X3
  insert is a hoodless brown rectangular panel connector with a spring-bail
  retainer and **12 contacts in two rows of six**, with molded contact
  numbers `1` and `12` visible on the insert corners. In the РШ2Н/РГ1Н
  family (panel half = РГ1Н-1 socket, cable half = РШ2Н-1 hooded plug) this
  identifies X3 as a **РГ1Н-1-4** 12-contact panel socket; the mating cable
  part is РШ2Н-1-23 (straight hood) or РШ2Н-1-24 (angled hood).
- `x3-serial-area-rear-20260722.jpg` — component-side view of the same edge:
  the 12-wire white harness from X3 to the A21-A32 landings (matching the
  `.009` cable table's 12 lines), adjacent to the serial chain (two К170АП2,
  К170УП2, КР580ВВ51А). The blue connector stamped `СНО51-30-23 8903`
  corroborates the BOM's X8 power-connector designation.

This supersedes the former СНП59-30-23-В labeling of X3 (a BOM part-name-map
mislabel; the 30-contact СНП59 is X2's parallel connector).

## Limitations

Photo sighting alone did not establish D2/D94 contents; repeated programmer
reads now preserve the byte-level truth for both devices independently of this
survey. The July grid remains applicable physical evidence for the populated
FDC board, but refdes-to-pad registration and end-to-end trace extraction must
be completed before using it to assign the remaining functional nets of D99 or D101.
D28/D97/D98/D102/D106 are source-closed by exact-revision sheet 3. Traces hidden by sockets, solder, glare, or crossings still
require continuity measurements. The exact C35-C72 per-position capacitor
values and the remaining D30 READY/D105 WAIT boundaries also remain open.
