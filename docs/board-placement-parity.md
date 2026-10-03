# Source-to-routed footprint placement parity

This compares footprint reference, placement anchor, and rotation in the source PCB with both routed variants. Tolerance: 0.01 mm and 0.1°. It does not verify whether the source PCB itself matches the owner board or whether copper follows a moved footprint.

The coordinates are KiCad footprint placement anchors, which can differ
from package or pad-array centers. Footprint geometry and pad nets are not
compared. A nonzero exit status reports placement gaps.

## Command

```sh
/usr/bin/python3 kicad/report_board_placement_parity.py
```

| Routed PCB | Missing source refs | Extra refs | Moved/rotated refs |
| --- | --- | --- | --- |
| `kicad/juku_routed.kicad_pcb` | R10, R9 | none | D11, D12, D26, D27, D42, D43, D58, D59, D6, D9 |
| `kicad/juku_routed_candidate.kicad_pcb` | R10, R9 | none | D11, D12, D26, D27, D42, D43, D58, D59, D6, D9 |

## Position differences

| Routed PCB | Ref | Source anchor / rotation | Routed anchor / rotation |
| --- | --- | --- | --- |
| `juku_routed.kicad_pcb` | `D11` | (193.392, 54.976) mm / 0.0° | (177.880, 49.190) mm / 0.0° |
| `juku_routed.kicad_pcb` | `D12` | (224.535, 67.630) mm / 180.0° | (202.495, 77.090) mm / 0.0° |
| `juku_routed.kicad_pcb` | `D26` | (256.125, 243.380) mm / 270.0° | (207.875, 258.620) mm / 90.0° |
| `juku_routed.kicad_pcb` | `D27` | (175.825, 28.080) mm / 270.0° | (127.575, 43.320) mm / 90.0° |
| `juku_routed.kicad_pcb` | `D42` | (143.620, 255.195) mm / 270.0° | (128.380, 262.805) mm / 90.0° |
| `juku_routed.kicad_pcb` | `D43` | (167.220, 255.695) mm / 270.0° | (151.980, 263.305) mm / 90.0° |
| `juku_routed.kicad_pcb` | `D58` | (194.430, 239.295) mm / 270.0° | (171.570, 246.905) mm / 90.0° |
| `juku_routed.kicad_pcb` | `D59` | (114.220, 253.195) mm / 270.0° | (98.980, 260.805) mm / 90.0° |
| `juku_routed.kicad_pcb` | `D6` | (66.550, 109.360) mm / 270.0° | (54.910, 117.905) mm / 90.0° |
| `juku_routed.kicad_pcb` | `D9` | (116.770, 109.400) mm / 270.0° | (118.813, 109.498) mm / 270.0° |
| `juku_routed_candidate.kicad_pcb` | `D11` | (193.392, 54.976) mm / 0.0° | (177.880, 49.190) mm / 0.0° |
| `juku_routed_candidate.kicad_pcb` | `D12` | (224.535, 67.630) mm / 180.0° | (202.495, 77.090) mm / 0.0° |
| `juku_routed_candidate.kicad_pcb` | `D26` | (256.125, 243.380) mm / 270.0° | (207.875, 258.620) mm / 90.0° |
| `juku_routed_candidate.kicad_pcb` | `D27` | (175.825, 28.080) mm / 270.0° | (127.575, 43.320) mm / 90.0° |
| `juku_routed_candidate.kicad_pcb` | `D42` | (143.620, 255.195) mm / 270.0° | (128.380, 262.805) mm / 90.0° |
| `juku_routed_candidate.kicad_pcb` | `D43` | (167.220, 255.695) mm / 270.0° | (151.980, 263.305) mm / 90.0° |
| `juku_routed_candidate.kicad_pcb` | `D58` | (194.430, 239.295) mm / 270.0° | (171.570, 246.905) mm / 90.0° |
| `juku_routed_candidate.kicad_pcb` | `D59` | (114.220, 253.195) mm / 270.0° | (98.980, 260.805) mm / 90.0° |
| `juku_routed_candidate.kicad_pcb` | `D6` | (66.550, 109.360) mm / 270.0° | (54.910, 117.905) mm / 90.0° |
| `juku_routed_candidate.kicad_pcb` | `D9` | (116.770, 109.400) mm / 270.0° | (118.813, 109.498) mm / 270.0° |

The source PCB now places D11 at the two-view owner-photo position; both routed variants retain the old D11 position and copper. The exact .009 assembly and owner component image place D12 above D3 (`ref/photos/juku-pcb-2/d12-d3-local-placement.json`); the source PCB has that corrected placement. Both routed variants retain D12's old left-of-D3 estimate inside the corrected D11 area and omit source-placed R9/R10. D26, D27, D6, and D9 also differ as listed above; see their individual placement audits and `docs/r9-r10-routed-collision-audit.md`.
