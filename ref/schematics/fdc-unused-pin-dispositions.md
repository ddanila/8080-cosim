# FDC unused-pin dispositions

Recovered `ДГШ5.109.009 Э3` sheet 3 is an exact-revision, pin-numbered electrical drawing. It draws every used section of D28, D97, D98, and D102, including whichever complementary АГ3 output participates in each path. The package pins omitted from those otherwise complete symbols are intentional no-connects, following the same convention already adopted for D96 section 2 and the unused D106 counter outputs.

| Device | Used sections visible on sheet 3 | Explicitly omitted package pins |
|---|---|---|
| D28 К155ЛН3 | pins 1→2, 3→4, 5→6, and 9→8 | fifth and sixth inverter pairs: 11→10 and 13→12 |
| D98 К155ЛП11 | buffer pairs 2→3, 4→5, 6→7, 12→11, and 14→13; enables 1/15 grounded | fourth buffer pair: input 10 and output 9 |
| D97 К155АГ3 | section-1 `/Q` pin 4 drives RAW READ; section-2 Q pin 5 and `/Q` pin 12 drive the first delay/cascade | unused section-1 complementary Q pin 13 |
| D102 К155АГ3 | section-2 Q pin 5 and `/Q` pin 12, then section-1 Q pin 13 form the second and third delays | unused section-1 complementary `/Q` pin 4 |

These dispositions remove eight false singleton boundary nets without changing any active signal. D28 pins 5/6 are specifically retained as the live READY inverter; stale no-connect entries for those two pins were an internal model contradiction and are removed.

Primary views: `ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg` and `PXL_20260718_101648508.jpg`. Machine guard: `python3 kicad/check_fdc_unused_pins.py`.
