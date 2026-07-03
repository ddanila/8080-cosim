# MAME juku.cpp -> hardware interface map (round-1 desk mining, 2026-07-03)
Source: ref/mame_juku.cpp (the MAME team's reverse-engineering of the E5101/E5104).
Behavioral truth for chip-to-chip wiring; pin numbers below are datasheet pinouts.

## I/O map (validates our D9 ИД7 decode 1:1)
| ports | device | our refdes | D9 output |
|-------|--------|-----------|-----------|
| 00-03 | ВН59 PIC | D10 | Y0 (pin 7) ✓ netted |
| 04-07 | ВВ55А #1 (kbd/floppy-ctl) | D26 | Y1 (9) ✓ |
| 08-0B | ВВ51А USART | D11 | Y2 (10) ✓ |
| 0C-0F | ВВ55А #2 (X2 parallel?) | D27 | Y3 (11) ✓ |
| 10-13 | ВИ53 #1 | D54 | Y4 (12) ✓ |
| 14-17 | ВИ53 #2 | D55 | Y5 (13) ✓ |
| 18-1B | ВИ53 #3 (baud/sound) | D57 | Y6 (14) ✓ |
| 1C-1F | ВГ93 FDC | D93 | **Y7 (15) — net to add** |

## PIC (D10) IR table
IR0/IR1 = tape-USART#2 Rx/TxRDY (cassette E5101) -> on FDC-era .009 likely ВГ93 INTRQ/DRQ [assumed]
IR2 = D11 RxRDY (8251 pin 14), IR3 = D11 TxRDY (pin 15)
IR4 = TAPE RUN INT (sheet-1) | IR5 = FRAME INT = D55 OUT1 | IR6 = mouse INT (X1 bus, -INT6)
IR7 = X1 -INT7 (netted, beeper session)

## PIT cascade (8253 pins: CLK0=9 G0=11 OUT0=10 CLK1=15 G1=14 OUT1=13 CLK2=18 G2=16 OUT2=17)
D54 (PIT#1, video horiz): CLK0=CLK1=CLK2 = 1 MHz (16MHz/16 from the D40 mesh divider)
  OUT0 -> D55.CLK0 + D54.GATE1 + D54.GATE2      (net PIT_HCHAIN)
  OUT1 = HOR RTR (video)                         (destination untraced)
  OUT2 = HOR SYNC DSL -> D55.CLK1 + D55.CLK2     (net PIT_HSYNC_DSL)
D55 (PIT#2, video vert): OUT0 -> D55.GATE1 + D55.GATE2  (net PIT_VCHAIN)
  OUT1 = VER RTR / FRAME INT (~50Hz) -> D10.IR5(23) + D57.CLK2  (net FRAME_INT)
  OUT2 = VERT SYNC DSL
D57 (PIT#3): CLK0 = 16/13 = 1.23 MHz, CLK1 = 2 MHz
  OUT0 = BAUD -> D11 RxC(25)+TxC(9) [assumed]    OUT1 = SOUND -> beep gate chain (D13/D92 zone)
  OUT2 = SYNC BAUD

## ВВ55А D26 (pio0) port map (8255 pins: PA0-3=4,3,2,1; PB0-7=18..25; PC0-7=14,15,16,17,13,12,11,10)
PortA out: 7=STB 6=PREN 4=AUDC(beep level) 3..0=keyboard column select -> X9
PortB in:  7=CTRL 6=SHIFT 5,4=contrdat 3..1=key code (К155ИВ1 encoder ON THE KEYBOARD) 0=pressed
           **PB5 (pin 23) = X9 pin 9 -- owner-measured ✓**
PortC out: 1,0 = MEMORY MODE (the D8 РЕ3 window pager select!) ; 2=motor 3=size 4=density
           5=drive-sel 6=side-sel 7=pof (FDC-era meanings; cassette-era: rec/play/ff/rn/stop/pof)
=> X9 (keyboard, bottom edge x~208) carries: PA0-3, PB0-7 signals, +5V/GND. Only pin 9 known.

## Conflict flagged for round 2 (sheet-1 re-read)
D8_D0/D1/D2 -> D9.A/B/C nets contradict the .117 РЕ3 contents for ports 00-1F (a[4:2]=000 -> FF,
no discrimination). The IO select coupling is probably D2 (РТ4 .037) -> D9, with the sheet's
"D8" refdes being the schematic numbering, not the board's. Verify on sheet 1.

## Clocks
CPU = 2 MHz (МАМЕ: 20MHz/10; board: 16MHz РК171 -> mesh /8). Video dot = 16MHz. PIT base = 1MHz.
FDC clock = 1 MHz (16/16).
