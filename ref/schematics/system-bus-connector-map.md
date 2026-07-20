# System-bus connector cross-check

Status: **SIGNAL CORE MATCHES / POWER MAP IS A DOCUMENTED VARIANT CONFLICT**

This reviewed transcription compares the `ДГШ5.106.103 Э3` 32 KiB
memory card's `XP` edge contacts with processor-module `.009` connector
`X1`, then records the `ДГШ3.031.011 Э6` terminal-level cable map.
The two drawings independently agree on every exposed data, address, and
listed control contact. They do **not** agree on all power contacts, so the
`.106.103` card must not be treated as a drop-in `.009` expansion card.

## Guarded primary frames

- `ref/photos/dgsh5-106-103-e3/PXL_20260718_122444769.MP.jpg` — SHA256 `4cc84a693fd8c19d720f8cae342fde43fce0a78ae3862092cb45f85409658785`
- `ref/photos/dgsh5-106-103-e3/PXL_20260718_122448921.jpg` — SHA256 `716176af3e731cff9a3a0ef992f06580fa66b405018ee6c83273eb463216461d`
- `ref/photos/dgsh5-106-103-e3/PXL_20260718_122454044.jpg` — SHA256 `be0fe8cee15270f25fffb1cfba9d1e1f211304e80b6b352516a006155ae00c18`
- `ref/photos/dgsh3-031-011-e6/PXL_20260718_121242143.jpg` — SHA256 `ae1a33258ca2b344b0457e5800a1fb793bb09583634ca786b4dc9cdc52434b6e`
- `ref/photos/dgsh3-031-011-e6/PXL_20260718_121246801.jpg` — SHA256 `4403fe67089d3e0fcb51240be0dcf9f804ba8f64115962a1d5bf14e8ba3ee03a`
- `ref/photos/dgsh3-031-011-e6/PXL_20260718_121250335.jpg` — SHA256 `f2835d46113713fe040a1bc0ae0d398564e7425d74d4b23684553ca6ce86613a`

The card overview and two overlapping detail reads independently cover
the XP labels. The system overview plus both details cover the complete
block/cable drawing. Contact codes below use the processor repository's
three-character form: card `C32` is processor `132C`, etc.

## Shared bus signal core

| X1/XP contact | Card label | Main-board model | Result |
| --- | --- | --- | --- |
| `132C` | `-D0` | `DAT0` | PASS |
| `132B` | `-D1` | `DAT1` | PASS |
| `131C` | `-D2` | `DAT2` | PASS |
| `131B` | `-D3` | `DAT3` | PASS |
| `130C` | `-D4` | `DAT4` | PASS |
| `130B` | `-D5` | `DAT5` | PASS |
| `129C` | `-D6` | `DAT6` | PASS |
| `129B` | `-D7` | `DAT7` | PASS |
| `124C` | `-ADR0` | `ADR_LO0` | PASS |
| `124B` | `-ADR1` | `ADR_LO1` | PASS |
| `123C` | `-ADR2` | `ADR_LO2` | PASS |
| `123B` | `-ADR3` | `ADR_LO3` | PASS |
| `122C` | `-ADR4` | `ADR_LO4` | PASS |
| `122B` | `-ADR5` | `ADR_LO5` | PASS |
| `121C` | `-ADR6` | `ADR_LO6` | PASS |
| `121B` | `-ADR7` | `ADR_LO7` | PASS |
| `120C` | `-ADR8` | `ADR_HI0` | PASS |
| `120B` | `-ADR9` | `ADR_HI1` | PASS |
| `119C` | `-ADRA` | `ADR_HI2` | PASS |
| `119B` | `-ADRB` | `ADR_HI3` | PASS |
| `118C` | `-ADRC` | `ADR_HI4` | PASS |
| `118B` | `-ADRD` | `ADR_HI5` | PASS |
| `117C` | `-ADRE` | `ADR_HI6` | PASS |
| `117B` | `-ADRF` | `ADR_HI7` | PASS |
| `109B` | `-IOM` | `IOM_N` | PASS |
| `104C` | `-MRDC` | `MRC_N` | PASS |
| `102B` | `-AMWTC` | `AMWC_N` | PASS |
| `106B` | `-INHIBIT` | `INHIB_N` | PASS |

The recovered card exposes ADR0 through ADRF (16 address bits), not
ADR0 through ADR17. Its four shown controls are `-IOM`, `-MRDC`,
`-AMWTC`, and `-INHIBIT`; these match `IOM_N`, `MRC_N`, `AMWC_N`, and
`INHIB_N` at the identical contacts in `kicad/juku.board.json`.

## Power-contact conflict

| Drawing/model | +5 V contacts | Ground contacts |
| --- | --- | --- |
| `.106.103` card | `106A, 107A, 108A, 108B, 108C` | `101A, 102A, 103A, 104A, 124A, 125A, 126A, 127A` |
| `.109.009` processor | `101A, 102A, 103A, 107A, 108A, 108B, 108C` | not redrawn from the card |

The drawings agree on +5 V at `107A, 108A, 108B, 108C` but
conflict directly at `101A, 102A, 103A`: the card grounds
those contacts while the exact `.009` processor sheet-1 power corner
labels them +5 V. The card additionally uses `106A` for +5 V. This is
not resolved by signal-name inference. The `.009` drawing remains
normative for the replica; no processor-board rail was changed.

## System-level cable map (`ДГШ3.031.011 Э6`)

| A1 E5101 connector | Conductors | Destination | Destination contact |
| --- | ---: | --- | ---: |
| `X1 / XP1` | 96 | A2.1 keyboard controller E4701 **or** A2.2 removable memory expander E6201 | `XP1` |
| `X2` | 30 | A3 printer СМ6329.02 / К6312М | 39 |
| `X4` | 23 | A4 НГМД block E6502 (`ДГШ3.065.008`) | 23 |
| `X6` | 2 | A5 display МС6105.09 | 2 |

The drawing also shows A1 `X3` contact 12 on the mains/switch harness;
it does not show an `X5` signal cable. Cable callouts 4, 5, and 6 are
respectively `ДГШ4.853.035`, `.042`, and `.043`; the A2 connection is
the drawing's alternative position 7 rather than evidence that both A2
modules are installed simultaneously.

## Disposition

- The main-board data/address/control model is independently corroborated.
- The `.106.103` README's former ADR17 claim is corrected to ADRF.
- The power conflict is a variant boundary and a bench safety warning,
  not permission to merge either rail map.
- A future `.106.102` drawing or backplane wiring table is required before
  claiming the E6201 module shown in the system drawing is pin-compatible
  with either connector map.
