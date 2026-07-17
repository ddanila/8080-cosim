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
- USER1 = **FRAME_TICK** (video card → I/O card PIC).
- USER2/3 = **MODE0/MODE1** — the 8255 PC0/PC1 memory-overlay mode bits, driven by
  the I/O card, consumed by the Memory card's GAL. **Backplane pull-up/downs default
  them to the boot mode** so tiers without the I/O card (B1/B2) decode correctly
  instead of floating the GAL inputs.

**10-pin extension** (salfter idea, own implementation; bussed across ALL slots):
/WAIT, /NMI, /BUSRQ, /BUSAK, /RFSH, /HALT, **IRQ_A, IRQ_B** (FDC INTRQ/DRQ → PIC
ir0/ir1), +5V, GND. CLK2 dropped — any card needing a special clock generates it
locally (video dot-clock, FDC crystal), same pattern everywhere.

Serial TxRDY/RxRDY → PIC ir3/ir2 never cross the bus: the 8251 and the PIC share
the I/O card (see card list) exactly as the real Juku clusters them.

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
4. **I/O** — one card, **populated in stages**: 8251-class UART (B1, minimum tier
   console) + 82C55 keyboard/mode bits + 8259-class PIC (added in B3). Mirrors the
   real Juku's serial/PPI/PIC cluster, and keeps the ir3/ir2 (serial→PIC) lines
   on-card instead of inventing bus pins for them. No throwaway serial-only card.
5. **Video** — rev A's TTL640x480 circuit re-hosted: on-card SRAM framebuffer at
   `0xD800`, local dot-clock, sync gen, /WAIT generation during active display,
   FRAME_TICK out on USER1.
6. **FDC** (last, optional) — ВГ93/WD1793 per the main repo's guarded FDC model;
   own crystal; INTRQ/DRQ to the PIC via extension IRQ_A/IRQ_B.

## Phases

**Phase B0 — bus contract + sim repartition (no money spent). ✅ DONE (2026-07-17).**
Delivered: `ref/juku-machine-facts.json` (facts source of truth) + `docs/spinoff-commons.md`
contract; `scripts/check_spinoff_commons.py` guard; `docs/rev-b-bus-contract.md`
(pins/map/ports/PIC/power, derived from facts); rev B card HDL in `hdl/revb/`
(CPU/Memory/Video/I-O + passive backplane) that boots ekta37 **byte-identical to
cosim in both decode modes** (`sim/revb_boot_check.sh`); bus-functional model +
per-card unit TBs (`sim/revb_card_tb_check.sh`, with a negative control); a
bus-conflict monitor + assertion test (`sim/revb_bus_assert_check.sh`); the
one-command `sim/revb_tier_suite.sh`; CI wiring (`hdl.yml` + `ci.yml`).
**Deviation:** the split rewrote the memory subsystem to the rev B architecture
(SRAM main + framebuffer on the Video card, no DRAM/U24) rather than mechanically
moving the DRAM twin — see execution-guide Deviations; oracle-gated, so faithful.

**Phase B1 — minimum tier boards (backplane, CPU, Memory, I/O-with-UART-only).**
`ekta37_z80.bin` cannot run this tier (no video to draw on, no keyboard — it would
hang), so B1 gets a **bring-up ROM**: a small serial monitor + RAM/bus self-test,
**written in the 8080-compatible subset so cosim remains its oracle** — the same
byte-identity discipline, different ROM. Sim gate: minimum-tier twin runs the
bring-up ROM against cosim before ordering. Schematics + 2-layer ≤100×100 layouts
(3D/STEP mating check; per-card LVS; ERC/DRC + silk checklist). Bench in rev A's
proven order, extended one step earlier: **backplane alone** (5 V, reset pulse,
clock present at every slot) → power-only cards → NOP free-run plug with analyzer
on the address bus (+ spot-check worst-case bus timing vs the B0 budget) → bring-up
ROM in. Exit: monitor prompt + RAM test PASS over the backplane FTDI header.

**Phase B2 — video card (standalone tier, first ekta37 boot).**
Re-host the TTL VGA design. Sim gates: /WAIT phase sweep; crop-vs-letterbox decided
against the oracle; **mode-bit defaults verified** (no I/O-card 8255 yet — MODE0/1
come from the backplane defaults, and the GAL must decode the boot overlay
correctly). Swap ROM to `ekta37_z80.bin`. Exit: real firmware banner on glass,
framebuffer readback byte-identical to cosim's `vram.bin`.

