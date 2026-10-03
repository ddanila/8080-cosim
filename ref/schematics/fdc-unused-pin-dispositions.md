# FDC unused-pin dispositions

Recovered `ДГШ5.109.009 Э3` sheet 3 is an exact-revision, pin-numbered
electrical drawing. It draws every used section of D28, D96, D97, D98, and
D102, including whichever complementary АГ3 output participates in each path.
Package pins omitted from otherwise complete symbols are intentional
no-connects.

| Device | Used sections visible on sheet 3 | Explicitly omitted package pins |
|---|---|---|
| D28 К155ЛН3 | all six pairs: 1→2, 3→4, 5→6, 9→8, and DRQ/INTRQ pairs 11→10 plus 13→12 | none |
| D96 КМ555ТМ2 | section 1 read-clock toggle; section-2 pins 9-13 including the D99.10-joined clear | none |
| D98 К155ЛП11 | buffer pairs 2→3, 4→5, 6→7, 12→11, and 14→13; enables 1/15 grounded | fourth buffer pair: input 10 and output 9 |
| D97 К155АГ3 | section-1 `/Q` pin 4 drives RAW READ; section-2 Q pin 5 and `/Q` pin 12 drive the first delay/cascade | unused section-1 complementary Q pin 13 |
| D102 К155АГ3 | section-2 Q pin 5 and `/Q` pin 12, then section-1 Q pin 13 form the second and third delays | unused section-1 complementary `/Q` pin 4 |

D28 pins 5/6 are the READY inverter; pins 10-13 participate in the
interrupt conditioner. Both D96 sections are source-used.

D96.13 is source-connected to D99.10 at a marked junction in the exact-revision
sheet-3 photo `PXL_20260718_101641055.jpg`; it is not an unused pin. Their
shared conductor continues to sheet 1 with an unread source. Recheck that
source, verify the D96.9/D101 and D96.11/D94.2 islands, and capture pins8-13 before hardware
release; see `docs/d96-read-clock-readiness.md`.

Primary views: `ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg`,
`PXL_20260718_101641055.jpg`, and `PXL_20260718_101648508.jpg`. Machine guards:
`python3 kicad/check_fdc_unused_pins.py` and
`python3 kicad/check_d93_irq_conditioner.py`.
