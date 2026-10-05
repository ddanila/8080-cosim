# FDC lower assembly placement

Status: **FACTORY PLACEMENT EVIDENCE / PARTIAL ELECTRICAL MAPPING**

Regenerate from the repository root with
`/usr/bin/python3 kicad/report_fdc_lower_assembly_placement.py`.
That interpreter needs KiCad's `pcbnew` module and Pillow; materialize
the original images through [Git LFS](git-lfs-policy.md#local-use).
The writer reads [the registration record](../ref/photos/dgsh5-109-009-sb/fdc-lower-placement-registration.json),
the canonical board JSON and source PCB. It overwrites this report,
[its JSON companion](fdc-lower-assembly-placement.json), and its review overlay.

The guard checks registration records, selected photo hashes and coordinates,
component values, and source-PCB placement/local joins. It does not establish
unobserved copper continuity or measure installed capacitances.
Held-out errors must be at most 1 mm. The restored-part subset in
[the writer](../kicad/report_fdc_lower_assembly_placement.py) must have
footprints within 0.02 mm of its recorded centres. Other targets are
reported without that placement gate; selected pad nets and values are
checked only when their footprints exist.

C12's population and lap-lead evidence belong to the
[upper assembly report](fdc-upper-assembly-placement.md) and its
[registration record](../ref/photos/dgsh5-109-009-sb/fdc-upper-placement-registration.json).

The photographed factory assembly drawing is registered to the five package centres
already fitted in the owner board photograph. D95, D101, and D102 define the affine
fit; D99 and D97 are independent checks. This establishes reference identity and
placement only, except where the linked owner-evidence records explicitly close
R79-R85/R93/R94/R95/R98 plus R92/R99/R100/R102/R108/R86 values or visible copper connectivity.

Held-out errors: D99 `0.910` mm; D97 `0.851` mm.

| Ref | Projected x,y mm | Current x,y mm | Delta mm |
| --- | ---: | ---: | ---: |
| D93 | 235.941, 73.335 | 235.941, 73.340 | -0.000, -0.005 |
| R79 | 292.431, 19.166 | 292.431, 19.166 | -0.000, +0.000 |
| R80 | 290.248, 19.189 | 290.248, 19.189 | +0.000, +0.000 |
| R81 | 288.066, 19.212 | 288.066, 19.212 | -0.000, +0.000 |
| R82 | 285.883, 19.235 | 285.883, 19.235 | +0.000, +0.000 |
| R83 | 283.701, 19.258 | 283.701, 19.258 | -0.000, +0.000 |
| R84 | 245.220, 97.300 | 245.220, 97.300 | +0.000, +0.000 |
| R85 | 278.302, 66.090 | 278.302, 66.090 | +0.000, +0.000 |
| R94 | 271.987, 54.141 | 271.987, 54.141 | +0.000, -0.000 |
| R93 | 277.444, 54.083 | 277.443, 54.083 | +0.001, +0.000 |
| R95 | 282.852, 54.319 | 282.852, 54.319 | +0.000, +0.000 |
| R78 | 267.999, 68.177 | 267.999, 68.177 | +0.000, +0.000 |
| R98 | 270.485, 68.177 | 270.485, 68.177 | +0.000, +0.000 |
| C10 | 252.361, 73.163 | 252.361, 73.163 | +0.000, -0.000 |
| C11 | 268.232, 93.540 | 268.232, 93.540 | +0.000, +0.000 |
| C16 | 267.094, 101.055 | 267.094, 101.055 | +0.000, +0.000 |
| C15 | 280.230, 110.120 | 280.230, 110.120 | +0.000, -0.000 |
| C19 | 292.893, 93.574 | 292.893, 93.574 | +0.000, -0.000 |
| R92 | 253.869, 101.194 | 253.869, 101.194 | +0.000, +0.000 |
| R99 | 241.207, 103.467 | 241.207, 103.467 | +0.000, -0.000 |
| R100 | 299.776, 94.000 | 299.776, 94.000 | -0.000, -0.000 |
| R102 | 299.253, 97.229 | 299.253, 97.229 | +0.000, +0.000 |
| R108 | 298.731, 100.458 | 298.731, 100.458 | -0.000, +0.000 |
| R86 | 298.208, 103.688 | 298.208, 103.688 | +0.000, -0.000 |
| C20 | 299.917, 110.117 | 303.997, 110.024 | -4.080, +0.093 |
| C22 | 302.204, 110.093 | 306.537, 110.024 | -4.333, +0.069 |
| C17 | 303.000, 55.000 | 303.017, 55.000 | -0.017, +0.000 |
| R103 | 307.200, 47.200 | 307.200, 47.200 | +0.000, +0.000 |
| C18 | 303.000, 70.000 | 303.017, 70.000 | -0.017, +0.000 |
| R97 | 298.620, 67.150 | 298.620, 67.150 | +0.000, +0.000 |
| C83 | 239.150, 140.065 | absent | - |

D93, C10, C11, C15, C16, C19, R79-R85, R92/R93/R94/R95/R98/R99, and the populated R100/R102/R108/R86 right-edge row have source-PCB footprints at the recorded coordinates in the table.
These use factory-drawing registration or stronger owner-photo lead evidence;
the JSON companion retains each target's observations and source coordinates.
C20/C22 have source-PCB footprints, but their table deltas are intentional: the drawing points identify the
overlapping body labels, whereas registered owner component and solder photos prove the actual adjacent 2.54 mm drill columns
at `(303.997,110.024)` and `(306.537,110.024)` mm with 10 mm vertical pad spans.

The owner photos confirm C16/C19, C20/C22, R92/R99, and the R100/R102/R108/R86 row. Their drill registration, pad order, and visible joins are documented in [analog-cluster placement](analog-cluster-photo-placement.md).
R92/R99 read 1.3 kΩ/4.7 kΩ; R100/R102/R108 read 12 kΩ and R86 reads 4.7 kΩ. C16 reads bare `27`; C19/C20/C22 read bare `22`. The schematic nominal values are 27/22 pF, but installed capacitances remain unverified. See [native capacitor values](native-capacitor-values.md) and the [FDC precomp map](../ref/schematics/fdc-write-precomp-map.md) for value boundaries and source connections.

C83 is absent from the owner board's D41/D40 gap. The factory drawing labels the intended part `C83`; candidate front sites align with solder crowns, but their identity needs continuity. The logical model connects C83 to +5 V/GND; physical placement and the owner-board pad pair remain unresolved. The photos cannot distinguish omission at assembly from later removal. C63 is a separate bare inherited DRAM-grid footprint.

The later July owner image `PXL_20260710_202708344.jpg` exposes green two-lead
bodies at the factory C10 and C11 positions. Their values and lead rails remain
unproved. Two later views show
a green C15-position body edge between D97/D102, but the cable hides its
second lead, so component identity and rails remain candidate evidence.
See [late bypass evidence](../ref/photos/juku-pcb-2/fdc-bypass-late-population-review.json).
