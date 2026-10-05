# Native schematic resistor values

Status: **26 VALUES SOURCE-CLOSED / 0 TARGET HOLD**

The native electrical sheets and target-board photos supply 26 registered values.
This report checksum-guards those sources and checks that the registered literals
agree with the board JSON and source PCB. It also checks the complete set of
modeled axial resistors for missing values.

## Command

Run from the repository root with Python 3 (standard library only).
The guard reads source PCB text directly; KiCad is not required.
It overwrites this report after the source and model checks pass.

```sh
python3 scripts/report_native_resistor_values.py
```

## Closed values

| Ref | Value | Sheet | Circuit group |
| --- | ---: | ---: | --- |
| `R11` | `1к` | 1 | sheet-1 decode open-collector pullups |
| `R12` | `1к` | 1 | sheet-1 decode open-collector pullups |
| `R13` | `1к` | 1 | sheet-1 decode open-collector pullups |
| `R14` | `1к` | 1 | sheet-1 decode open-collector pullups |
| `R17` | `200` | 1 | sheet-1 decode RC series resistor |
| `R33` | `620` | 2 | sheet-2 D34 counter-load pulse shaper |
| `R40` | `15к` | 2 | sheet-2 S3 switch pullup bank |
| `R41` | `15к` | 2 | sheet-2 S3 switch pullup bank |
| `R42` | `15к` | 2 | sheet-2 S3 switch pullup bank |
| `R43` | `15к` | 2 | sheet-2 S3 switch pullup bank |
| `R44` | `15к` | 2 | sheet-2 S3 switch pullup bank |
| `R45` | `15к` | 2 | sheet-2 S3 switch pullup bank |
| `R47` | `20к` | 2 | sheet-2 D56 timing network |
| `R48` | `8,2` | 2 | sheet-2 beeper clamp |
| `R59` | `33к` | 2 | sheet-2 D56 timing network |
| `R60` | `5,1к` | 2 | sheet-2 frame interrupt pullup |
| `R61` | `12к` | 2 | sheet-2 D56 timing network |
| `R62` | `2к` | 2 | sheet-2 video summing stage |
| `R63` | `1к` | 2 | sheet-2 video summing stage |
| `R64` | `5,1к` | 2 | sheet-2 video summing stage |
| `R65` | `430` | 2 | sheet-2 video summing stage |
| `R66` | `1к` | 2 | sheet-2 video summing stage |
| `R67` | `4,7к` | .009 photos | .009 target video-clamp body |
| `R78` | `10к` | 3 | .009 D106 preset pull-up |
| `R90` | `2к` | 2 | sheet-2 beeper clamp |
| `R91` | `1к` | 2 | sheet-2 beeper clamp |

## Deliberate holds

None. Every modeled axial resistor has a value; this report validates the 26 registered literals above.

## Evidence boundary

The guard checks source hashes and registered value fields. It does not
measure installed resistance, verify physical continuity, or run PCB DRC.

- Sheet 1 closes R11-R14 and R17 directly; these are not values inferred
  from open-collector behavior.
- Sheet 2 closes the R40-R45 common 15 kΩ group, plus the D56,
  FRAME_INT, video-summing, and beeper networks.
- The factory-identified target R67 body reads `4K7` independently in July
  and May views. This supersedes the 2 kΩ R67 value printed on both
  the `.006` and exact `.009` sheet-2 drawings without
  promoting the target part's still-unresolved pin-2 destination.
- R78's exact-sheet connectivity, factory pair identity, registered owner
  joints, and directly readable `10K` marking close its value and placement.
- Exact `.009` sheet 2 prints R33=620 Ω, and independent May and July
  owner views read `К62` on its fitted body. Isolated resistance and
  the hidden R33 right-hand rail still need measurement.
- R48's `8,2 Ом` label is independently corroborated by the traced beeper
  boundary. No modeled axial resistor remains unvalued.
