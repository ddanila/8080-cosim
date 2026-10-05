# R9/R10 routed placement collision

The exact .009 drawing and owner photo identify R10 as the outer-left and R9 as the inner-right 2 kΩ pull-ups beside D3. `ref/photos/juku-pcb-2/r9-r10-r15-r16-identity-review.json` records the source evidence and photo registration. The source PCB has both footprints at their photo-projected positions; the two routed variants still omit them.

## Local routing conflicts

A placement-only insertion trial produced shorts and clearances against
existing signal and power copper. The conflicts below identify the local
repair area; they are recorded trial observations, not fresh DRC results.
Current whole-board findings belong to
[factory-wire fidelity](factory-wire-route-fidelity.md).

The source footprint positions are R10.1 `INT6_RAW` `(211.204,93.578)` mm, R10.2 `P5V` `(211.204,83.418)`, R9.1 `INT7_RAW` `(214.319,94.881)`, and R9.2 `P5V` `(214.319,84.721)`. Representative trial conflicts:

| Pad | Existing routed item | Consequence |
| --- | --- | --- |
| R10.1 | IR7 B.Cu around `(211.5,93.5)`; FRAME_INT via `(212.125,94.0)`; P5V F.Cu diagonal | Short and hole clearance failures |
| R10.2 | WREQ_N B.Cu around `(210.5,83.25)`; D12 pins 5/6 nearby | Short and pad clearance failures |
| R9.1 | INTA F.Cu/B.Cu and via `(213.5,95.25)`; P12V F.Cu near `(214.25,94.75)` | Multiple direct shorts and hole clearance failures |
| R9.2 | INTA via `(214.5,84.5)` and IR7 B.Cu | Direct shorts |

## Cause and correction boundary

The source PCB places D12 at `(224.535,67.630)` mm, rotated 180°, directly above D3, matching the exact .009 assembly and owner photo reviewed in `ref/photos/juku-pcb-2/d12-d3-local-placement.json`. Both routed variants still place D12 at `(202.495,77.090)` mm, rotation 0°, left of D3. That stale D12 placement and its local copper occupy the R9/R10 corridor. This is a source-to-routed placement divergence, not evidence that the photographed R9/R10 body locations are wrong.

The [placement parity report](board-placement-parity.md) lists the full
source-to-routed differences. R9/R10 are the two missing references;
D11, D12, D26, D27, D42, D43, D58, D59, D6, and D9 also differ in position or rotation.
The local D12/R9/R10 repair is therefore only part of the routed refresh.

Native owner crop `(1000,650)-(1600,1350)` of
`ref/photos/juku-pcb-2/PXL_20260710_200418174.jpg` shows the fitted inner
R9 axial body beside D3 with a visible body-to-package gap; its bent leads
also clear the D3 package in this view. That observation rules out an obvious
body collision on the photographed board, but does not validate the generic
replica footprint's courtyard or a substitute resistor's diameter. Review
the fitted body envelope and lead bends before reducing or waiving the
source-board D3/R9 courtyard overlap. The insertion-trial shorts above
are copper conflicts; this mechanical view does not resolve them.

The source KiCad geometry makes the warning precise. D3's F.Fab body starts
at x `217.204` mm and R9's F.Fab body ends at x `215.619` mm, leaving
`1.585` mm between drawn bodies. Their F.Courtyard envelopes instead meet
at x `215.544` and `215.844` mm, an overlap of `0.300` mm. Thus the
source geometry has an assembly-envelope overlap, not a drawn-body
intersection. The photo supports physical body clearance on the original;
the replica's selected parts and insertion method still control the
courtyard disposition.

Refresh D12 to the source/owner position and redesign the displaced D12, INTA, IR7, P12V, FRAME_INT, and WREQ_N copper around the two resistors. Keep R9/R10 at their registered source locations unless stronger owner evidence changes them. Then connect R10.1 to D3.1, R9.1 to D3.13, both upper pads to +5 V, and compare DRC to the routed baseline. Owner continuity of those four physical joints remains pending independently of the replica layout.

## Repair scope

Use a targeted local relocation and reroute. Moving power endpoints can
also affect unrelated GND/P5V copper. Check open connections, DRC, and
source-to-routed placement before promoting a replacement board.
