# WD1772 PLA/PLM inspection

Status: **PLA SHAPE INSPECTED**

This generated report inspects the vendored `wd1772pla.txt` dump as a
reference artifact. It validates the text-table shape and records the
ambiguous markers that need interpretation before the table can be used as
machine equations. It does not translate the PLA into HDL.

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

## Duplicate Labels

| Label class | Duplicates |
| --- | --- |
| A labels | `A00` x2, `A01` x2, `A02` x2, `A03` x2, `A04` x2, `A05` x2, `A06` x2, `A07` x2, `A08` x2, `A09` x2, `A10` x2, `A11` x2, `A12` x2, `A13` x2, `A14` x2, `A16` x2, ... (+42) |
| R labels | `R008` x2, `R062` x2, `R063` x2, `R064` x2, `R065` x2, `R066` x2, `R085` x2, `R104` x2 |
| Input/output terms | `0010101011001110101/1001101001001111111` x2, `0011001011011110011/0101110110110111011` x2, `0100001111101110010/0101110111110101111` x2, `0111011111111111100/0001100010010011111` x2, `1001011111111111001/0111111111111111111` x2, `1111001111110000000/0111111111111111111` x2, `1111011111001100110/0111111010010011111` x2, `1111110011001111111/0000110010100101010` x2, `1111111100110011111/1111111111111111111` x2, `1111111111111111111/1111111111111111111` x3 |

## Footer Guide Rows

- `|CCCCCCCCCCCCCCCCCCC|CCCCCCCCCCCCCCCCCCC`
- `|0123456789012345678|9012345678901234567`
- `|0         1        | 2         3`
