# D6 input continuity correction

Status: **D6 A5/A6/A7 SOURCES MEASURED**

Direct continuity measurements on a physical `.009` processor board correct
the older-sheet assignment of D6's three high address inputs. The measurements
were accompanied by a visual copper trace where noted by the owner.

## Confirmed routes

```text
D26.15 PC1 --+-- D3.3 -> inverter -> D3.4 -- D6.1  A6
             +-- resistor branch (return disputed)

D26.14 PC0 --+-- D3.5 -> inverter -> D3.6 -- D6.2  A5
             +-- resistor branch (return disputed)

D6.15 A7 ------------------------------ D105.1
```

`D6.1 <-> D3.4` was reported as zero ohms and its copper was followed
visually. Direct continuity also proves `D6.2 <-> D3.6`, `D3.3 <-> D26.15`,
`D3.5 <-> D26.14`, and `D6.15 <-> D105.1`. An original-resolution
reread of the exact `.009` sheet-1 detail `PXL_20260718_101809608.jpg`
(crop `(1100,2750)`–`(2150,3850)`) confirms `R15=12k` on D26.14/D3.5
and `R16=12k` on D26.15/D3.3. Both terminate in the drawing's perpendicular
ground bar: vertical at R15, horizontal at R16. The rotated form agrees with
the ground symbol at D2.V1/V2 on sheet-1 detail `PXL_20260718_101817644.jpg`. The `.009`
assembly detail `PXL_20260711_114556899.jpg` places **R15 vertically to the
right of D3** and **R16 horizontally below D3**. The owner component photo
`PXL_20260710_200418174.jpg` shows distinct fitted bodies at those positions;
their dark markings are compatible with `12K`, but neither value nor both lead
connections have been measured.

The two upright red-black-red/gold **2 kΩ bodies left of D3 are R10 (outer)
and R9 (inner)** in the same original-resolution assembly crop. Their position
and value agree with exact `.009` sheet 1's 2 kΩ INT6/INT7 pull-ups. The former
R15/R16 `12k`-versus-`2k` claim came from assigning that left pair to the
wrong drawing labels and is retracted. The owner views show an apparent common
upper solder bridge for R9/R10. Test it to +5 V and test the separate lower
leads to D3.1/INT6_RAW and D3.13/INT7_RAW before treating their physical nets
as closed. Separately measure the right-side R15 and lower horizontal R16:
each signal lead against D3.5/D26.14 or D3.3/D26.15, and each return lead
against ground and +5 V. The source return bars and earlier owner-reported
+5 V paths remain a real electrical conflict for R15/R16 until the correct
physical bodies are probed. Source/photo registration is recorded in
`ref/photos/juku-pcb-2/r9-r10-r15-r16-identity-review.json`.

## Resistor photo evidence and remaining probes

The [actual-pad review](../ref/photos/juku-pcb-2/r15-r16-actual-pad-review.json)
closes R15's lower lead to D3.5 and R16's right lead to D3.3 by visible copper.
The opposite leads and their return rails remain open. Measure them to ground
and +5 V to resolve the source/continuity conflict above.

For R9/R10, the
[two-face review](../ref/photos/juku-pcb-2/r15-r16-two-face-review.json)
retains the provisional hole matches, common upper conductor, separate lower
routes, remote probe annuli, and registration limits. The file's original
R15/R16 attribution is retracted. Neither proximity nor cross-face projection
closes the lower routes to D3.1/D3.13 or establishes the common rail as +5 V.
Use its recorded coordinates for probe planning, then verify continuity.

The resulting proved D6 address order is:

```text
A0..A7 = BA15, BA14, BA13, BA12, BA11, /PC0, /PC1, D7.8 IO_CYCLE_H
```

## Explicit negative evidence

- D6.1 does not connect to D26; the older D26.17/PC3 assignment is rejected.
- D6.2 does not connect to any D26 pin; the older D26.16/PC2 assignment is
  rejected.
- D6.15 does not connect to any D26 pin; the older D26.13/PC4/FDC-density
  assignment is rejected.
- D105.1 does not connect to D105.12.
- The separately reconfirmed write-strobe net remains
  `D105.12 <-> D105.13 <-> D5.26`.

Owner continuity closes `D7.8 -> D105.1 -> D6.15`. D7.8 is the NAND
output receiving raw `/IORD` and `/IOWR`, so A7 is the I/O-cycle-active-high
qualifier. It must remain separate from MEMW and FDC density.

## Modeling consequence

The structural model now routes D26 PC1 and PC0 through the measured D3
inverters before D6 A6 and A5, and routes D7.8 to D105.1/D6 A7.
Runnable selection now comes from the physical D6 table through `U_DECODE` under
the direct physical output mapping. The 2026-07-19 revision-3 reread proved that
the earlier artifact had all four data channels reversed; the separately named
functional decoder is retained only by the B37A diagnostic comparison. The A7
source and output-order questions are independently closed.

## Chip-removed output correction

A subsequent D6-removed measurement invalidates the earlier installed-PROM
claim that D6.11, D6.12, and D13.12 form one zero-ohm conductor. The physical
socket pads are separate:

```text
D6.12 ROM_N -> D8.15 E_N
D6.11 RAM_N -> D2.15 A7 / -WREQ
D6.11 RAM_N -> D92.5 and R12.2 pull-up branch
D6.11 RAM_N -/-> D8.15
D6.11 -/-> D6.12
D13.12 -> D6.14 V2
D6.13 V1 <-> D6.14 V2 (bottom-layer copper visually confirmed)
```

The same powered-off owner session directly confirms the complete decode-path
endpoint chain: `D6.9 -> D13.1`, `D13.2 -> D37.4`, and
`D37.6 -> D58.9`.

The other D37 NAND input is not an open continuity ask: the native sheet-2
route closes global `MEMR -> D33.3`, inverter output `D33.4 -> D37.5`, while
the guarded D37 package contract fixes pins 5/4->6 as that NAND section.

The model therefore restores the independent `ROM_SEL` output and moves
D6.11 onto the measured `WREQ_N` conductor. Follow-up owner continuity proves
that conductor also reaches D92.5/R12.2, with R12's other side at +5 V,
physically confirming the older-sheet pull-up branch while keeping D6.12
separate. D13.12
therefore feeds both physically tied D6 enable pins. The reported D13.12-to-D16.13 reading
is recorded as a follow-up candidate, not promoted connectivity, until D16 is
removed and the socket pad is rechecked.
