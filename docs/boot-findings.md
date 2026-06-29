# Boot findings — ekta43.bin (RomBios 2.43m, EktaSoft '90)

Empirical results from `cosim/trace.c` (traced superzazu 8080, MIT) running the
16 KB ROM from reset with a naive map (ROM read-only `0x0000..0x3FFF`,
RAM `0x4000..0xFFFF`, all `IN` = 0).

## Confirmed

- **ROM:** 16384 bytes, mapped at `0x0000`, reset vector `C3 17 00` = `JMP 0x0017`.
- **Banner strings present:** `'EktaSoft '90  Serial #0043`, `Screen b/w 53x24/+wnd`,
  `IBM AT keyboard`, `Parallel printer`, `DiskBios (Fdc 1793...)`,
  `System from <D>isk, <T>ape, ?` (the boot prompt).
- **I/O port map — matches the chip inventory exactly:**
  | ports | chip | notes |
  |-------|------|-------|
  | `0x04–0x07` | 8255 PPI #1 | ctrl@`0x07`←`0x82`; `IN 0x04` is polled |
  | `0x0C–0x0F` | 8255 PPI #2 | ctrl@`0x0F`←`0x9B` (all-input mode word) |
  | `0x10–0x13` | 8253 timer #1 | |
  | `0x14–0x17` | 8253 timer #2 | |
  | `0x18–0x1B` | 8253 timer #3 | |
  - 8251 USART (2 ports) not touched during early boot.
- **Decoded routines:**
  - `0x0248`: RAM fill — `MVI M,0x55 / INX H / DCX D / ORA / JNZ`, fills
    `0xD300` len `0x2D00` (i.e. `0xD300..0xFFFF`) with `0x55`; `0x0257` verifies.
  - `0x047B`: software delay loop (`MOV A,D / ORA E / RZ / DCX D / JMP`).
  - `0x00CE`: **real error trap** — `OUT 0x07` then `JMP 0x00D2` spin forever.
    We never reach it ⇒ RAM tests are PASSING.

## The wall (open problem)

Boot **never completes**: even at 400M cycles the CPU is cycling RAM-fill +
delay and **never draws the banner**. Notable facts:

- `iff = 0` throughout ⇒ it is **not** waiting on an interrupt.
- Returning `0xFF` for all `IN` ports changes nothing ⇒ not a simple status poll.
- **Every** RAM write lands in `0xD300..0xFFFF`; no separate video region is ever
  written ⇒ it's stuck *before* drawing text.
- Rendering `0xD300..0xFFFF` at 64 B/line shows the `0x55` RAM-test comb, not text.

### Leading hypotheses (next session)

1. **Memory map / banking is wrong.** The reset bytes at `0x0017` disassemble as
   two back-to-back `LXI B` (dead code) — a smell that the ROM is *not* simply
   based at `0x0000`, or that there is ROM/RAM banking (recall the blocked writes
   aimed at `0x0000`). The Juku likely relocates ROM and/or banks RAM under it.
2. Need the **actual Juku memory + I/O map** to settle this. This is exactly the
   info the KiCad schematic (the whole point of the project) encodes — so the PCB
   model and the emulator feed each other.

### Concrete next steps

- Add an **instruction-level disassembling tracer** (log PC/opcode/regs) to follow
  the boot call-flow and find where it loops.
- Model **RAM-under-ROM / banking** once the control port is identified.
- Cross-check against the schematic's address-decode logic when available.
