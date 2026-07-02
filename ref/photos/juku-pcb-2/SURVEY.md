# Photo survey — board #2 (rev 7.102.158), 22 photos
## Major finds
1. **К155РЕ3 (8904) SOCKETED** (blue socket, top-center) → the V3-gating timing PROM is dumpable.
   Also socketed (per drawings + photos): D2/D6/D8 (РТ4 ×2 visible in blue sockets), D15-D22 ROM.
2. **Connectors**: X1 = СНП59-96Р (3×32 confirmed by angle shot), X2 = СНП59-30 ("СНП51-30-25 8903"
   label), bracket: RESET pushbutton (S1) | VIDEO BNC | **X4 = DB-26HD** | **X3 = small brown
   ~10-pin** (tape/serial). ОТК QC stamp on X4.
3. **Solder side (full shot)**: 2-layer confirmed; **X8 pads labeled on the mask: -12/+12/+5V/GND** —
   physically confirms our rail mapping (59/60/61/62). Power = thick tinned traces (not pours).
   Trace style: 45° Manhattan, dense horizontal channels through the DRAM field (matches our router's
   congestion experience). "7.102.158 №1в" etched.
4. **The "missing ЛЕ4" is actually DECAPPED** — package present, lid off, bare die + bond wires
   visible (clock/video corner).
5. **Real part IDs in the clock/video corner**: КР531ИЕ17 8902 (→ our D40 "СТ16" is ИЕ17/74S169-class,
   NOT ИЕ7 — silk-mark correction), К555ИР16 8902 (confirms ИР16, DIP-14), К555ЛП5 8904, КР1533ЛА3 8906,
   К555ИЕ10 8905, КР531ЛА1 8702. Crystal = **РК-171 8903**.
6. **Bodge wires**: heavy white ECO lacing (more than board #1/rev 7.102.100) — schematic-vs-etch
   deltas + possibly post-schematic ECOs; to be traced wire-by-wire (see bodge plan in bom-toward-76).
7. This board: DRAM bank unpopulated; electrolytics cut (board #1 photos are the caps reference).
