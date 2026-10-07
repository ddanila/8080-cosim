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
`D3.5 <-> D26.14`, and `D6.15 <-> D105.1`. The exact `.009` sheet-1 detail draws R15 and R16 as 12 kΩ
branches from D26.14/D3.5 and D26.15/D3.3 to ground. The factory assembly
places R15 upright to the right of D3 and R16 horizontally below it. Their
owner-photo markings are compatible with `12K`; isolated values and return
rails remain unmeasured. Source images, crops and registration are retained in
[the resistor identity review](../ref/photos/juku-pcb-2/r9-r10-r15-r16-identity-review.json).

The two upright 2 kΩ bodies left of D3 are **R10 (outer) and R9 (inner)**,
the source-drawn INT6/INT7 pull-ups. They must not be used as R15/R16 value
evidence. Check their apparent common upper bridge to +5 V and their separate
lower leads to D3.1/INT6_RAW and D3.13/INT7_RAW before accepting those physical
nets as closed.

For the actual R15/R16 bodies, measure isolated resistance and each return
lead to known ground and +5 V. The source ground bars conflict with earlier
owner-reported +5 V paths until the correctly identified bodies are probed.

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
Runnable selection uses the reader-3-qualified physical D6 table through
`U_DECODE`, with direct physical output mapping. The functional decoder remains
only in the B37A diagnostic comparison. A7 source and output order are closed;
[RT4 acquisition](rt4-dump-acquisition.md) preserves the channel-order evidence.

## Chip-removed output correction

Chip-removed continuity separates D6.11, D6.12 and D13.12. Installed-PROM
resistance readings must not be treated as proof of one copper conductor:

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
