# D101 Q0/Q1 crossing: source and owner continuity

The native `.009 Э3` sheet-3 frame
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101648508.jpg`
separates D101 Q0/pin 7 and Q1/pin 9. At original pixels around
`(1550,620)`, the pin-9 conductor rises across the horizontal pin-7 run
**without a junction dot**. The filled dot farther right, around `(1598,620)`,
belongs to another vertical conductor meeting pin 7 and the source-drawn
`R99 4.7k` branch.

Pin 9 continues on its separate path to D100.6. Owner chip-removed
continuity closes pin 7 to D94.14. The registered target solder photo
`ref/photos/juku-pcb-2/PXL_20260710_200522685.jpg` places pin 9 near
`(2166,1099)` and pin 7 near `(2112,1262)` with no visible local B.Cu bridge.
These three pieces of evidence agree on separate outputs. A power-off
pin-7-to-pin-9 isolation measurement remains a useful board check, but the
source draws them separately.

The source's separate `R99` label remains problematic: the native D97 detail tile `PXL_20260718_101644861.jpg` and D101 detail tile `PXL_20260718_101648508.jpg` each legibly print `R99 4,7к`, so it duplicates the timing-resistor designator, while owner copper instead places the physical
R99 between D101.4/R92.1 and D101.8/GND. That source-to-board discrepancy
does not change the separate output paths.

In the exact sheet-3 overview `PXL_20260718_101633062.jpg`, crop
`(2040,1450)-(2310,2350)` preserves both verticals: D101.9 turns north on
the left and crosses the D101.7 line without a dot; the filled D101.7 junction
is on the right vertical. In the same native frame, crop
`(1800,1050)-(2480,2250)`, that vertical crosses the horizontal D100
output runs without junction dots; proximity to those runs does not assign
another D100 output to Q0. The overlapping native frame
`PXL_20260718_101641055.jpg`, crop `(1150,900)-(2250,4050)`, follows
the Q0 vertical north to its westward turn near original pixel
`(1570,2020)`, above D100. The westward Q0 run turns north again near `x≈1290`. A separate, nearly
collinear run ends near `x≈1235` and descends to the joined D101 A0–A3
input branch; tracing it upward reaches D96 Q2/pin 9. The gap between
those two turns is visible in `PXL_20260718_101641055.jpg` crop
`(450,1800)-(1700,4080)`. Their matching height does not join Q0 to the
D96.9/input island. The single-frame sheet-3
overview `PXL_20260718_101633062.jpg`, crop `(700,520)-(2420,2400)`,
shows the complete connection: D94 A4/pin 14 rises onto the lowest of the long upper rails;
the same uninterrupted rail runs east, descends beside D99/D100, and
continues to the marked D101 Q0/pin 7 junction. The narrower overview crop
`(1650,600)-(2420,2350)` preserves the eastern descent and Q0 junction.
Thus exact `.009` source and owner continuity independently agree on
D94.14↔D101.7. The same overview shows D99.4/Q1_N on the neighboring
rail above this one and traces it onward to D93.23/HLT; their physical
continuity remains a separate probe.

## Model guard

```sh
python3 kicad/check_fdc_precomp_network.py
```

The guard checks the canonical JSON output nets, R99 connection to the
D96.9/input island, and structural HDL/LVS mappings. It does not establish
physical isolation, copper routing, or analog precompensation timing.