**Phase B3 — I/O card fully populated (interactive full firmware).**
Add 82C55 + PIC to the I/O card; FRAME_TICK via USER1; MODE0/1 now driven by PC0/PC1
(backplane defaults overridden). Sim gates: keyboard scan against the video-derived
tick (S2); **mode-switch overlay test** — firmware writes ports 0x06/0x07, Memory-card
GAL must follow; tier suite = keyboard-react + jmon33 guards on the assembled twin.
Exit: typing at the Juku monitor/BASIC on real hardware, jmon33 checkpoint parity.

**Phase B4 — FDC card (EKDOS, optional).**
Port the guarded ВГ93 quadrant; INTRQ/DRQ on extension IRQ_A/B; own crystal; 12 V
jack only if real drives (Gotek is 5 V). Tier suite = the root FDC/EKDOS/jbasic
prompt guards on the assembled twin. Exit: EKDOS `A>` on hardware **plus** the
write-sector readback test on an explicitly writable disk copy (the root repo's
write-path discipline, applied on the bench).

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
| S11 | How do the 8255 mode bits reach the Memory-card GAL? | **USER2/3 = MODE0/MODE1** bus lines, I/O card drives, **backplane defaults them to boot mode** via pull-up/downs. | Found by whole-plan audit: without this the GAL inputs float in B1/B2 (no I/O card populated) — a guaranteed bench failure. |
| S12 | How do peripheral interrupt requests reach the PIC? | Serial ir3/ir2: **on-card** (8251 shares the I/O card with the PIC, like the real Juku cluster). FDC ir0/ir1: **extension IRQ_A/IRQ_B**. CLK2 dropped from the extension to make room — special clocks are generated locally per card. | Found by whole-plan audit: a separate serial card would have needed two more bus pins that didn't exist. |
| S13 | What firmware runs the B1 tier? | A **bring-up ROM** (serial monitor + RAM/bus self-test) in the **8080-compatible subset, so cosim stays its oracle**. `ekta37_z80.bin` enters at B2 with the video card. | ekta37 needs video + keyboard; running it on the minimum tier would hang with nothing observable. |

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

## B1 design decisions (resolved at B1 planning, 2026-07-17)

