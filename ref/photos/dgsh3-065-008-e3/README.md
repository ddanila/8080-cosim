# Juku НГМД (floppy-drive) block — `ДГШ3.065.008 Э3`

Owner photographs (2026-07-18) of **ДГШ3.065.008 Э3 «Блок НГМД Е6502 / Схема
электрическая принципиальная»**, stamped «ДУБЛИКАТ» — the floppy-drive-unit
schematic.

## Why this matters

Together with processor-module `.009` sheet 3, this drawing documents the
drive side of the floppy interface. The reviewed
[X4/НГМД map](../../schematics/fdc-x4-ngmd-wire-map.md) reconciles the
processor connector with both drive tables and their shared external connector.
Contact-number agreement establishes drawing intent; no separate cable
assembly drawing or physical cable continuity is proved by these photos.

Contents: two НГМД drive mechanisms (**ЕС5323.01 / ЕС5323.02**), their
hierarchical **X1/X2** power/signal connectors, intermediate **XS3/XS4**, and
common external **XS5** carrying the standard Shugart-style FDC signal set
(S.SEL, RD DATA, WR DATA, STEP, DIR, INDEX, W.PROT, TR.0, SEL0/SEL1, M.ON,
W.GATE, RDY, side-select), and a **БЛОК ПИТАНИЯ** power block (+5 V / +12 V from
~220 V "POWER" mains input).

## Photos

Overview frame first, then detail tiles in camera order (left-to-right,
top-to-bottom):

- `PXL_20260718_121821197.jpg` — overview
- `PXL_20260718_121826539.jpg` … `PXL_20260718_121851825.jpg` — 8 detail tiles

## Reviewed scope

The transcription covers both X1/X2 drive tables, XS3/XS4 fanout, XS5, and
the separate +5 V/+12 V power-block boundary. The drawing presents the PSU
as a named block and contains no component-level PSU circuit.
