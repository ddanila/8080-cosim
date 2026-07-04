# FDC quadrant scaffold (grind C, 2026-07-04)
The .009 revision's floppy subsystem, netted to the extent the desk sources allow.

## Netted (this pass)
- **D93 КР1818ВГ93** (WD1793 pinout): CS(3) <- D9.Y7 [the sheet-3 CS7 delta: io 0x1C],
  RE(4) <- IORD, WE(2) <- IOWR, A0/A1 <- BA0/BA1, DAL0-7 <- D100 B-side,
  DDEN(37) <- D26.PC4 [MAME], INTRQ(39) -> D10.IR0 [assumed], DRQ(38) -> D10.IR1 [assumed].
- **D100 КР580ВА87** (8287): A-side <- DB0-7, B-side -> FDC_DAL0-7. OE/T gating [assumed
  boundary -- likely CS_FDC + IORD-derived].
- **D94 К155РЕ3** (.113 table): A0-A4 <- BA11-15 (same convention as D8); outputs = 2K
  selects over A000-BFFF; destinations unknown (FDC buffer RAM enables?) [owner].
- HDL: inert stubs (never drive DAL/DB/IRQ) -- boot stays byte-identical; connectivity
  is the deliverable. PIC grew ir0/ir1 structural inputs.

## Not netted (owner-session territory)
Support logic: D95/D101 (КП12 muxes -- drive/side select fanout?), D97/D99/D102 (АГ3
one-shots -- step/precomp timing), D96 (ТМ2), D28 (ЛН3), D98 (ЛП11 + the wires-17/18
reset chain), D106 (ИЕ7), D107? no -- D106 counter; the drive cable connector (X4/X5,
DB-26HD per photo); MR source; 1 MHz CLK rail; VT2/VT4 analog (write precomp/pump).

## Owner measurement list (FDC)
1. D93.39/38 -> D10.18/19 (IR0/IR1) -- confirm which is INTRQ vs DRQ.
2. D93.19 (MR) source; D93.24 (CLK) rail (expect 1 MHz mesh tap).
3. D100.9/11 (OE/T) gating logic.
4. D94 output destinations (8 lines).
5. КП12/АГ3 pin wiring; drive cable pinout at the bracket.
6. Wires 17/18: D98.7 -> 220R -> reset switch chain.
