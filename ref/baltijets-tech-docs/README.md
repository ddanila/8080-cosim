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
