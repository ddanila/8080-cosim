# Board #2 photo survey

Target: processor module `7.102.158`, 22 owner photographs taken in 2026.

## Confirmed observations

- A top-center **К155РЕ3** timing PROM is **SOCKETED** and therefore
  dumpable. The exact refdes/program identity must still be established before
  treating a dump as D8 or D94 evidence.
- D2, D6, D8, and the D15-D22 ROM positions are socketed according to the
  combined drawing/photo evidence.
- X1 is a 3x32 СНП59-family connector. X2 is a 30-contact СНП connector. The
  bracket carries reset, video, a high-density D-sub connector, and the smaller
  tape/serial connector.
- X8 mask labels expose `-12V`, `+12V`, `+5V`, and `GND`; the power rails use
  thick tinned traces rather than copper pours.
- The board is two-layer. The insulated wires correspond to documented
  assembly links summarized in `BODGE-TRIAGE.md`.
- The nominally "missing" ЛЕ4 package is present but decapped, with die and
  bond wires visible.
- The clock/video corner visibly includes ИЕ17/74S169-class, ИР16, ЛП5, ЛА3,
  ИЕ10, and ЛА1 devices. Refdes and exact role come from the official documents
  and board model, not package sighting alone.

## Limitations

This board has its DRAM bank unpopulated and electrolytics removed. It is useful
for routing, sockets, connectors, and package identity, but another assembly is
needed for installed DRAM/capacitor-value evidence. Photo sighting alone does
not close D2/D94 contents or provide pin-level connectivity for the 9 official
placement-only IC footprints in the FDC cluster. The remaining D30 READY and
D105 WAIT-revision boundaries also require stronger evidence.
