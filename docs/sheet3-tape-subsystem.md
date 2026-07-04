# Sheet 3 (ДГШ5.109.006 Э3, лист 3) — the TAPE subsystem [DELETED in .009]
First-pass read 2026-07-04 (grind B). This whole sheet is the cassette interface of the
.006 board; the .009 FDC revision DELETED it and recycled its refdes (D93-D108) for the
FDC quadrant parts. None of these chips exist on our target board -- recorded for the
architectural record and for any future .006-variant build.

## Blocks
- D93 = КР580ВВ51А #2 (tape SIO; MAME sio[1]): D0-7 <- DB rails, RD/WR <- -IORD/-IOWR(1),
  CLK <- VIDEO CYCLE(2), CS <- [the CS7 rail from sheet-1 D9.Y7 -- see deltas]. TxRDY/RxRDY
  -> (1) = the sheet-1 IR0/IR1 rails.
- Write chain: PREN(1) [D26.PA6] -> ЛН2 D91 -> ТВ1 JK pair (D97.1/D97.2) -> ЛП2/АП2 (D95/D14)
  -> SOUT2 -> X2 pin 216 (!) and SYNC -> 501, REC.DATA -> 502 (tape connector codes).
- Read chain: DATA IN <- 504 (+503 gnd) -> R82 5.1k/R84 33k/R85-R86/C16-C18 -> К554СА3
  comparator (D106) -> data separator: ЛН2/ЛП2 (D94.3/D94.4) + ТМ2 pair (D98.1/D98.2) +
  ЛП2 D95.2 -> recovered RxC.
- Serializer/checksum: 2x ИР9 shift registers (D99, D100) + К561ИМ1 4-bit adder (D101,
  SM block S1-S4/B1-B4/C1/CO) + ЛА7 gates (D96.1-4) + ЛН2/ЛП2 glue -- hardware
  checksum/framing for tape blocks.
- Baud: К561ИЕ11 counter (D102, СТ16 block) -> TxC; input SYNC B.R.(2) = D57.OUT2.
- Deck sense/control: TAPE RUN <- 408/40 -> R88 12k/R89 130k/R100 10k -> ЛП2 D95.4 ->
  TAPE RUN INT (1) = sheet-1 IR4. CNTR CHECK -> 407/39 via ЛН2 D90.1.
- Power table (К561 series): +5(A) pins 14/16/11/26; GND 7/8/6/4 per column.

## .009-relevant deltas (feed grind C)
1. CS7 (D9.7, sheet-1) -> here = D93 tape-USART select at IO 0x1C. On .009 the same select
   goes to the ВГ93 FDC (MAME: 0x1C-0x1F = fdc) -- CS_FDC net should be D9.7 -> ВГ93 /CS zone.
2. IR0/IR1: .006 = tape TxRDY/RxRDY; .009 = ВГ93 INTRQ/DRQ [assumed; owner-verify].
3. X2 pin 216 = SOUT2 (tape audio) on .006 -- absent/repurposed on .009 (our X2 netting
   from sheet-1 D27 didn't include 216 ✓ no conflict).
4. X4 tape connector codes 401-408 + 501-504 = cassette-era; .009 repurposes the X4/X5
   bracket for FDC cabling [photo: DB-26HD at X4].
5. VIDEO CYCLE rail reaches (3) -- on .009 its sheet-3 consumer is gone; check FDC quadrant
   for a reuse before assuming it terminates.
