# Source PCB DRC

Status: **PLACEMENT HOLD**

This report parses KiCad's `violations` array. `shorting_items` is a
violation type, not a top-level JSON member; checking
`report.get('shorting_items')` incorrectly reports zero.

## Command

```sh
python3 kicad/report_source_pcb_drc.py
```

## Summary

- Board SHA256: `5533c360f7dcab5bda31b298e97d072610fdd49c90c7a0c64593150da2401ae7`
- Total violations: `649`
- Unconnected items: `499`
- Short violations: `12`
- Unique colliding pad/item pairs: `6`

## Violation types

| Type | Count |
| --- | ---: |
| `clearance` | 2 |
| `courtyards_overlap` | 105 |
| `hole_to_hole` | 2 |
| `shorting_items` | 12 |
| `silk_over_copper` | 199 |
| `silk_overlap` | 199 |
| `solder_mask_bridge` | 12 |
| `text_thickness` | 118 |

## Unique short collisions

| Nets | Items |
| --- | --- |
| Items shorting two nets (nets GND and D95_A1_BOUNDARY) | PTH pad 2 [GND] of C13; PTH pad 2 [D95_A1_BOUNDARY] of D95 |
| Items shorting two nets (nets D97_A2N_BOUNDARY and RF_RAIL) | PTH pad 9 [D97_A2N_BOUNDARY] of D97; PTH pad 1 [RF_RAIL] of R73 |
| Items shorting two nets (nets D102_Q1N_BOUNDARY and VT3_BASE) | PTH pad 4 [D102_Q1N_BOUNDARY] of D102; PTH pad 2 [VT3_BASE] of R68 |
| Items shorting two nets (nets D102_Q2_BOUNDARY and VT3_BASE) | PTH pad 5 [D102_Q2_BOUNDARY] of D102; PTH pad 2 [VT3_BASE] of R69 |
| Items shorting two nets (nets D102_Q2N_BOUNDARY and VT3_E) | PTH pad 12 [D102_Q2N_BOUNDARY] of D102; PTH pad 1 [VT3_E] of R74 |
| Items shorting two nets (nets D102_Q1_BOUNDARY and VT3_E) | PTH pad 13 [D102_Q1_BOUNDARY] of D102; PTH pad 1 [VT3_E] of R74 |

## Placement disposition

The D95/D97/D102 package centres are registered by independent owner-photo
fits and the factory assembly drawing. Each collision instead involves a
passive whose current coordinate is explicitly approximate; moving an IC to
clear one of these shorts would regress known-good placement.

| Approximate part | Fixed registered anchor | Required evidence |
| --- | --- | --- |
| `C13` | `D95` | the assembly-drawing site formerly read as C13 is proved to be C63; the real C13 position still requires target-board evidence |
| `R73` | `D97` | R73 is a three-terminal RF-bias trimmer, not a lower-FDC-row part; register its physical body before moving it |
| `R68` | `D102` | R68 placement is only an approximate analog-grid seed; locate the physical SND_MIX resistor from target-board imagery or continuity |
| `R69` | `D102` | R69 placement is only an approximate analog-grid seed; locate the physical D34_SIG resistor from target-board imagery or continuity |
| `R74` | `D102` | R74 placement is only an approximate analog-grid seed; locate the physical VT3 emitter resistor from target-board imagery or continuity |

- Classified approximate collision parts: `5/5`
- Unexpected collision references: `none`

The source PCB is not eligible for routed-copper adoption while any
short collision remains. Move parts only from registered target-revision
placement evidence; do not silence these findings with waivers.
