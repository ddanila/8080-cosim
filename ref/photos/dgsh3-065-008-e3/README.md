# Juku НГМД (floppy-drive) block — `ДГШ3.065.008 Э3`

Owner photographs (2026-07-18) of **ДГШ3.065.008 Э3 «Блок НГМД Е6502 / Схема
электрическая принципиальная»**, stamped «ДУБЛИКАТ» — the floppy-drive-unit
schematic.

## Why this matters

This was the **highest-value document lead** tracked in `PLAN.md`: the FDC-era
floppy interface was only partially known, and the МАМЕ Juku driver's own TODO
still reads "work out how the floppy interface really works" (juku3000 #25).
Together with the processor board's FDC sheet (`ref/photos/dgsh5-109-009-e3/`,
sheet 3, КР1818ВГ93), this drawing gives the **drive side** of that interface —
the mating pinout of the processor board's X4 drive connector — so the two can
be reconciled end to end. This is the connector cross-check the import was
requested for.

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

## TODO

- [x] Extract the X1/X2/XS3/XS4/XS5 pinout and reconcile it against the
      processor board's X4 (sheet 3, `dgsh5-109-009-e3/`) and the VG93 signal
      contract (`ref/schematics/fdc-x4-ngmd-wire-map.md`).
- [x] Complete the drawing-level transcription: both drive X1/X2 tables,
      XS3/XS4 fanout, XS5, and the separate +5 V/+12 V power-block boundary
      are covered by that map. The Э3 presents the PSU as a named block and
      contains no component-level PSU circuit.
