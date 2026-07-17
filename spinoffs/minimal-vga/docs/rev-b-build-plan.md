# VJUGA rev B — build plan

Companion to `rev-b-modular-design.md` (cards + bus concept). This resolves the open
questions and sequences the build. Principle throughout: **inherit everything rev A
already proved** (chip map, GAL equations, power budget, bring-up method, oracle,
`ekta37_z80.bin`) — rev B changes the *packaging*, not the machine.

## Resolved decisions

| Question | Decision | Rationale |
|---|---|---|
| Merge CPU+Memory? | **Separate cards** | Cheap re-spin of one card is the whole point; RC2014 precedent keeps them separate |
| Decode: РТ4/РЕ3 or GAL? | **GAL22V10 on the Memory card**, reusing rev A's equations (Mode A) | Reprogram vs re-spin; ATF22V10C still in production. Testing original PROMs stays **rev A's mission** — rev B base stays clean. A separate "PROM workbench card" can come later if wanted (modularity makes it additive) |
| Slot count / pitch | **6 slots @ ~19 mm (0.75")** on a ≤100 mm backplane | 96 mm / 5 gaps; room for DIP-40 cards + airflow; matches common RC2014 practice |
| Termination / buffering | **No bus termination** (RC2014 community norm at 4 MHz, short bus, ≤~8 modules); **CPU card buffers** its outputs (74HCT245/244) as margin | Mainline RC2014 runs unbuffered at 7.37 MHz; buffers cost ~2 chips and remove the loading unknown |
| Interrupts | **Tiered.** Minimum/standalone tiers: **none — poll** (proven: rev A banner boots with no interrupts). Full-Juku tier: **8259-class PIC on the I/O card**, wired as the real Juku (`hdl/juku_top.v`): ir5=frame tick, ir3/ir2=serial TxRDY/RxRDY, ir1/ir0=FDC DRQ/INTRQ; frame IRQ services the keyboard scan (ROM vector `0xFED4`) | Don't pay interrupt complexity before the tier that needs it |
| Frame tick distribution | **USER1 bus pin = FRAME_TICK**, driven by the video card, consumed by the I/O card's PIC | Real Juku's `frame_tick` (calibrated period 200,000 cycles in the twin) must reach the PIC; USER pins exist for exactly this |

## Bus contract (the one authoritative table)

**Pins 1–39 are signal-identical to the RC2014 Standard bus** (1–16 A15–A0, 17 GND,
18 +5V, 19 /M1, 20 /RESET, 21 CLK, 22 /INT, 23 /MREQ, 24 /WR, 25 /RD, 26 /IORQ,
27–34 D0–D7, 35 TX, 36 RX, 37–39 USER1–3; USER4/pin-40 dropped to fit <100 mm).
USER1 = FRAME_TICK (video → PIC), USER2/3 reserved.

**10-pin extension** (salfter idea, own implementation; bussed across ALL slots):
/WAIT, /NMI, /BUSRQ, /BUSAK, /RFSH, /HALT, CLK2, reserved, +5V, GND.

Memory map = the Juku map rev A validated (`rev-a-gal-equations.md`): ROM low /
RAM overlay per mode bits, framebuffer `0xD800`+9640 **owned by the video card**
(Memory card must not respond there). I/O map: 8255 keyboard/mode at the Juku
ports (mode bits PC0/PC1), PIC, UART, FDC — same ports the firmware pokes.

## Cards (final list)

1. **Backplane** — passive, ≤100×100, 2-layer, 6 slots; + USB-C 5V in, reset
   button/supervisor, power LED, FTDI-style 6-pin TTL serial header on the bus
   TX/RX pins (bring-up console without any I/O card).
2. **CPU** — Z80 (Z0840004PSC, 4 MHz), oscillator, buffers. Sole bus driver.
3. **Memory** — 27C256 ROM (`ekta37_z80.bin`) + 32K/128K SRAM + GAL22V10 decode
   (rev A Mode-A equations, minus DRAM terms — SRAM kills U20–U24 entirely).
4. **Serial I/O** — UART for the console. Minimum tier ends here.
5. **Video** — rev A's TTL640x480 circuit re-hosted: on-card SRAM framebuffer at
   `0xD800`, local dot-clock, sync gen, /WAIT generation during active display,
   FRAME_TICK out on USER1.
6. **Keyboard/PIC I/O** — 82C55 (matrix + PC0/PC1 mode bits via the rev A Port-C
   split) + 8259-class PIC (full tier).
7. **FDC** (last, optional) — ВГ93/WD1793 per the main repo's guarded FDC model.

## Phases

**Phase B0 — bus contract + sim repartition (no money spent).**
Write the pin/memory/IO map doc (above, expanded). Split `vjuga_juku_top.v` into
per-card HDL modules whose ports are exactly the bus contract; backplane = top-level
wiring. Add a bus-functional model; unit-sim each card; assembled sim must boot the
banner **byte-identical to cosim** (existing framebuffer oracle). Exit: same oracle
result as rev A's twin, now across module boundaries.

**Phase B1 — minimum tier boards (backplane, CPU, Memory, Serial).**
Schematics + 2-layer ≤100×100 layouts in KiCad (3D/STEP check of card-connector
mating before ordering). Order at the $2 tier. Bring-up in rev A's proven order:
power-only → NOP free-run plug (resistor plug, fetches read 0x00) with analyzer on
the address bus → ROM in, monitor over the backplane FTDI header. Exit: serial
monitor prompt on a modern PC.

**Phase B2 — video card (standalone tier).**
Re-host the TTL VGA design; verify /WAIT timing in sim first (BFM drives CPU writes
during active display), then bench: boot banner on a VGA monitor, compare
framebuffer readback vs cosim. Exit: banner pixels on glass, oracle-identical.

**Phase B3 — keyboard + PIC (interactive full firmware).**
8255 + PIC card; FRAME_TICK from video via USER1; firmware keyboard scan runs in
the frame IRQ exactly as the twin calibrates it (200,000-cycle period). Exit:
typing at the Juku monitor/BASIC on real hardware.

**Phase B4 — FDC card (EKDOS, optional).**
Port the guarded ВГ93 quadrant; exit = EKDOS `A>` from a real or Gotek drive.

Each phase = 1–2 cards = 1–2 cheap PCB orders; any failure re-spins one small
2-layer board. Sim gate before every order: the card's HDL module passes its BFM
unit sim AND the assembled sim still boots the banner.

## Design questions register (identified + resolved, design level only)

### System / bus
| # | Question | Decision | Rationale / gate |
|---|---|---|---|
| S1 | Who drives CLK, and at what frequency? | CPU card, **socketed can oscillator**. Start near the Juku's **~2 MHz** (FDC timers and firmware delay loops assume a 2 MHz-equivalent world; `cosim/juku_fdc.c`); the 4 MHz Z80 part gives headroom. | Z80 cycle counts ≠ 8080 cycle counts is an *already accepted* deviation — cosim/twin equivalence is the arbiter of any speed change. Socket = change without re-spin. |
| S2 | FRAME_TICK rate vs the twin's calibrated 200,000-cycle period? | Generated by the **video card's frame boundary** (like the real machine's video chain), bussed on USER1. Exact cadence must reproduce the twin's calibrated keyboard-scan behavior. | **Sim gate in B3**: BFM replays firmware keyboard scan against the video-derived tick before the I/O card is ordered. |
| S3 | Interrupt vectoring mechanism? | **Z80 IM0 + 8259-class PIC in 8080 mode** (PIC injects CALL), exactly as the real Juku / `juku_top.v`. | Firmware vectors (`0xFED4` frame service) work unmodified; already proven in the twin. |
| S4 | Shared/wired-OR lines (/INT, /NMI, /WAIT, /BUSRQ) — who pulls up? | **Backplane owns the pull-ups**; cards drive these open-drain only, never push-pull. | Multiple potential drivers (video /WAIT, PIC /INT, future DMA) must never fight. |
| S5 | TX/RX contention: backplane FTDI header vs Serial card? | **Jumper on the backplane header** disconnects it when the Serial card is present. | Two drivers on one RX line otherwise. |
| S6 | Power architecture? | **USB-C 5 V** in on backplane, single rail, per-card decoupling + bulk cap; budget carried over from `rev-a-power-budget.md`. FDC-tier 12 V (real drives) enters on the **FDC card's own jack**; Gotek needs only 5 V. | Keeps backplane passive apart from power/reset; no card regulates. |
| S7 | Reset topology? | Backplane **supervisor + button** is the *only* /RESET driver. | One reset authority; cards are consumers. |
| S8 | Mechanical keying — how do we prevent offset/reversed insertion? | The **10-pin extension connector doubles as the polarizing key**: its offset placement makes misaligned or flipped cards physically unpluggable. Silkscreen banding for pin 1. **No hot-plug**, stated on every card. | The classic RC2014 failure mode is off-by-one insertion; the extension gives us keying for free. |
| S9 | Observability? | Every card carries a **J95-style analyzer header** (rev A pattern) exposing its key internals; Memory card keeps the **NOP-plug provision** (J91 equivalent) for free-run bring-up. | Rev A's bring-up method depends on these; cheaper than debugging blind. |
| S10 | Expansion beyond 6 slots? | **Daisy-chain connector** at the backplane end (salfter idea). | Second backplane instead of a bigger board keeps the ≤100×100 tier. |

### Per-card
| # | Question | Decision | Rationale / gate |
|---|---|---|---|
| C1 | SRAM part / size? | One **128K×8 5 V SRAM** (AS6C1008-class), GAL maps what the Juku map needs; spare capacity unused. | One chip replaces the whole U10–U24 DRAM+arbitration chapter; 128K ≈ price of 32K. |
| C2 | ROM? | Socketed **27C256** carrying `ekta37_z80.bin`; ROM/RAM overlay switching stays GAL terms driven by the 8255 PC0/PC1 mode bits. | Same as rev A; the mode-bit path is already reconciled in `rev-a-chip-map.md`. |
| C3 | I/O port decode ownership? | Each card decodes its own ports; the map is **pinned from cosim**: PIC `0x00/0x01`, 8255 `0x04–0x07` (A=kbd column, B=kbd read, C=mode bits + control at 0x07); UART/FDC ports enumerated in the B0 contract doc from the same source. | cosim is the single source of truth for what the firmware actually pokes. |
| C4 | Video pixel mapping to VGA 640×480? | **Double both axes**; 241 rows × 2 = 482 lines → 2-line overscan handled by crop-or-letterbox, **decided in B2 sim** where the oracle can see it. | Keeps the dot-clock chain trivial; defers the only cosmetic choice to where it's testable. |
| C5 | Video output electrical? | Mono **resistor-DAC on the RGB pins**, white-on-black default. | TTL-only, no video DAC chip, matches rev A's TTL640x480 approach. |
| C6 | UART choice? | **8251-class (КР580ВВ51-compatible)** at the Juku's serial ports — not a 68B50/16C550. | The full-Juku tier firmware pokes an 8251; using it from day one means the minimum-tier monitor and the full firmware share one serial card, and the twin already models it. |
| C7 | Keyboard interface? | **82C55 matrix scan** per the rev A Port-C split (lower nibble = column out via Port A low, read via Port B, mode bits on PC0/PC1). | Identical to the reconciled rev A design; no translation layer. |

Anything not listed here (component values, footprints, trace widths) is deliberately
out of scope — implementation detail belongs to the per-phase schematic work, gated
by the B0 contract and the sim oracles.

## Best-practice notes (researched 2026-07-17)
- RC2014 bus spec: Standard 40-pin row + Enhanced partial second row
  (smallcomputercentral.com "RC2014 Bus Specification"); mainline runs
  **unterminated and unbuffered** at 7.37 MHz — by design, fine for short
  backplanes; practical limits appear around ~12 slots. At 4 MHz / 6 slots we
  have margin, and the buffered CPU card adds more.
- Enhanced-bus second row already standardizes /WAIT //NMI //BUSRQ //BUSAK //RFSH
  //HALT — our 10-pin extension carries the same signal set, so a future move to
  the official Enhanced pinout is a connector change, not a redesign.
- Salfter's rc2014-compat (100×100 respin) is the pattern source for the 39+10
  split, USB-C backplane power, and daisy-chain expansion — **ideas only, boards
  are our own** (his repo has no license).
