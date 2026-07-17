# VJUGA rev B — modular card + backplane design

New parallel approach (rev A, the 200×200 4-layer board, is **not** scrapped). Goal:
several **≤100×100 mm** cards on a **passive backplane**, so production is cheap (2-layer,
price cliff) and you re-spin one small card instead of a big 4-layer board.

## Bus: RC2014
0.1" pin header/socket, Z80-native (A0–15, D0–7, real Z80 control, clock, power).
Chosen over ISA 8-bit (8088/XT baggage) and card-edge fingers (gold + bevel upcharge).
Reusing the RC2014 bus means the **bus contract is mostly pre-defined**. The RC2014
*interface* is freely implementable; only the specific board Gerbers are restricted
(mainline = commercial license; the salfter respin = no license = all rights reserved).
So we **reuse ideas, draw our own boards** — see below.

### The ≤100 mm problem and the fix (idea from salfter/rc2014-compat)
Mainline RC2014's 40-pin 0.1" bus spans ~102 mm → just over the 100×100 cheap-tier
cliff, and the standard bus lacks /WAIT. salfter's respin solves both with a scheme we
adopt (concept only, not his files):
- **39-pin base connector** (~96.5 mm) → fits under 100 mm → the $2 JLCPCB tier.
- **Separate 10-pin extension** carrying the signals the standard bus lacks — **/WAIT,
  /NMI, and a second clock**. This gives us WAIT (needed for video contention) *without*
  going to the wide 80-pin enhanced backplane. **Supersedes the earlier "use an 80-pin
  enhanced backplane" note.**
- **Daisy-chain connectors on opposite card edges** for expansion; **2-layer** (backplane
  routable even single-sided).
- **Backplane carries housekeeping**: USB-C power in, reset circuit, TTL UART, power LED —
  so those aren't per-card.
- Extension must be **bussed across all slots** (not per-card) or /WAIT is useless.
- Not pin-compatible with vanilla 40-pin RC2014 — this is our own variant of the idea.

## Cards — how many?
Three tiers:

| Tier | Cards | What you get |
|---|---|---|
| **Minimum (boot + interact)** | 3 + backplane | CPU, Memory, Serial I/O → boots to monitor over a serial console |
| **Standalone** | 4 + backplane | + Video (TTL VGA) card, keyboard on the I/O card → own display + keyboard |
| **Full Juku-like** | 5 + backplane | + FDC card → EKDOS / disk BASIC |

### Card contents
- **CPU** — Z80 + clock oscillator + reset + **bus buffers** (74x245 data / 74x244 addr /
  buffered control). This card is the **sole bus driver**; all others are buffered loads.
- **Memory** — SRAM (main RAM) + ROM (EPROM/flash) + address decode. No DRAM → no refresh.
- **Video (TTL VGA)** — **on-card framebuffer** at `0xD800`+9640, local 25.175 MHz dot
  clock, sync + pixel-shift, resistor-ladder RGB, VGA connector. CPU writes over the bus;
  scanout never touches the bus. Owns `0xD800`+ in the memory map.
- **I/O** — UART (serial console; TTL to host/Arduino, or MAX232 for real RS232) + keyboard
  (PS/2 or matrix).
- **FDC** (optional) — WD1793/ВГ93 floppy controller.
- **Backplane** — passive: connectors + power + bus traces. ~4–6 slots fit in ≤100 mm.

## System rules (the bus contract must nail these)
- **One driver:** only the CPU card drives the backplane (buffered); everyone else listens.
- **Decode ownership:** each card decodes its own range; no overlaps. Video owns `0xD800`+,
  so the Memory card must **not** respond there.
- **Single +5V rail** — Z80, SRAM, TTL, resistor-DAC VGA all 5V. Simple supply.
- **Video contention:** CPU vs video framebuffer access → assert bus **WAIT** during active
  video (simplest), or blank-only access, or dual-port RAM.
- **Reset + INT/NMI** distributed on the bus; define who drives INT (keyboard? serial?).
- Per-card decoupling; slow Z80 clock forgives most backplane signal-integrity sins.

## Simulation
- Each card = an HDL module with the bus as its interface; backplane = top-level wiring.
- Add a **bus-functional model** so each card can be unit-simulated in isolation.
- Existing **framebuffer-readback oracle** still validates the assembled machine.
- Caveat: the digital twin does **not** catch backplane SI/timing — budget it (few-MHz clock
  = low risk) or bench-validate the physical backplane.

## Open questions
All resolved in `rev-b-build-plan.md` (separate CPU/Memory cards; GAL22V10 decode
reusing rev A equations; 6 slots @ ~19 mm; tiered interrupts — none until the
full-Juku tier, then 8259-class PIC with FRAME_TICK on USER1).
