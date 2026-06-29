# Juku E5104 — authoritative hardware map

Source: MAME `src/mame/ussr/juku.cpp` (BSD-3-Clause, by Dirk Best & Märt Põder),
copy kept at `ref/mame_juku.cpp`. Cross-checked against our own traced boot of
`ekta43.bin`. This is the ground truth for both the KiCad schematic and the HDL.

## CPU
- КР580ВМ80А (i8080A). Reset → PC=0x0000.
- Reset vector: `C3 17 00` = `JMP 0x0017`; bytes at 0x0017 are a signature that
  executes as undocumented NOPs and falls through to `JMP 0x01A8` (real init).

## Memory — 64 KB DRAM + a 4-mode ROM overlay ("memory view")
Base is 64 KB RAM (the 20× К565РУ5). A view overlays ROM; mode = **8255#0 Port C
bits[1:0]** (see I/O). Reset mode = 0.

| mode | overlay | rest |
|------|---------|------|
| 0 (reset) | ROM `0x0000–0x3FFF` (maincpu +0x0000) | RAM |
| 1 | ROM `0xD800–0xFFFF` (maincpu +0x1800) | RAM `0x0000–0xD7FF` |
| 2 | expansion cart `0x4000–0xBFFF` + ROM `0xD800–0xFFFF` | RAM |
| 3 | (none) | all RAM |

- Writes under an active ROM overlay are dropped (ROM is read-only, no write-through).
- ROM region `maincpu` = 16 KB = `ekta43.bin` loaded flat at offset 0.
- Stack lives at `0xD450` (set by init) — RAM, writable in mode 0.

## Video
- Monochrome bitmap, **base `0xD800`**, read straight from DRAM (independent of CPU bank).
- Default geometry 320×241; **stride = WIDTH/8 = 40 bytes/line**, MSB = leftmost pixel.
- Geometry is programmable via I/O writes (see screen_* ports below); BIOS text mode
  is "53×24 b/w".

## I/O map (8080 IN/OUT port space)
| ports | device | notes |
|-------|--------|-------|
| `0x00–0x01` | 8259 PIC | interrupt controller |
| `0x04–0x07` | 8255 PPI #0 | A=`04` (kbd column/strobe/beep, **output, reads return latch**), B=`05` (kbd data in), **C=`06` → mem mode + floppy ctrl**, ctrl=`07` |
| `0x08–0x0B` | 8251 USART #0 | serial |
| `0x0C–0x0F` | 8255 PPI #1 | ctrl word `0x9B` |
| `0x10–0x13` | 8253 PIT #0 | also: `10`=screen_width, `11`=h-blank, `12`=h-front-porch (write taps) |
| `0x14–0x17` | 8253 PIT #1 | also: `14`=screen_height, `15`=v-blank, `16`=v-front-porch |
| `0x18–0x1B` | 8253 PIT #2 | |
| `0x1C–0x1F` | КР1818ВГ93 (WD1793) | FDC; `1C`=cmd, `1F`=data |
| `0x80` | mouse | |

## Interrupts (8259 IR lines)
- IR5 ← PIT#1 out1 (~49.92 Hz "frame interrupt")
- IR2/IR3 ← USART#0 rxrdy/txrdy; IR0/IR1 ← USART#1; IR6 ← mouse
- PIC INT → 8080 INT line; 8080 INTA → PIC acknowledge (returns interrupt opcode)

## Keyboard
- Column strobed out on 8255#0 Port A (bits 3:0 = column, bit7 = strobe).
- Data read back via 8255#0 Port B (key data + shift/ctrl + valid bit) through a
  key-encoder device. **This handshake is what our boot currently stalls on** — see
  `boot-findings.md`.
