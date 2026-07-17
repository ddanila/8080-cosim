# VJUGA rev B — bus contract

The single authoritative interface every card and every HDL module is written
against. Signal-level detail only; card internals live elsewhere. Map, port, and
timing values are **derived from `ref/juku-machine-facts.json`** (root
`docs/spinoff-commons.md`) and enforced by `scripts/check_spinoff_commons.py` —
do not edit a value here without updating the facts file.

## 39-pin base connector

0.1" single row, ~96.5 mm span (fits the ≤100×100 tier). Pins 1–39 are
signal-identical to the RC2014 Standard bus except pin 40 (USER4) is dropped and
USER1–3 are assigned below. All `_N` signals active-low.

| Pin | Signal | Dir (from CPU card) | Pin | Signal | Dir |
|---|---|---|---|---|---|
| 1 | A15 | out | 21 | CLK | out |
| 2 | A14 | out | 22 | INT_N | in (open-drain, PIC) |
| 3 | A13 | out | 23 | MREQ_N | out |
| 4 | A12 | out | 24 | WR_N | out |
| 5 | A11 | out | 25 | RD_N | out |
| 6 | A10 | out | 26 | IORQ_N | out |
| 7 | A9 | out | 27 | D0 | bidir |
| 8 | A8 | out | 28 | D1 | bidir |
| 9 | A7 | out | 29 | D2 | bidir |
| 10 | A6 | out | 30 | D3 | bidir |
| 11 | A5 | out | 31 | D4 | bidir |
| 12 | A4 | out | 32 | D5 | bidir |
| 13 | A3 | out | 33 | D6 | bidir |
| 14 | A2 | out | 34 | D7 | bidir |
| 15 | A1 | out | 35 | TX | (serial, see S5) |
| 16 | A0 | out | 36 | RX | (serial, see S5) |
| 17 | GND | — | 37 | USER1 = FRAME_TICK | video → I/O PIC |
| 18 | +5V | — | 38 | USER2 = MODE0 | I/O → Memory GAL |
| 19 | M1_N | out | 39 | USER3 = MODE1 | I/O → Memory GAL |
| 20 | RESET_N | in (backplane) | 40 | (absent) | — |

## 10-pin extension connector

Bussed across **all** slots (else /WAIT is useless); also the mechanical
polarizing key (S8). All `_N` active-low.

| Pin | Signal | Notes |
|---|---|---|
| E1 | WAIT_N | video asserts during active display; open-drain |
| E2 | NMI_N | reserved; open-drain |
| E3 | BUSRQ_N | future DMA; open-drain |
| E4 | BUSAK_N | CPU card drives |
| E5 | RFSH_N | CPU card drives (unused by SRAM, carried for completeness) |
| E6 | HALT_N | CPU card drives |
| E7 | IRQ_A = FDC INTRQ | FDC → PIC ir0 |
| E8 | IRQ_B = FDC DRQ | FDC → PIC ir1 |
| E9 | +5V | second power feed |
| E10 | GND | |

CLK2 is intentionally **not** on the extension — any card needing a special clock
generates it locally (video dot-clock, FDC crystal).

## Shared / open-drain lines and defaults

- **INT_N, WAIT_N, NMI_N, BUSRQ_N** are wired-OR: cards drive open-drain only,
  never push-pull; the **backplane owns the pull-ups** (S4).
- **MODE0/MODE1 (USER2/3)** are driven by the I/O card's 8255 PC0/PC1. The
  **backplane defaults them to boot mode (mode 0)** via pull resistors, so the
  minimum/standalone tiers (no I/O card populated) decode correctly instead of
  floating the Memory-card GAL inputs (S11).
- **RESET_N** has exactly one driver: the backplane supervisor+button (S7).
- **TX/RX**: the backplane's bring-up FTDI header is jumper-disconnected when the
  I/O card's UART is present (S5).

## Memory map

ROM/RAM overlay selected by 8255 Port C bits[1:0] via MODE0/1. "ROM" = served by
the ROM overlay; everything else is RAM. The **framebuffer at 0xD800 (9640 bytes,
40×241 mono bitmap) is owned by the Video card** — the Memory card must not
respond in that window.

