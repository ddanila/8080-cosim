# VJUGA rev B — bus contract

The single authoritative interface every card and every HDL module is written
against. Signal-level detail only; card internals live elsewhere. Map, port, and
timing values are **derived from `ref/juku-machine-facts.json`** (root
`docs/spinoff-commons.md`) and enforced by `scripts/check_spinoff_commons.py` —
do not edit a value here without updating the facts file.

## 39-pin base connector

0.1" single row, ~96.5 mm span (fits the ≤100×100 card tier). Pins 1–39 are
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

Bussed across **all** slots (else `/WAIT` is useless). Its offset makes the intended
orientation conspicuous, but FreeCAD could not prove that it mechanically blocks a
reversed card; orientation is convention-only under D1.32b. All `_N` signals
are active-low.

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

**Physical placement (D1.4/D1.32b):** the 10-pin extension is a separate 0.1" row,
5 mm behind the base row and offset toward the pin-1 end. Inline on one edge is
impossible (39+10 pins ≈ 124 mm > 100 mm). A reversed card's centered base row can
still seat while its extension pins hover without a matching socket, so silk arrows
and operator discipline—not an unproved mechanical interlock—prevent reversal.

## Shared / open-drain lines and defaults

- **INT_N, WAIT_N, NMI_N, BUSRQ_N** are wired-OR: cards drive open-drain only,
  never push-pull; the **backplane owns the pull-ups** (S4).
- **MODE0/MODE1 (USER2/3)** are driven by the I/O card's 8255 PC0/PC1. The
  **backplane defaults them to boot mode (mode 0)** via pull resistors, so the
  minimum/standalone tiers (no I/O card populated) decode correctly instead of
  floating the Memory-card GAL inputs (S11).
- **RESET_N** has exactly one driver: the backplane supervisor+button (S7).
- **TX/RX**: the only UART is the I/O card's 8251. With both `JP_S5` shunts
  fitted, bus TX reaches the backplane's `J_TTL` pin 2 and `J_TTL` pin 3 reaches
  bus RX. Removing the shunts isolates the external console for diagnosis or
  loopback; it does not select a second serial card.
- **`J_TTL` pinout is board-relative:** pin 1 = `VCC_SENSE`, pin 2 = `BOARD_TX`
  (VJUGA output), pin 3 = `BOARD_RX` (VJUGA input), pin 4 = GND. The connector
  is TTL only, never RS-232. Pin 1 is a measurement/reference output through
  10 kΩ and a blocking diode, not a power input or an adapter supply. A 74HCT125
  and series/divider resistors form the protected 3.3/5 V USB-TTL boundary; see
  `rev-b-serial-console.md`.

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
| 0x08 | 8251-class USART (D11) | I/O | A0=0: TX/RX data |
| 0x09 | 8251-class USART (D11) | I/O | A0=1: mode/command, status (TxRDY/RxRDY/TxEMPTY) |
| 0x1C-0x1F | ВГ93/WD1793 FDC | FDC | port&3 = cmd/status, track, sector, data |

USART decoded window: **0x08-0x0B** (data 0x08, control/status 0x09). This is the
minimum-tier console; the bring-up ROM (B1) talks only through it.

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

## Mechanical mating contract (D1.31)

Machine-checked by `kicad/revb/check_revb_mating.py` against `kicad/revb/mating.json`
(the numeric source of truth); both cards and the backplane derive their connector
geometry from it. Distances in mm, footprint-centre.

| Constant | Value | Meaning |
|---|---:|---|
| `base_row_x` | 50.0 | card + backplane base (1×39) row centre X |
| `base_edge_offset` | 4.0 | card base row: mm from the card's mating edge |
| `ext_row_x` | 14.45 | ext (1×10) row centre X (see interleave note) |
| `ext_edge_offset` | 9.0 | card ext row: mm from the mating edge |
| `ext_row_dy` | 5.0 | backplane ext row = base row + this (per slot) |
| `slot_pitch` | 16.0 | backplane slot-to-slot spacing |
| `slot0_y` | 10.0 | backplane first (bottom) base row Y |
| `n_slots` | 5 | backplane slots (CPU/Memory/I/O/Video/FDC; no spare) |
| `backplane_board_h` | 100.0 | backplane outline height (cheap-tier decision D1.37) |
| `tail_strip_y0` | 82.0 | clear top-side service strip starts above the final ext row |

The base offset is **4.0 mm** (not mem's historical 5.0): io — the densest, most
routing-constrained card — routes reliably only at 4 mm, and it is the binding
constraint, so the contract adopts its value and the roomier cards follow.

**Connector gender / presentation (RC2014-compatible).** Cards carry **right-angle
male** headers on the bottom edge; the backplane carries **female sockets**
([RC2014 module template](https://rc2014.co.uk/1377/module-template/),
[RC2014 bus spec](https://smallcomputercentral.com/rc2014-bus/specification-rc2014-bus/)).
Mainline RC2014 presents the enhanced bus as an *adjacent second row* of the main
connector; **we instead use a separate 10-pin ext header**. This is a legitimate
RC2014-compatible variant (the spec fixes the signal set, not the physical presentation)
and it lets the base and ext bus **columns interleave** on the 2-layer backplane:
`ext_row_x = 14.45` places the ext pin grid a **half pin-pitch (1.27 mm)** off the base
grid, versus only 0.82 mm at the old 14.0 — the checker's `min_column_sep` gate enforces
this. Five 16 mm-pitch slots occupy base-row Y=10…74 and ext-row Y=15…79; the service
tail starts at Y=82 on the 100×100 board. D1.37 supersedes the earlier 100×120/six-slot
variant: the complete planned five-card system still fits, while top-side power/reset/
serial components stay outside the seated-card envelope.

The right-angle mating posts point out through the bottom card edge. The 39-pin base
header is front-side and the 10-pin extension header is back-side; this is required
because their pad rows are only 5 mm apart and two same-side Samtec bodies would
physically overlap. Backplane base sockets use the corresponding reversed rotation,
while extension sockets retain the opposite rotation, so pin 1 still meets pin 1 on
both rows. `mating.json` freezes side and rotation as well as XY coordinates.

## Five-card first-article power budget

R5.V2 replaces the old four-card/B1 estimate with a conservative actual-population
budget. Details and machine-checked arithmetic are in `rev-b-five-card-power.md` and
`video-power-audit.json`.

| Card | Conservative +5 V budget |
|---|---:|
| CPU | 250 mA |
| Memory | 235 mA |
| I/O (UART tier, B3 parts DNP) | 150 mA |
| Backplane | 30 mA |
| Video | 686 mA |
| **Five-card total** | **1351 mA** |

The required supply is regulated 5 V rated at least 2 A: 649 mA/32.45% planning
headroom remains. The MF-R110 USB-branch polyfuse holds only 1.1 A, below this
worst-case total, so USB-C is **not qualified for the complete five-card machine**.
Use the regulated 2 A-or-better bench input; R5.V6 must add/verify protection on that
normal input before release. The old ~712 mA number remains historical four-card
evidence only and must not be used for the VGA-populated system.
