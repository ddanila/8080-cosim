# Baltijets Juku E5104 technical documentation

Source:
`https://elektroonikamuuseum.ee/failid/juku/tech_docs_from_baltijets/`

Fetched: 2026-07-06.

The directory contains 16 PDFs found in the former Baltijets factory building in
Narva and scanned in November 2024. `000 Info.pdf` is text-searchable; the other
PDFs are image scans. The adjacent `.txt` files are `pdftotext` outputs and are
empty for the scan-only PDFs.

`SHA256SUMS` records the fetched PDF hashes.

## Doc 007 ROM/programming triage

`007 ROM and ROM programming.pdf` does not close the small PROM byte-content
blocker. It confirms the existence/type/provenance of several programmed parts,
but the relevant small-PROM tables are referenced as disk-held programming
tables rather than printed in the PDF:

| Page | Drawing | Part | Finding |
|---|---|---|---|
| 16 | `ДГШ5.106.038` | `КР556РТ4` | programming table `ДГШ5.106.038 Д1`; note says `на диске` |
| 17 | `ДГШ5.106.040` | `К573РФ5` | EPROM, table `ДГШ5.106.040 Д1`; `на диске` |
| 18 | `ДГШ5.106.092` | `КР556РТ5`-class marking | programming table `ДГШ5.106.092 Д1`; `на диске` |
| 19-22 | `ДГШ5.106.106` | `К573РФ2` | printed hex listing `ДГШ5.106.106 Д1`; already low priority because РФ2 ROMs are available elsewhere |
| 23 | `ДГШ5.106.107` | `К573РФ2` | EPROM sheet, no printed byte table on the shown page |

Implication for the replica plan:

- `ДГШ5.106.037/.038` remain dump-or-disk items for the two `КР556РТ4`
  decode PROMs.
- `ДГШ5.106.039` remains the needed D8 `К155РЕ3` content.
- `ДГШ5.106.092` is confirmed in the factory set for the FDC-era PROM, but its
  bits are still not present in this PDF.
- The owner/community dump request remains necessary unless the referenced
  programming-disk files surface.

## Doc 002 schematics/components first pass

`002 Schematics and components.pdf` is a mixed packet: assembly/mechanical
drawings, component lists, applicability tables, and a few connection schematics.
It does not contain a replacement full processor-module schematic in this scan,
so it does not close the remaining CPU-board net unknowns by itself.

Useful pages identified in the first pass:

| Page | Finding |
|---|---|
| 28 | Power-supply schematic `ДГШ2.087.031 Э3`, showing +5 V/+12 V/GND connector mapping and PSU component values. Useful for WS-G PSU recreation, not processor-board LVS. |
| 29 | Power-supply element list `ДГШ2.087.031 ПЭ3`; confirms PSU capacitors, regulators, diodes, transformer, fuse, and connector types. |
| 32 | Interface-terminal connection schematic `ДГШ3.031.007 Э4`; confirms X8 power pins 62/61/60/59 and X9 signal labels including `K2`, `K0`, `K1`, `-ГК`, `+5V`, `SHIFT`, `CTRL`, `WAIT`, `STB`, `SC0`..`SC3`. Useful for bring-up cabling. |
| 34-35 | Applicability/specification table for `ДГШ5.109.009` processor module. Confirms the .009 module includes programmed microcircuits `ДГШ5.106.037`, `.038`, `.039`, `.041`, `.042`, `.043`, `.087`, `.088`, `.089`, `.090`, `.091`, `.092`, plus related module/enclosure items. |

Implication:

- The repo's .009/FDC processor-module target is corroborated by factory
  applicability tables.
- The table confirms the small PROM drawing numbers already seen in doc 007,
  but still gives no byte contents.
- The remaining net blockers in PLAN WS-A/WS-F still need either the original
  processor schematic pages, the referenced programming disk, or hardware
  continuity/dump sessions.

## Doc 010 parts-list first pass

`010 Parts list.pdf` is a parts-list/kit packet rather than the adjustment
instructions anticipated in PLAN's `010-class` placeholder. It is still useful
for sourcing:

| Page | Finding |
|---|---|
| 20 | Group комплект/BOM page includes `ДГШ5.109.009`, `КР1818ВГ93`, `КР556РТ4`, and the КР580-family logic mix. This supports the long-lead sourcing list and the .009 FDC revision target. |

Implication:

- Treat doc 010 as sourcing/census evidence, not timing/adjustment evidence.
- RAS/CAS/refresh and RF/video adjustment data still need to come from another
  adjustment document in the Baltijets set, not this parts-list PDF.