| Mode (MODE1:MODE0) | ROM regions | Notes |
|---|---|---|
| 0 | 0x0000–0x3FFF | boot/default; ekta37 stays here |
| 1 | 0xD800–0xFFFF | |
| 2 | 0x4000–0xBFFF, 0xD800–0xFFFF | 0x4000–0xBFFF = cartridge (0xFF empty) |
| 3 | (none) | all RAM |

Framebuffer window: base **0xD800**, **9640** bytes, geometry **40×241**.

## I/O port map

Low 8 address bits. Each card decodes only its own ports.

| Port(s) | Device | Card | Role |
|---|---|---|---|
| 0x00 | 8259-class PIC | I/O | A0=0: ICW1 / OCW2 / OCW3 |
| 0x01 | 8259-class PIC | I/O | A0=1: ICW2 / OCW1 (mask) |
| 0x04 | 8255 Port A | I/O | keyboard column select (low nibble) |
| 0x05 | 8255 Port B | I/O | keyboard read (74148) |
| 0x06 | 8255 Port C | I/O | memory-overlay mode bits[1:0] → MODE0/1 |
| 0x07 | 8255 control | I/O | mode-set / Port C bit set-reset |
| 0x1C-0x1F | ВГ93/WD1793 FDC | FDC | port&3 = cmd/status, track, sector, data |

## PIC interrupt assignments

Lower number = higher priority. Frame-service ROM vector 0xFED4.

| Line | Source | Reaches PIC via |
|---|---|---|
| ir0 | FDC INTRQ | extension E7 (IRQ_A) |
| ir1 | FDC DRQ | extension E8 (IRQ_B) |
| ir2 | serial RxRDY | on-card (I/O) |
| ir3 | serial TxRDY | on-card (I/O) |
| ir5 | frame tick | base pin 37 (USER1/FRAME_TICK) |
| ir6, ir7 | reserved | — |

## Timing anchors

- Frame IRQ / keyboard-scan period: **200000** CPU cycles.
- FDC controller clock: 2 MHz nominal (FDC card carries its own crystal).

(Both from the facts file; CPU operating frequency is a build-plan decision, S1.)

## B1-population power budget (planning estimate)

Conservative +5 V budget for the **minimum tier** (backplane + CPU + Memory +
I/O-with-UART-only), for the USB-C headroom check. Method and per-part figures
follow `rev-a-power-budget.md`; the big change vs rev A is **SRAM replaces the
eight 4164 DRAMs** (build-plan C1), removing ~600 mA, and B1 carries **no video
card and no bipolar PROMs** (GAL decode, C2).

| Block | Qty | Budget each | Total | Card |
|---|---:|---:|---:|---|
| Z80 CPU (NMOS Z0840004-class) | 1 | 200 mA | 200 mA | CPU |
| Bus buffers (74HCT245/244) | 2 | 10 mA | 20 mA | CPU |
| Oscillator | 1 | 25 mA | 25 mA | CPU |
| 27C256 ROM | 1 | 50 mA | 50 mA | Memory |
| 128K×8 SRAM (AS6C1008 CMOS) | 1 | 40 mA | 40 mA | Memory |
| GAL22V10 decode | 1 | 90 mA | 90 mA | Memory |
| 8251-class UART (82C51 CMOS) | 1 | 30 mA | 30 mA | I/O |
| TTL/CMOS glue (decode gates, latches) | 5 | 10 mA | 50 mA | all |
| Reset supervisor + pull-ups | 1 | 5 mA | 5 mA | Backplane |
| Power LED | 1 | 2 mA | 2 mA | Backplane |
| Margin / sourcing variation | — | — | 200 mA | — |
| **Total (B1 minimum tier)** | | | **~712 mA** | |

**USB-C budget & headroom rule.** A non-PD USB-C source advertising 1.5 A (22 kΩ
Rp) gives a 5 V budget of **1.5 A**. B1 draw ~712 mA = **~47 %** of that — under
the 60 % headroom ceiling (0.9 A), with room for the video + I/O-full + FDC cards
added in later tiers (each re-checked here as populated). As in rev A, without PD
negotiation do not assume a given host delivers the full 1.5 A; the bench-supply
path stays the safe primary bring-up input.
