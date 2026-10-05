# Main board fabrication readiness

Board: `kicad/juku_routed.kicad_pcb`
KiCad CLI: `/usr/bin/kicad-cli`
KiCad version: `10.0.6`
Status: **NOT READY**

Run from the repository root with Python 3 and KiCad CLI available
through `scripts/find-kicad-cli.sh` or the `KICAD_CLI` override:

```sh
python3 kicad/report_fab_readiness.py
```

The writer replaces `juku_routed-drc.json`, `SHA256SUMS` and this report
in the output directory. It derives checksums from current files; this
does not verify a previously approved checksum manifest.
The command reruns KiCad DRC on the named PCB, checks nine fabrication
files for nonempty content and expected format markers, and records their
current hashes. It does not export those files or prove they were generated
from this PCB. Gerber geometry, source-model parity, waiver acceptance,
and design release require the separate manufacturing gates.

## Gates

- Electrical/routing gate: **FAIL**
- Fabrication-file inventory gate: **FAIL**
- DRC violation entries (excluding the separate unconnected list): 798
- Unconnected items: 59

## Electrical Blockers

| Type | Count |
| --- | ---: |
| clearance | 0 |
| shorting_items | 0 |
| tracks_crossing | 0 |
| unconnected_items | 59 |

## DRC Finding Types

| Type | Count |
| --- | ---: |
| courtyards_overlap | 108 |
| pth_inside_courtyard | 68 |
| silk_over_copper | 199 |
| silk_overlap | 199 |
| text_thickness | 199 |
| track_dangling | 24 |
| via_dangling | 1 |

## Fabrication Files

| File | SHA256 | Bytes | Format markers |
| --- | --- | ---: | --- |
| juku_routed-F_Cu.gtl | - | - | FAIL |
| juku_routed-B_Cu.gbl | - | - | FAIL |
| juku_routed-F_Silkscreen.gto | - | - | FAIL |
| juku_routed-B_Silkscreen.gbo | - | - | FAIL |
| juku_routed-F_Mask.gts | - | - | FAIL |
| juku_routed-B_Mask.gbs | - | - | FAIL |
| juku_routed-Edge_Cuts.gm1 | - | - | FAIL |
| juku_routed-job.gbrjob | - | - | FAIL |
| juku_routed.drl | - | - | FAIL |

## Failures

- Missing or empty fabrication file: juku_routed-F_Cu.gtl
- Missing or empty fabrication file: juku_routed-B_Cu.gbl
- Missing or empty fabrication file: juku_routed-F_Silkscreen.gto
- Missing or empty fabrication file: juku_routed-B_Silkscreen.gbo
- Missing or empty fabrication file: juku_routed-F_Mask.gts
- Missing or empty fabrication file: juku_routed-B_Mask.gbs
- Missing or empty fabrication file: juku_routed-Edge_Cuts.gm1
- Missing or empty fabrication file: juku_routed-job.gbrjob
- Missing or empty fabrication file: juku_routed.drl

## Disposition

Do not order from this package until the failed gate(s) above are fixed.
