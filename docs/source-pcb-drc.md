# Source PCB DRC

Status: **PASS**

This report parses KiCad's `violations` array. `shorting_items` is a
violation type, not a top-level JSON member; checking
`report.get('shorting_items')` incorrectly reports zero.

## Command

```sh
python3 kicad/report_source_pcb_drc.py
```

## Summary

- Board SHA256: `f939ac76613320495a8fe5ce706290215bcccab28eec8ecad1c9edbc6db7da0f`
- Total violations: `610`
- Unconnected items: `499`
- Short violations: `0`
- Copper-clearance violations: `0`
- Track-crossing violations: `0`
- Unique colliding pad/item pairs: `0`

## Violation types

| Type | Count |
| --- | ---: |
| `courtyards_overlap` | 92 |
| `silk_over_copper` | 199 |
| `silk_overlap` | 199 |
| `text_thickness` | 120 |

## Unique short collisions

| Nets | Items |
| --- | --- |

## Revision disposition

The former ten collision pairs came from placing the `.006` dashed VT3/VT4 RF option
on top of independently registered `.009` FDC parts. Complete `.009` assembly-drawing
coverage and the owner-board component tiles show only VT1/VT2, while the archived group
BOM assigns the adjustable trimmer and extra RF transistors to `.006`. The legacy-only
population is therefore DNP on this target; reused C9/C10/C11/C12/C15 retain their `.009`
factory positions with explicit continuity-boundary nets.

The upper-left decode row is independently component-photo fitted. D8 is the socketed
К155РЕ3 PROM, D9 the adjacent metal К555ИД7 decoder, and D7 the marked black
КР1533ЛА3 package; all three are horizontal with right-facing notches. The drawing-labeled
R13 and lower R14 are fitted to their photographed horizontal landings. These corrections
replace stale vertical/overlapping seeds rather than waiving D7/D8/D9/R13/R14 collisions.

R33 and R66 retain their independently photo-registered centres and orientations. Their
nearest pads are 1.721 mm centre-to-centre; using 1.50 mm copper around the original-style
0.80 mm drills preserves a 0.35 mm annulus and provides 0.221 mm copper clearance without
moving either component.

- Guarded legacy-DNP references: `15`
- Current collision references: `none`
- Evidence: `ref/photos/dgsh5-109-009-sb/rf-option-disposition.json`

The source PCB has no copper short, clearance, or track-crossing violation and passes this gate.
