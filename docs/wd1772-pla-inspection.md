# WD1772 PLA/PLM inspection

Status: **PLA SHAPE INSPECTED**

This generated report inspects the vendored `wd1772pla.txt` dump as a
reference artifact. It validates the text-table shape and records the
ambiguous markers that need interpretation before the table can be used as
machine equations. It does not translate the PLA into HDL.

## Command

Run from the repository root with Python 3 (standard library only) and
`sha256sum`. The exporter overwrites the normalized JSON/CSV and
`ref/wd1772-vg93/SHA256SUMS`; the report writer overwrites this file.

```sh
(cd ref/wd1772-vg93 && sha256sum -c SHA256SUMS)
python3 scripts/export_wd1772_pla.py
python3 scripts/report_wd1772_pla_inspection.py
```

The shape guard requires 120 rows, 19-bit fields, the listed alphabets,
one row containing `9`, and three ignored footer rows. Section counts
and duplicate labels/terms are reported, not rejected. The source hash
is calculated for this report rather than compared with a pinned identity.
The exporter preserves the ambiguous bits in JSON/CSV and derives its
checksum manifest from current files. Neither command establishes PLA
signal meanings, chip timing, or equivalence to the Juku VG93 circuitry.

## Source

| Field | Value |
| --- | --- |
| File | `ref/wd1772-vg93/wd1772pla.txt` |
| SHA256 | `687a62103ae5a89a3daf4c1decb8968d730802522fa142e458031545b7a34b10` |

## Shape

| Metric | Value |
| --- | --- |
| Data rows | 120 |
| Sections | 2 |
| Rows per section | 1: 62, 2: 58 |
| Input bit width | 19 |
| Output bit width | 19 |
| Input alphabet | 01 |
| Output alphabet | 019 |
| Ignored footer guide rows | 3 |

## Ambiguities

| Item | Value |
| --- | --- |
| Row with `9` markers | `A17/R015` |
| `9` output columns (zero-based) | 0, 1, 5, 8, 9, 10, 11 |
| Raw output field | `9911191199991111111` |

## Duplicates

Counts are distinct labels or terms occurring more than once across the table.
Full rows are preserved in [the normalized export](../ref/wd1772-vg93/wd1772pla.normalized.json).

| Class | Repeated values |
| --- | --- |
| A labels | 58 |
| R labels | 8 |
| Input/output terms | 10 |