| # | Question | Decision | Rationale / gate |
|---|---|---|---|
| D1.1 | UART port addresses? | **0x08 data (A0=0), 0x09 control/status (A0=1); decoded window 0x08–0x0B** — the real D11 USART window (`docs/serial-handoff.md`, `hdl/juku_top.v` '138 row). Add to the facts file + bus contract (T1.0). | Was missing from the I/O map; the bring-up ROM and I/O-card decode both need it. Twin reuses the root `usart_8251` model verbatim (`sync/serial_check.sh` already proves its TxRDY/RxRDY + 8N1 slice). |
| D1.2 | How does cosim oracle the serial output (it has no UART model)? | Bring-up ROM emits via `OUT 0x08`; cosim's `[IOSEQ]` trace captures the exact TX byte stream; the checker compares the twin's UART TX log against it. TxRDY poll: the 8251 **command word with TxEN sets bit0**, and cosim's output-latch readback returns it as status bit0 — so the poll naturally sees "ready" in cosim. Keep a generous bounded poll as bench belt-and-braces, and document the coincidence in the ROM source. | Zero root-cosim changes (executor Rule 4); the byte stream, not timing, is the oracle. |
| D1.3 | RAM-test range? | **0x4000–0xD7FF** (mode-0 RAM below the framebuffer window). Walking-1s per cell + an address-in-cell pass (catches aliasing). 0xD800+ is excluded: the Video card owns it and is absent in B1. | Testing unowned space would hang on floating bus. |
| D1.4 | Where does the 10-pin extension physically go? | **Second 0.1" row, 2.54 mm behind the base row, aligned to the pin-1 end.** Inline on the same edge is impossible (39+10 pins ≈ 124 mm > 100 mm); the end-aligned second row is the polarizing asymmetry S8 promised. Update the bus contract (T1.0). | Must be pinned before any board.json is written. |
| D1.5 | KiCad flow for four boards? | **Clone the rev A deterministic flow per card**: `<card>.board.json` spec → generator → check scripts → export/package (pattern: `kicad/minimal-vga.board.json`, `gen_rev_a_pcb.py`, `check_rev_a_*.py`, `export_fab.sh`, `package_rev_a_upload.py`). | CI-checkable without KiCad installed; same LVS fallback style as `sync/check.sh`. |
| D1.6 | B1 console path? | I/O-card 8251 ↔ bus TX/RX (pins 35/36) ↔ backplane FTDI header (passive) ↔ PC. The S5 jumper stays on the header but is a no-op until a *powered* serial source exists on the backplane. | Header is passive; no contention in B1. |
| D1.7 | I/O card B1 population? | **8251 + its decode + local UART clock only.** 8255, PIC, keyboard connector: footprints present, DNP. | One I/O card design across tiers (S12); B1 populates the minimum. |
| D1.8 | 8251 TxC/RxC source (real Juku uses the PIT, absent in B1)? | **Local baud oscillator on the I/O card** (S12 local-clock pattern); exact frequency/divider chosen at schematic time; PIT-as-baud-source arrives with B3+. | Design-level only; don't pick crystals in a plan. |
| D1.9 | Bench record? | `docs/rev-b-b1-bench-log.md` — expected-vs-observed table per bring-up step, created with the boards (T1.11), patterned on `docs/phase4-bench-bringup.md`. | The bench oracle needs a ledger like the sim ones. |

## Feedback loops & coverage matrix

Audit of every verification loop, what it catches, and whether it exists or is
new work. "Reuse" = the mechanism exists in the repo and rev B plugs into it.

| Loop | Catches | Gate | Status |
|---|---|---|---|
| cosim ↔ assembled twin (banner byte-identity) | logic errors in the machine model | B0, then every card change | **reuse** (`sim/boot_check.sh` pattern) |
| BFM unit sim per card | wrong card behavior at the bus boundary | before every PCB order | new (B0) |
| **Bus-conflict assertions in the BFM** | two cards driving D0–D7 at once; decode overlaps (e.g. Memory answering at `0xD800`) | every assembled sim run | **new — was missing.** Tri-state overlap is exactly the class of bug byte-identity can't see (X-propagation may still produce the right bytes in sim and smoke on the bench) |
| /WAIT phase sweep | CPU write landing at every phase offset of active display | B2, before video card order | new (was implied, now explicit) |
| **Tier-inherited probe suites** | deeper firmware regressions per tier | B1: monitor checkpoint; B3: keyboard-react + jmon33 guards; B4: EKDOS/jbasic prompt guards | **reuse** — the root `sync/*.sh` guards already exist; rev B's assembled twin must be able to run the tier's suite, not just the banner |
| **Per-card LVS** (KiCad netlist ↔ card HDL module) | schematic diverging from the sim that passed the oracle | before every PCB order | **reuse pattern, new scope** — rev A's LVS (`hdl/minimal_vga_lvs.*`) is monolithic; rev B needs it per card, so a card re-spin re-proves only itself |
| ERC/DRC + manufacturing-readiness script | electrical rule / footprint / fab errors | before order | **reuse** (`kicad/check_replica_manufacturing_ready.sh` precedent, rev B variant) |
| **Silk checklist** | assembly-time human errors | before order | new, cheap: pin-1 marks, card name+rev, orientation banding, bus pin labels at the connector, extension-key orientation arrow, "NO HOT-PLUG", NOP-plug and J95 headers labeled |
| Power budget check | card set exceeding the USB-C 5 V budget | B0 + whenever a card is added | **reuse** (`rev-a-power-budget.md` method, summed per backplane population) |
| GAL fuse-map verify + bench vectors | programmed GAL ≠ equations | after programming, via J95-style header | reuse (rev A dual-mode decode pattern) |
| ROM self-checksum | corrupted EPROM burn | free — firmware checks at `0x03E0` on every boot | reuse (already in cosim trace) |
| Framebuffer-readback bench oracle | real board ≠ twin | every bring-up phase | **reuse** (rev A phase 4 method) |
| Bench trace replay (analyzer capture → BFM replay → diff) | timing/behavior divergence the FB oracle averages away | B1+, on anomaly | new, optional — promote only if a bench mystery appears |
| Commons guard | spin-off constants diverging from root facts | CI, every push | new (per `docs/spinoff-commons.md`) |
| **CI wiring** | all of the above rotting | rev B sims path-gated into `hdl.yml`; commons guard into `ci.yml`; deep guards stay pre-push | new (B0 deliverable) |

The three that were genuinely missing before this audit: **bus-conflict
assertions**, **per-card LVS scope**, and the **silk checklist** — all are now
B0/pre-order gates. Everything else was already in the repo's DNA and rev B
inherits it.

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
