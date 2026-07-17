# Native schematic resistor values

Status: **23 VALUES SOURCE-CLOSED / 1 TARGET HOLD**

The native electrical sheets print 23 values that were formerly blank in
the machine-readable board model. This report checksum-guards those scans,
checks the board JSON and generated source PCB agree, and keeps ambiguous or
revision-sensitive values out of the promoted set.

## Command

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
| `R90` | `2к` | 2 | sheet-2 beeper clamp |
| `R91` | `1к` | 2 | sheet-2 beeper clamp |

## Deliberate holds

| Ref | Why it remains unvalued |
| --- | --- |
| `R67` | sheet 2 prints 2k, but target .009 photos prove its far-side continuation differs from the .006 drawing; retain the target-value hold until the body or target documentation is readable |

## Evidence boundary

- Sheet 1 closes R11-R14 and R17 directly; these are not values inferred
  from open-collector behavior.
- Sheet 2 closes the R40-R45 common 15 kΩ group, correcting stale 13 kΩ
  prose, plus the D56, FRAME_INT, video-summing, and beeper networks.
- Connectivity is unchanged. This milestone only replaces absent value
  metadata with literal scan evidence.
- R48's `8,2 Ом` label is independently corroborated by the traced beeper
  boundary. R67 alone remains outside sourcing-ready valued BOM groups.
