# R9/R10 routed placement collision

The exact .009 drawing and owner photo identify R10 as the outer-left and R9 as the inner-right 2 kΩ pull-ups beside D3. [the identity review](../ref/photos/juku-pcb-2/r9-r10-r15-r16-identity-review.json) records the source evidence and photo registration. The source PCB has both footprints at their photo-projected positions; the two routed variants still omit them.

## Local routing conflicts

A placement-only insertion trial produced shorts and clearances against
existing signal and power copper. The conflicts below identify the local
repair area; they are recorded trial observations, not fresh DRC results.
Current whole-board findings belong to
[factory-wire fidelity](factory-wire-route-fidelity.md).

The recorded trial found these conflicts around the source pad locations:

| Pad | Copper requiring review |
| --- | --- |
| R10.1 | IR7, FRAME_INT and P5V |
| R10.2 | WREQ_N and nearby D12 pads |
| R9.1 | INTA and P12V |
| R9.2 | INTA and IR7 |

Use the current source pads and routed copper for repair coordinates. The
trial identifies affected nets; it does not qualify a replacement layout.

## Cause and correction boundary

The source PCB places D12 at `(224.535,67.630)` mm, rotated 180°, directly above D3, matching the exact .009 assembly and owner photo reviewed in [the D12 placement record](../ref/photos/juku-pcb-2/d12-d3-local-placement.json). Both routed variants still place D12 at `(202.495,77.090)` mm, rotation 0°, left of D3. That stale D12 placement and its local copper occupy the R9/R10 corridor. This is a source-to-routed placement divergence, not evidence that the photographed R9/R10 body locations are wrong.

The [placement parity report](board-placement-parity.md) lists the full
source-to-routed differences. R9/R10 are the two missing references;
other devices also differ in position or rotation.
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

The source footprint outlines leave about 1.6 mm between the drawn D3/R9
bodies while their courtyards overlap by about 0.3 mm. Review the selected
parts and assembly method before waiving that courtyard conflict. Physical
body clearance does not resolve the insertion-trial copper shorts.

Refresh D12 to the source/owner position and redesign the displaced D12, INTA, IR7, P12V, FRAME_INT, and WREQ_N copper around the two resistors. Keep R9/R10 at their registered source locations unless stronger owner evidence changes them. Then connect R10.1 to D3.1, R9.1 to D3.13, both upper pads to +5 V, and compare DRC to the routed baseline. Owner continuity of those four physical joints remains pending independently of the replica layout.

Moving power endpoints can also affect unrelated GND/P5V copper. Check open
connections, DRC and source-to-routed placement before promoting a replacement
board.
