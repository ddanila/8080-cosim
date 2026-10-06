# К155РЕ3 firmware inspection

Status: **PASS**

This generated report preserves the tracked owner-scan РЕ3 programming
tables under `ref/firmware/` and keeps their role bounded. The files are
real factory programming-table excerpts, but current board evidence says
they are **not** the processor-module D8 `.039` or D94 `.092` contents.

## Command

Run from the repository root with Python 3 (standard library only).
The reference guard also requires Bash, `sha256sum`, `awk`, `head`,
`grep` and `file`, plus materialized owner-photo Git LFS objects.
The writer replaces this report and the firmware checksum manifest.

```sh
sync/reference_artifact_check.sh
python3 scripts/report_re3_firmware_inspection.py
```

The writer compares retained HEX bytes with hard-coded transcriptions and
the retained physical D8/D94 tables. It does not reread the scan or verify
drawing-to-socket identity. It rewrites `ref/firmware/SHA256SUMS` from the
current artifacts rather than checking them against fixed historical hashes.
The separate reference-artifact guard checks the registered source identities.

## Shape Checks

| Check | Result |
| --- | --- |
| `.113` byte count is 32 | PASS |
| `.117` byte count is 32 | PASS |
| `.113` matches the scanned sparse 14h-17h one-cold walk | PASS |
| `.117` matches the scanned 08h-17h four-row one-cold dwell | PASS |
| Both tables use only `FF`, `07`, `0B`, `0D`, `0E` | PASS |
| The two scanned tables are distinct | PASS |
| Neither scanned table matches physical D8 or D94 | PASS |
| Physical D8 supersedes and differs from the historical reconstruction | PASS |

## Tables

| Programmed drawing | Primary use | Row summary |
| --- | --- | --- |
| `ДГШ5.106.113` | `ДГШ5.106.103` family | `00-13:FF, 14:07, 15:0B, 16:0D, 17:0E, 18-1F:FF` |
| `ДГШ5.106.117` | `ДГШ5.106.103` family | `00-07:FF, 08-0B:07, 0C-0F:0B, 10-13:0D, 14-17:0E, 18-1F:FF` |

Artifact checksums are in [the firmware manifest](../ref/firmware/SHA256SUMS).


## Interpretation Boundary

- `.113` and `.117` are not exported as D8/D94 burnable fallbacks: the processor-module
  parts list names D8 as `ДГШ5.106.039`, and the `.009` FDC revision adds
  D94 as `ДГШ5.106.092`; neither scanned table represents those parts.
- The one-cold shape suggests timing/phase selection; this is an
  interpretation, not a verified circuit role or socket assignment.
- Repeated physical D8 `.039` and D94 `.092` reads are preserved under
  `ref/physical-proms/validated/`; the former D8 reconstruction is
  retained only to make the 19-row mismatch auditable.
- Programming-disk copies could independently corroborate the retained
  tables. Their absence does not invalidate the adopted physical captures.
