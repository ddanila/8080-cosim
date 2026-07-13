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

- Board SHA256: `28509aea5ff95df14c5d7aaa32e1b206df137a50aeabe9a3b838ac586132ce2d`
- Total violations: `620`
- Unconnected items: `499`
- Short violations: `12`
- Unique colliding pad/item pairs: `6`

## Violation types

| Type | Count |
| --- | ---: |
| `clearance` | 2 |
| `courtyards_overlap` | 83 |
| `hole_to_hole` | 2 |
| `shorting_items` | 12 |
| `silk_over_copper` | 199 |
| `silk_overlap` | 199 |
| `solder_mask_bridge` | 12 |
| `text_thickness` | 111 |

## Unique short collisions

| Nets | Items |
| --- | --- |
| Items shorting two nets (nets VT3_BASE and D102_Q2_BOUNDARY) | PTH pad 2 [VT3_BASE] of R69; PTH pad 5 [D102_Q2_BOUNDARY] of D102 |
| Items shorting two nets (nets D97_A2N_BOUNDARY and RF_RAIL) | PTH pad 9 [D97_A2N_BOUNDARY] of D97; PTH pad 1 [RF_RAIL] of R73 |
| Items shorting two nets (nets VT3_BASE and D102_Q1N_BOUNDARY) | PTH pad 2 [VT3_BASE] of R68; PTH pad 4 [D102_Q1N_BOUNDARY] of D102 |
| Items shorting two nets (nets GND and D95_A1_BOUNDARY) | PTH pad 2 [GND] of C13; PTH pad 2 [D95_A1_BOUNDARY] of D95 |
| Items shorting two nets (nets VT3_E and D102_Q2N_BOUNDARY) | PTH pad 1 [VT3_E] of R74; PTH pad 12 [D102_Q2N_BOUNDARY] of D102 |
| Items shorting two nets (nets VT3_E and D102_Q1_BOUNDARY) | PTH pad 1 [VT3_E] of R74; PTH pad 13 [D102_Q1_BOUNDARY] of D102 |

The source PCB is not eligible for routed-copper adoption while any
short collision remains. Move parts only from registered target-revision
placement evidence; do not silence these findings with waivers.
