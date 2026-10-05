# Source PCB DRC

Status: **PASS**

The command runs fresh KiCad DRC on the source PCB. PASS and exit 0 mean
only that shorting_items, clearance, and tracks_crossing violations are
absent. Unconnected items, courtyard, silkscreen, and other violation
types do not fail this placement gate. It does not check routed variants
or authorize fabrication; see [manufacturing readiness](replica-manufacturing-readiness.md).

## Command

Run from the repository root with Python 3 and KiCad CLI available.
`scripts/find-kicad-cli.sh` selects the CLI; set `KICAD_CLI` to choose
an executable explicitly. Python uses only the standard library.
The raw DRC JSON is temporary and removed on exit. The writer replaces
this report, including when the placement gate returns exit status 1.

```sh
python3 kicad/report_source_pcb_drc.py
```

## Summary

- Board SHA256: `c1fbfcdeae9a859f76d9c46f79c570f83e7d1a98a5a136ef60e818d801482b97`
- DRC violations excluding unconnected items: `762`
- Unconnected items: `499`
- Short violations: `0`
- Copper-clearance violations: `0`
- Track-crossing violations: `0`
- Unique short-collision item groups: `0`

## Violation types

| Type | Count |
| --- | ---: |
| `courtyards_overlap` | 106 |
| `pth_inside_courtyard` | 59 |
| `silk_over_copper` | 199 |
| `silk_overlap` | 199 |
| `text_thickness` | 199 |

## Revision disposition

The `.006` RF option is excluded from this `.009` target; the evidence
record below supplies the legacy-DNP reference list. For current
component identity and placement boundaries, see
[video analog evidence](video-analog-boundary.md) and
[photo placement](analog-cluster-photo-placement.md). This DRC command
does not verify the photo registrations or component markings.

- Recorded legacy-DNP references: `15`
- Current short-collision references: `none`
- Evidence: `ref/photos/dgsh5-109-009-sb/rf-option-disposition.json`

The source PCB has no copper short, clearance, or track-crossing violation and passes this gate.
