# VJUGA rev B — modular card + backplane design

New parallel approach (rev A, the 200×200 4-layer board, is **not** scrapped). Goal:
several **≤100×100 mm** cards on a **passive 100×120 mm backplane**, so iterative cards
stay in the cheap 2-layer tier and you re-spin one small card instead of a big 4-layer
board. The one-off backplane is deliberately taller to preserve six mate-compatible
slots and a safe power tail.

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
- **Separate 10-pin extension** carrying `/WAIT`, `/NMI`, `/BUSRQ`, `/BUSAK`, `/RFSH`,
  `/HALT`, `IRQ_A`, `IRQ_B`, +5 V and GND. This gives us WAIT (needed for video contention) *without*
  going to the wide 80-pin enhanced backplane. **Supersedes the earlier "use an 80-pin
  enhanced backplane" note.**
- A future second-backplane/daisy-chain path remains possible but is **not fitted on B1**.
- **Backplane carries housekeeping**: USB-C power in, reset circuit, passive TTL-serial
  header/jumper, power LED —
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
- **CPU** — Z80 + socketed clock oscillator + diagnostic header. B1 is deliberately
  unbuffered (D1.21); reset authority lives on the backplane.
- **Memory** — SRAM (main RAM) + ROM (EPROM/flash) + address decode. No DRAM → no refresh.
- **Video (TTL VGA)** — **on-card framebuffer** at `0xD800`+9640, local 25.175 MHz dot
  clock, sync + pixel-shift, resistor-ladder RGB, VGA connector. CPU writes over the bus;
  scanout never touches the bus. Owns `0xD800`+ in the memory map.
- **I/O** — 8251 UART (TTL serial console) plus the fully wired, initially-DNP 8255/PIC
  and Juku matrix-keyboard header.
- **FDC** (optional) — WD1793/ВГ93 floppy controller.
- **Backplane** — passive: connectors + power + bus traces. Six slots at 16 mm pitch on
  a 100×120 mm board.

## System rules (the bus contract must nail these)
- **One driver per signal/cycle:** CPU owns address/control and write data; exactly one
  selected memory/I/O card may drive read data. Shared `/INT`, `/NMI`, `/WAIT`, `/BUSRQ`
  lines are open-drain with backplane pull-ups.
- **Decode ownership:** each card decodes its own range; no overlaps. Video owns `0xD800`+,
  so the Memory card must **not** respond there.
- **Single +5V rail** — Z80, SRAM, TTL, resistor-DAC VGA all 5V. Simple supply.
- **Video contention:** the B2 twin uses bounded cycle stealing—`WAIT` only when a CPU
  framebuffer access collides with an active scanout fetch; its phase sweep proves no
  lost/corrupted accesses.
- **Reset + INT/NMI** distributed on the bus; define who drives INT (keyboard? serial?).
- Per-card decoupling; slow Z80 clock forgives most backplane signal-integrity sins.

## Simulation
- Each card = an HDL module with the bus as its interface; backplane = top-level wiring.
- Add a **bus-functional model** so each card can be unit-simulated in isolation.
- Existing **framebuffer-readback oracle** still validates the assembled machine.
- Caveat: the digital twin does **not** catch backplane SI/timing — budget it (few-MHz clock
  = low risk) or bench-validate the physical backplane.

## Open questions
All resolved in `rev-b-build-plan.md` (separate CPU/Memory cards; GAL22V10 decode;
six slots @ 16 mm on the 100×120 backplane; tiered interrupts—polling in B1,
8259-class PIC populated at B3 with FRAME_TICK on USER1). The remaining choices are
the owner’s B1 order decision and post-B1-bench release of B2 physical layout work.
