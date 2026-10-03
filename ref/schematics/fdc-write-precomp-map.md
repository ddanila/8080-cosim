# FDC write-precomp source map

The recovered ДГШ5.109.009 Э3 sheet 3 closes the target board's write-data delay and precompensation chain. The model adopts every non-conflicting sheet connection, while direct target-board continuity remains authoritative where the factory electrical drawing is internally inconsistent.

| Function | Closed path |
|---|---|
| Write-data input | D93.31 → D97.10 |
| First delay | D97.5 → D101.10; D97.12 → D102.10 |
| Cascaded delays | D102.5 → D101.11; D102.12 → D102.2; D102.13 → D101.12 |
| Selection | D93.17 EARLY → D101.2; D93.18 LATE → D101.14 |
| Section-A enable | Sheet-1 D26 PA6/pin38 `IMDRG (3)` → sheet-3 D101 VA/OE0_N pin1 `IMDRG (1)`; physical continuity pending |
| Section-A data | Marked sheet-3 junctions join D101 A0–A3/pins 6, 5, 4, 3; the full sheet-3 overview traces their common conductor to D96 Q2/pin9. Owner-visible copper closes pin4 to R92.1/R99.2; physical continuity of D96.9 and the other three inputs to that island is pending |
| Precomp output | D101.9 → D100.6 |
| Clears/triggers | WREQ_N → D97.3/.11 and D102.3/.11; D97.1/.9, D102.1/.9 and D101.13/.15 → GND |
| Timing networks | C16 on D97.15/.14; C19/R100 on D97.7/.6; C20/R108 on D102.6/.7; C22/R102 on D102.14/.15; timing resistor rail → +5 V |

Sheet-3 detail tiles `_101644861` and `_101648508` print C16=`27` and
C19/C20/C22=`22`, giving schematic nominals of 27 pF and 22 pF under the
native bare-number convention. The target C16/C19 bodies show matching digits
but incomplete unit codes, so their installed values remain unverified.
Two owner angles show bare `22` on C20/C22, matching the drawing
numerals without independently proving the unit. Installed values remain held;
22 pF is the drawing nominal. See
[native capacitor values](../../docs/native-capacitor-values.md).

## Conflict resolution

Two overlapping exact .009 sheet-3 detail frames independently print `R99 4,7к`: `PXL_20260718_101644861.jpg` beside D97 timing network (native crop about (1390,1230)-(2260,1540)) and `PXL_20260718_101648508.jpg` beside D101 Q0/pin7 (native crop (1250,390)-(1780,1050)). The duplicated designator is legible in both originals, although the assembly has one R99. Target component and solder views instead close physical R99 between D101.4/R92.1 and D101.8/GND. That observed target topology is retained.

The sheet labels a separate `R86 470` WREQ reset pull-up. Target views unambiguously place physical R86=4.7k in the four-resistor timing column, with R86.1 on C19.2/D97.6 and R86.2 on the common +5 V rail. The target identity and connectivity override the sheet annotation.

D101 Q1/pin9 crosses the Q0/pin7 conductor without a junction. The source
and owner continuity independently close D101.7 to D94.14; D101.9 remains
on the separate D100.6 precomp path. Crop coordinates and physical isolation
limits are in [the D101 output review](../../docs/d101-output-tie-photo-review.md).
D99.4 reaches D93.23/HLT on the neighboring upper rail; its original-board
continuity remains unmeasured. See
[the D99 route review](../../docs/d99-q1n-a4-conflict-photo-review.md).

R88 is owner-closed on D94.3/D93.4. D97.13 and D102.4 are omitted
complementary outputs on otherwise complete, pin-numbered one-shot symbols
and are intentional no-connects. The section-A enable and common input
conductor are source-closed as listed above; their physical continuity
limits are recorded in
[the section-A review](../../docs/d101-section-a-input-source-review.md).

Primary image: `ref/photos/dgsh5-109-009-e3/PXL_20260718_101648508.jpg`. Target corroboration: `ref/photos/juku-pcb-2/PXL_20260710_200418174.jpg` and `PXL_20260710_200522685.jpg`.

## Model guard

```sh
python3 kicad/check_fdc_precomp_network.py
```

The guard checks canonical JSON connections and resistor values, unresolved
C20/C22 installed values, and structural HDL/LVS mappings. It does not
validate installed analog timing, physical continuity, or routed copper.
