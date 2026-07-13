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

- Board SHA256: `e20687d60197204b17f2be35b847f3e48cfcd2ce92dee673d5f85554dcb9f7d8`
- Total violations: `677`
- Unconnected items: `499`
- Short violations: `16`
- Unique colliding pad/item pairs: `8`

## Violation types

| Type | Count |
| --- | ---: |
| `clearance` | 6 |
| `courtyards_overlap` | 116 |
| `hole_to_hole` | 3 |
| `shorting_items` | 16 |
| `silk_over_copper` | 199 |
| `silk_overlap` | 199 |
| `solder_mask_bridge` | 16 |
| `text_thickness` | 122 |

## Unique short collisions

| Nets | Items |
| --- | --- |
| Items shorting two nets (nets RF_RAIL and D97_A2N_BOUNDARY) | PTH pad 1 [RF_RAIL] of R73; PTH pad 9 [D97_A2N_BOUNDARY] of D97 |
| Items shorting two nets (nets R86_1_BOUNDARY and VT3_E) | PTH pad 1 [R86_1_BOUNDARY] of R86; PTH pad 1 [VT3_E] of VT3 |
| Items shorting two nets (nets VT3_BASE and D102_Q2_BOUNDARY) | PTH pad 2 [VT3_BASE] of R69; PTH pad 5 [D102_Q2_BOUNDARY] of D102 |
| Items shorting two nets (nets D95_D10_BOUNDARY and GND) | PTH pad 10 [D95_D10_BOUNDARY] of D95; PTH pad 2 [GND] of C13 |
| Items shorting two nets (nets VT3_E and D102_Q2N_BOUNDARY) | PTH pad 1 [VT3_E] of R74; PTH pad 12 [D102_Q2N_BOUNDARY] of D102 |
| Items shorting two nets (nets VT3_E and D102_Q1_BOUNDARY) | PTH pad 1 [VT3_E] of R74; PTH pad 13 [D102_Q1_BOUNDARY] of D102 |
| Items shorting two nets (nets VT3_BASE and D102_Q1N_BOUNDARY) | PTH pad 2 [VT3_BASE] of R68; PTH pad 4 [D102_Q1N_BOUNDARY] of D102 |
| Items shorting two nets (nets GND and RF_TAP) | PTH pad 1 [GND] of VD3; PTH pad 3 [RF_TAP] of L1 |

## Placement disposition

The D95/D97/D102 package centres and VD3 body centre are registered by independent owner-photo
fits and the factory assembly drawing. Each collision instead involves an
analog/FDC part whose current coordinate is explicitly approximate; moving a registered part to
clear one of these shorts would regress known-good placement.

| Approximate part | Fixed registered anchor | Required evidence |
| --- | --- | --- |
| `R73` | `D97` | R73 is a three-terminal RF-bias trimmer, not a lower-FDC-row part; register its physical body before moving it |
| `VT3` | `R86` | VT3 is a legacy .006 analog-placement seed; the .009 factory/photo-proven R86 centre disproves this location, so locate or explicitly DNP the target-revision VT3 before moving it |
| `R69` | `D102` | R69 placement is only an approximate analog-grid seed; locate the physical D34_SIG resistor from target-board imagery or continuity |
| `C13` | `D95` | the assembly-drawing site formerly read as C13 is proved to be C63; the real C13 position still requires target-board evidence |
| `R74` | `D102` | R74 placement is only an approximate analog-grid seed; locate the physical VT3 emitter resistor from target-board imagery or continuity |
| `R68` | `D102` | R68 placement is only an approximate analog-grid seed; locate the physical SND_MIX resistor from target-board imagery or continuity |
| `L1` | `VD3` | L1 is still an unregistered three-pad tapped-coil stand-in; the factory/photo-proven VD3 centre now disproves this placeholder location, so locate the actual coil holes before moving it |

- Classified approximate collision parts: `7/7`
- Unexpected collision references: `none`

The source PCB is not eligible for routed-copper adoption while any
short collision remains. Move parts only from registered target-revision
placement evidence; do not silence these findings with waivers.
