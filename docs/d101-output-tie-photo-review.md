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

The full sheet-3 overview `PXL_20260718_101633062.jpg` traces
D94.14 to the marked D101.7 junction. The overlapping frame
`PXL_20260718_101641055.jpg`, crop `(450,1800)-(1700,4080)`,
separates that Q0 conductor from the nearby D96.9/A0–A3 input branch;
their aligned turns do not join. Source and owner continuity therefore
agree on D94.14↔D101.7.

The overview places D99.4/Q1_N on the neighboring rail and traces it to
D93.23/HLT. That path's physical continuity remains unmeasured; see
[the D99 route review](d99-q1n-a4-conflict-photo-review.md).

## Model guard

Run from the repository root with Python's standard library:

```sh
python3 kicad/check_fdc_precomp_network.py
```

The guard checks selected canonical JSON nets, including R99's connection to
the D96.9/input island, component values and NC declarations. It verifies
D97/D101/D102 instance entries in `sync/map.json` and literal HDL connection
markers. It does not run LVS or compile/simulate the HDL, and does not
establish physical isolation, copper routing, or analog precompensation timing.
