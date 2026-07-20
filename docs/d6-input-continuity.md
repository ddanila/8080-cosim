# D6 input continuity correction

Status date: 2026-07-20

Status: **D6 A5/A6/A7 SOURCES MEASURED**

Direct continuity measurements on a physical `.009` processor board correct
the older-sheet assignment of D6's three high address inputs. The measurements
were accompanied by a visual copper trace where noted by the owner.

## Confirmed routes

```text
D26.15 PC1 --+-- D3.3 -> inverter -> D3.4 -- D6.1  A6
             +-- resistor pull-up -> +5 V

D26.14 PC0 --+-- D3.5 -> inverter -> D3.6 -- D6.2  A5
             +-- resistor pull-up -> +5 V

D6.15 A7 ------------------------------ D105.1
```

`D6.1 <-> D3.4` was reported as zero ohms and its copper was followed
visually. Direct continuity also proves `D6.2 <-> D3.6`, `D3.3 <-> D26.15`,
`D3.5 <-> D26.14`, and `D6.15 <-> D105.1`. The pull-up resistor references
and values at D3.3 and D3.5 were not identified.

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

The initial session found no continuation beyond `D6.15 <-> D105.1`.
With D6 removed, resistance from D6.15 to both GND and +5 V fluctuates at
approximately 100-200 kohm. This excludes a simple low-value pull-up or
pull-down; the variation may reflect in-circuit charging or leakage, but does
not by itself prove a capacitor. That observation is retained as measurement
history. A later owner session on 2026-07-19 directly closed
`D7.8 -> D105.1 -> D6.15`; D7.8 is the output of the D7 NAND receiving raw
`/IORD` and `/IOWR`, so A7 is the I/O-cycle-active-high qualifier. The model
must not merge it with MEMW or FDC density.

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
