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

**Phase B1 — minimum tier boards (backplane, CPU, Memory, I/O-with-UART-only). SIM/SPEC PORTION DONE (2026-07-17).**
Bring-up ROM + minimum-tier twin boot byte-identical to cosim with the real 8251;
card connectivity specs + checker pass. KiCad layout/DRC/STEP (needs KiCad/FreeCAD)
and the bench bring-up (needs boards) are the remaining, tool/hardware-blocked
continuation — see `rev-b-execution-guide.md` B1 execution status.
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

## B1-CAD design decisions (the T1.7–T1.9 continuation, planned 2026-07-17)

| # | Question | Decision | Rationale / gate |
|---|---|---|---|
| D1.10 | Which environment runs the KiCad/FreeCAD work? | **Both, via the repo's locator scripts** (`scripts/find-kicad-cli.sh`, `find-kicad-python.sh`): KiCad 10.0.4 exists on this Mac (Homebrew cask app bundle — off PATH) and on the Linux box. **Mac needs `KICAD_FOOTPRINTS`** pointing at the app bundle (the `gen_rev_a_pcb.py` documented override). Committed *generated* artifacts (.kicad_pcb, STEP, renders) are canonical from **one recorded environment per artifact** — note which in the commit; re-gen elsewhere must be diff-clean or the difference explained. FreeCAD: absent locally — `brew install --cask freecad`, or the Linux box. All new check scripts **skip-not-fail** when tools are missing (rev A/CI pattern), so CI stays green. | The earlier "kicad-cli absent" blocker note was wrong — it was only off PATH. Toolchain-split memory: Mac and Linux box differ; determinism needs the env pinned per artifact. |
| D1.11 | LVS strategy for behavioral card models? | **Per-card structural LVS models** (`hdl/revb/revb_<card>_lvs.v`): connector + real chips as instances (Z80 socket, '245/'244, 27C256, AS6C1008, GAL22V10, 8251 — reusing `hdl/devices.v` chip models where they exist). Behavioral validation: the **assembled structural twin must boot byte-identical to cosim** (root `juku_top` precedent: the LVS-checked structural model is also the booting model). Then netlist-vs-board LVS per card via `sync/lvs.py`. | LVS compares connectivity, not behavior — the boot oracle closes the behavior side, same as the main repo does. |
| D1.12 | board.json shape per card? | Full `<card>.board.json` (chips + nets; the 39+10 bus connector is a component whose pin N carries the `bus-pinout.json` signal). `scripts/check_revb_boards.py` grows a **cross-check: board.json connector nets ↔ cards.json roles ↔ bus-pinout.json**. | The connectivity contract already exists; board.json must provably restate it, not fork it. |
| D1.13 | PCB generation? | Clone the deterministic `gen_rev_a_pcb.py` flow per board, parameterized to **100×100** (backplane) and card outlines; 1×39 + offset 1×10 0.1" header footprints per D1.4; **silk emitted by the generator** (name+rev, pin-1, bus labels, key arrow, NO HOT-PLUG, NOP/J95 labels) so the silk checklist is machine-generated and machine-checked. | Hand-drawn layout would be the first non-reproducible artifact in the project; don't start now. |
| D1.14 | DRC/fab gate? | `kicad-cli pcb drc` + rev A fab/assembly checks; 2-layer, cheap-tier constraints (min track/clearance per JLC 2-layer). One `check_revb_ready.sh` covering all four boards. | Same bar rev A had to pass. |
| D1.15 | STEP/mating check — automated or eyeballed? | **Automated first**: `kicad-cli pcb export step` per board; a `freecadcmd` headless script assembles cards into backplane sockets at 19 mm pitch and runs a boolean **interference check**, plus a deliberately **reversed card placement that must collide** (keying proof). Fallback if headless FreeCAD fights back: manual GUI assembly with committed screenshots + measured clearances. | "Assembled render looks fine" is not a gate; a collision boolean is. |

## B1-CAD revamp decisions (after the TC.3 findings, 2026-07-17)

| # | Question | Decision | Rationale / gate |
|---|---|---|---|
| D1.16 | I/O-card chip-select decode (UART_CS_N was dangling in TC.2)? | **One ATF16V8-class GAL on the I/O card** generates UART_CS_N (window 0x08–0x0B), PPI_CS_N (0x04–0x07), PIC_CS_N (0x00–0x01) from IORQ_N + A2–A7, plus the **8251 RESET inversion** (the 8251 reset pin is active-HIGH; the bus RESET_N is active-low — a caught-on-paper polarity bug). 8255/PIC selects are wired but DNP-consumers until B3. | One programmable chip covers all I/O selects + the inverter; consistent with the GAL-decode pattern (C2). |
| D1.17 | CPU-card buffer control ('245/'244 in-path)? | Z80 pins → **local nets (D0L…, A0L…)** → buffers → bus nets. Control terms: **'244 always enabled** (address/control are CPU-sourced, S-rules), **'245 DIR = RD_N** (read: bus→CPU; write: CPU→bus), **'245 /OE = RD_N & WR_N** (enabled on an actual read or write). **CORRECTED (TD.0):** the first draft said `/OE = MREQ_N & IORQ_N`, which drives the bus during Z80 **refresh** (MREQ active, RD/WR idle) — a real bug the boot oracle can't see (refresh has no data consumer/competitor). Now caught by the monitor's **refresh-drive assertion**. | The exact terms that must not be guessed on copper — and the reason D1.19 needed the refresh assertion to have teeth. |
| D1.18 | Netlist completeness rule (what "schematic depth" means, checkable)? | On a populated card, **every internal (non-bus) net must have ≥2 endpoints** or be explicitly tagged `_TIE` / `_NC` / listed DNP. Bus nets may have 1 endpoint per card (they continue through the backplane). The board checker enforces this per card. | Turns "did we finish the schematic?" into a machine check; would have caught UART_CS_N and the beside-the-path buffers. |
| D1.19 | How do control equations get validated before silicon? | **Behavioral-twin-first rule:** any equation destined for a GAL or buffer control (D1.16 selects, D1.17 DIR/OE, mem-card decode) is first encoded in the behavioral card models and must pass the **boot + bring-up oracles**; the netlist/GAL-doc versions are then derived from those oracle-tested terms (single source). | Extends the byte-identity discipline to the last mile of logic; costs minutes, catches inverted-enable class bugs. |
| D1.21 | Buffer the CPU card in B1? | **No — unbuffered in B1** (Z80 directly on the bus, mainline-RC2014 style, which runs unbuffered at 7.37 MHz; we target ~2–4 MHz on ≤6 slots). '245/'244 in-path buffering needs its own /OE control logic (a gate/GAL) — real cost for margin we don't need yet. The '245/'244 remain a documented **optional later-rev margin footprint**, not populated. Matches the behavioral model, which drives the bus directly (the `buf245_*` wires in `revb_cpu_card.v` document intent; the Z80's own drivers do the work). | Surfaced by TD.4: in-path buffers need control silicon; RC2014 precedent says unbuffered is fine at this scale. Revises the earlier "CPU card buffers as margin" (Resolved-decisions table / D1.17). |
| D1.20 | All four boards in parallel, or one first? | **Pipeline-prove on the mem card first** (simplest full-pipeline card: 3 ICs, no in-path buffers), through netlist→LVS→PCB→DRC→STEP. Only then replicate to io, cpu (hardest, buffers), backplane (no LVS — passive). | The first card absorbs all pipeline iteration (footprints, DRC rules, generator bugs); the rest become replication instead of four parallel debug sessions. |

## Stage B design decisions (mem-card pipeline, planned 2026-07-17)

| # | Question | Decision | Rationale / gate |
|---|---|---|---|
| D1.22 | LVS scope + pinmap source? | LVS maps the **U-refs only** (mem: U1 ROM, U2 SRAM, U3 GAL); connectors, caps, headers stay unmapped (`sync/lvs.py` compares only mapped-instance endpoints). The `map.json` pinmaps are **generated from `gen_revb_boards.py`'s CHIP_TYPES** by a small emitter — never a second hand transcription. | A hand-copied pinmap is a second source of truth waiting to drift; the generator already owns the pin tables. |
| D1.23 | mem-card geometry? | **100×60 mm** outline. Base **1×39 row on the bottom edge, pin 1 left** (96.5 mm span, ~1.7 mm margins); **1×10 extension row 2.54 mm above it, pin-1-end aligned** (D1.4 keying). DIPs pin-1 upper-left per `rev-a-placement-rules.md`. **THT 1×39 availability must be probed** (grep found only SMD; 1×40 THT does not fit — 99.06 mm span); fallback = programmatic pad row in the generator. | Fixes the coordinates every TD.7 artifact and the TD.8.2 sanity check measure against. |
| D1.24 | Routing method? | **freerouting via the rev A DSN/SES round-trip** (`route_rev_a_pcb.sh` pattern; Java 25 probe order: repo-local `.tools/jre25`, Gradle Temurin, `JAVA_BIN`). Zones/planes after routing, then DRC. | Proven flow in this repo; hand-routing a generated board defeats regeneration. |
| D1.25 | What does "deterministic PCB" mean here? | **Content-checked, not byte-diffed**: pcbnew emits UUIDs, so byte-stable regen is not guaranteed (rev A never promised it either — its guarantee is `check_rev_a_pcb.py`). Rev B gets `check_revb_mem_pcb.py`: outline dims, connector pin coordinates, every board.json ref placed, silk items present. Big binary artifacts (STEP, DSN/SES) live under untracked `fab/` with SHA256s recorded in docs, per the root-repo convention. | Corrects TD.7's earlier "byte-stable regen" acceptance, which pcbnew cannot honor. |

## Stage B-finish / C / D design decisions (planned 2026-07-17)

| # | Question | Decision | Rationale / gate |
|---|---|---|---|
| D1.26 | Does the B1 io card carry the B3 parts' wiring? | **Yes — full B3 wiring now, parts DNP.** The 8255 (DIP-40), 8259-class PIC (DIP-28), and keyboard header are **footprinted AND fully wired** on the io card (8255→bus/kbd header/MODE lines; PIC→D-bus, INT_N, IRQ_A/B, FRAME_TICK, selects from the ATF16V8) so **B3 = populate-only, no respin**. Wiring source: `hdl/juku_top.v` PIC/PPI wiring + the facts file; D1.18 completeness applies to the DNP nets too (they must terminate at real pads). | The whole point of "one io card populated in stages" (S12); discovering this at B3 would mean a respin — the exact cost rev B exists to avoid. |
| D1.27 | What does "DRC-clean" gate, and when? | **Two-stage gate.** Pre-routing: **zero placement-class violations** (courtyards, hole-to-hole, edge clearances, silk-over-copper/edge, mask bridges, shorting items) — unconnected items excluded (that's routing's job). Post-routing: **zero everything, unconnected = 0**. Human eyeball via committed **preview renders** (`kicad-cli pcb render` / SVG, rev A `render_*_preview.sh` pattern) — headless DRC coordinates plus a picture beat blind numbers. | The first DRC dump mixed both classes; gating them separately makes placement iteration convergent without Java 25 present. |

## Stage C-finish design decisions (from Stage B/C findings, 2026-07-18)

| # | Question | Decision | Rationale / gate |
|---|---|---|---|
| D1.28 | How to close a *deterministic* single-net routing failure (cpu A8: 12/12 attempts)? | **Automated placement sweep first**: grid-search U1 (Z80) x-position (e.g. 25–45 mm in 2 mm steps) × rotation {90, 270} headlessly — regenerate, placement-DRC gate, 2 route attempts each, stop at the first DRC-0/0 full route. Only if the whole sweep fails: **one hand-authored track** emitted by the generator (documented, deterministic — not a GUI edit that regeneration would erase). | Stochastic retries are the wrong tool for a deterministic constraint; a sweep is desk-executable and stays within the everything-is-generated discipline. mem's U1-180° fix was exactly one sweep point found manually. **Resolved 2026-07-18: sweep found U1 x=41 mm, rot=90 (was x=35); cpu routes 0/0 from a clean regenerate. No hand-authored track needed.** |
| D1.29 | How to route the backplane (49 bus signals × 6 slots)? | **Exploit the regularity: don't auto-route the bus.** Stack the six 39+10 slots at the SAME x-origin, 19 mm pitch → every bus pin aligns in a vertical column → the generator emits **programmatic straight vertical tracks** per column (F.Cu), deterministic and DRC-predictable. freerouting handles only the irregular tail (USB-C/supervisor/pulls/FTDI/LED). Prerequisite gen change: split each `J_S{n}` connector into per-slot `J_S{n}_BUS`/`J_S{n}_EXT` refs (the current code hardcodes one `J_BUS`/`J_EXT` pair). | A parallel backplane is a regular structure; a stochastic router adds risk to the one board where routing is trivial by construction. **Resolved 2026-07-18: `emit_bus_columns()` emits 245 locked column segments; freerouting fills only the tail → 0/0 on attempt 1.** |
| D1.30 | Where to place base vs ext connectors on the backplane? | The 39-pin base spans ~96.5 mm (nearly full width), so co-locating each slot's base+ext pair would drop the 10-pin ext body **onto the base's bus columns**. Instead run **two independent bussed banks**: six base connectors column-aligned in the upper region, six ext connectors column-aligned lower-left; power/reset/serial tail in the free lower-right quadrant. Bus-signal pullups sit in the **interior band between banks** so each taps its column with a short stub (a long cross-board pullup trace otherwise dragged a via into a corner → copper-edge fail). | Keeps both banks cleanly column-routable and the tail short; per-card base/ext edge mating is a Stage-D (TD.12 FreeCAD) concern, not a routing one. |

## Stage D design decisions (from Stage C exit review, 2026-07-18)

| # | Question | Decision | Rationale / gate |
|---|---|---|---|
| D1.31 | How do cards physically mate with the backplane — and what enforces it? | **A machine-checked mechanical mating contract**, like the bus contract but for geometry. The Stage-C exit review found: (a) the cards are mutually INCONSISTENT (mem's base/ext rows sit 5/10 mm from the card bottom edge; io and cpu sit at 4/9 mm); (b) the D1.30 two-bank backplane cannot mate any card at all — a card presents base+ext rows **5 mm apart at one slot line**, while the backplane has base sockets at 8 mm pitch in one bank and ext sockets in another bank 40+ mm away; (c) nothing checks any of this. Contract (constants in `kicad/revb/mating.json`, consumed by the generator AND a new `check_revb_mating.py` in the tier suite): card base row centered x=50 at **5.0 mm** above the bottom edge, ext row centered **x=14.45** at **10.0 mm** (RC2014-style right-angle headers: the two rows' down-legs land 5 mm apart at the slot); backplane slot k = base socket row (x=50, y_k) + ext socket row (x=14.45, y_k+5), **slot pitch 18 mm**, 6 slots. Ext x-center moves 14.0→14.45 so its pin grid sits on the base grid's half-pitch (1.27 mm column separation; at 14.0 the base/ext bus columns would run only 0.82 mm apart). If slot pairs + power tail can't pass placement DRC inside 100×100, **grow the backplane** (≤100×115) rather than dropping slots — the 100×100 price cliff matters for cards that iterate, not the one-off backplane. | Two boards route-perfect and physically incompatible is exactly the class of error this project exists to make impossible; the D1.18 lesson (completeness as code) applied to mechanics. Gate: the checker must FAIL on today's geometry before the fix (proving it catches the known bug), then pass after. |
| D1.32 | What if the reversed-card keying proof (D1.4) fails in FreeCAD? | Decide at TG.3 with the model in hand: a reversed card mirrors its ext row to x≈85.55 where there is no socket — but 6 mm pins may simply hover rather than collide, so "second-row keying" may not self-enforce. Fallback options, in preference order: (a) per-slot **blocking standoff / unplated hole obstruction** at the mirrored-ext position (generator-emitted, +6 cheap parts); (b) RC2014 precedent — **convention only** (silk pin-1 arrows both sides), formally downgrading D1.4 and recording the residual risk. | Don't design the key blind; the FreeCAD negative test (TD.12) is precisely the oracle for this. Deferring the choice costs nothing — both options are generator-level, no card respin. **Resolved 2026-07-18 (TG.3): the base connector is centred/symmetric so a reversed card's base pins still seat; with generic 0.1″ headers the ext row can't be shown to bottom-out mechanically → adopt D1.32b convention-only (RC2014 precedent), risk recorded in `rev-b-mating-report.md`; blocking-post (a) held in reserve for bench.** |
| D1.33 | Why can't the mate-compatible backplane be routed by freerouting like the cards? | **The specctra DSN roundtrip can't represent the mate-forced column interleave.** Mate-compatibility (D1.31) forces the ext row to x=14.45 *inside* the 96.5 mm base span, so base and ext bus columns interleave ~1.27 mm apart. Emitted directly in pcbnew this is **DRC-clean** (0 violations), but `ExportSpecctraDSN` silently **drops the threading tracks** (195 base cols → 161 fixed wires; ext similar), so freerouting never sees them, re-routes them itself, and leaves a handful of nets unrouted (best observed: 2). Mitigations applied: base cols F.Cu / ext cols B.Cu (layer split); bottom-strip pullups placed **on their own bus columns** (R_INT→x=60 near its x≈55 column) so freerouting's residual job is short taps; JP_S5 beside J_FTDI. If freerouting still can't reach 0/0, the fallback is a **generator-emitted deterministic tail** (rails + taps in the two column-free strips), extending D1.29 to the whole backplane. | The two-bank layout that routed trivially in Stage C was only routable *because* it was NOT mate-compatible. Mate-compatibility and freerouting are in tension here; the columns being DRC-clean when emitted directly means determinism, not freerouting, is the right tool for this one board. **Superseded by D1.34.** |
| D1.34 | Locked column pre-routes + power rails still couldn't reach 0/0 (170+ attempts, freerouting failing even on mid-column base segments). What now? | **Retire the locked pre-routes entirely; the backplane routes like any other card.** Root cause narrowed: pcbnew's specctra export mangles LOCKED tracks around the mate-forced interleave — it drops a varying subset of the fixed wires, freerouting then routes around the half-visible corpse and reliably strands 1–40 connections. The SAME board with **no locked tracks routes 0/0 on attempt 1 with the day's best score** (997.78). `emit_bus_columns`/`emit_power_rails` stay behind `REVB_COLUMNS=1` for comparison only. Electrical note: the bus is now freerouted meanders instead of straight columns — irrelevant at VJUGA's few-MHz speeds on a 100 mm board. | An optimization must survive its pipeline. The columns were correct for the (non-mating) Stage-C layout and correct in pcbnew — but the DSN roundtrip is part of the pipeline, and through it they were net-negative. Evidence: two 0/0 flukes vs 170+ failures with columns; 2/2 clean routes without them. |

## Backplane order-safety decisions (pre-order audit follow-up, 2026-07-18)

| # | Question | Decision | Rationale / gate |
|---|---|---|---|
| D1.35 | The backplane — the power-entry board — has **zero capacitors**. Ship as is? | **No — add input power conditioning**: one bulk electrolytic (47 µF/16 V radial) plus one 100 nF ceramic across VCC5/GND at the USB-C entry, and a **polyfuse (~1 A hold) in series in the USB VBUS branch only** — the bench-supply header `J_PWR` stays wired directly to the rail, so the fuse never sits in the primary bring-up path and cannot be DNP'd into an open circuit. | Cards each carry a 100 nF local bypass, but the rail itself has no bulk storage and no inrush/short protection toward a USB host. Cheap parts, no respin later; the connectivity + D1.18 completeness guards automatically police the new wiring. |
| D1.36 | Six backplane footprints (USB-C, TO-92 supervisor, pushbutton, LED, 2×2 jumper, axial R) were **name-matched to the KiCad library, never verified** — the exact mechanism of the DIP-28 width bug. And the TO-92's pad→net map (1=GND, 2=RESET_N, 3=VCC5) is **part-family-specific** (right for DS1813-class, wrong for e.g. MCP100 pinouts). | **Pin the BOM first, then guard it.** Every backplane part gets an exact orderable MPN whose datasheet drawing is checked against the named footprint (drill ≥ pin, pitch, pad pattern, and for polarized/3-pin parts the pad→net mapping); where the KiCad footprint names a specific part (GCT USB4125, APEM MJTP1243), **buy exactly that part**. Then extend the footprint probe with a physical contract for non-DIPs: pad-count == board.json pin-count (catches silently floating pads, which no existing gate sees) + key dimensions. Guard must be negative-tested like PKG_WIDTH. | A footprint is only "verified" relative to a specific purchasable part; name-matching is how the last board-killer got in. The pad-count check closes a real hole: `add_fp` assigns nets by pad number and extra unmapped pads float with no DRC complaint. |

## Phase B2 design decisions (video card, planned 2026-07-18)

Planned ahead of the B1-exit rule (progressive elaboration says expand B2 after the
hardware tiers; the user requested the design plan now — bench findings from T1.11 may
still adjust it, and TI.5+ should not tape out before the platform boards prove the bus).

| # | Question | Decision | Rationale / gate |
|---|---|---|---|
| D2.1 | What do we adopt from [mengstr/TTL640x480](https://github.com/mengstr/TTL640x480)? | **The VGA timing chain, as a licensed adoption** (MIT — unlike the salfter respin, we may copy, not just reference): 640×480@60 sync + blanking from 9 TTL ICs (3×74HCT393 counters, 2×'00, 1×'10, 2×'20, 1×'04 + a diode-NOR), driven by a 25.175 MHz can oscillator. It is timing-ONLY — the framebuffer, CPU bus interface, pixel shifter, mode logic, and DAC are ours. Record the adopted commit hash + license text in the adoption note (TI.1); redraw in our generator pipeline (no Eagle import). | Proven-on-breadboard timing chain with simulation files, permissive license, THT-friendly chip set that matches our hand-solder ethos. Redrawing keeps the everything-is-generated discipline and our guards. |
| D2.2 | Can ~19 THT DIPs + DB15 route on 100×100 2-layer? | **Try the proven pipeline first** (hand-tuned PLACE + placement sweep + freerouting, exactly as io/cpu). Objective escape hatch: if the placement sweep cannot reach total-DRC 0/0, take a **4-layer exception for this one card** (cheap-tier 4-layer 100×100 exists now; the 2-layer rule was an economy choice, not a contract) rather than going SMD or splitting the card. | The io card (7 DIPs) routed near capacity; the video card roughly doubles that. An objective trigger avoids both premature 4-layer cost and endless 2-layer fiddling. Mating contract is layer-count-agnostic. |
| D2.3 | Framebuffer RAM part? | **Reuse AS6C1008 (128K×8 DIP-32), the mem card's SRAM.** Only 10,240 bytes are needed (0xD800+40×241), so a 62256 would do — but one SRAM part number across the machine beats saving 4 board-cm²; it is already in CHIP_TYPES, footprint-probed, width-guarded, and in the parts drawer. | BOM commonality is worth more than area on a card whose constraint is routing, not placement. High address lines strapped. |
| D2.4 | 320×241 source vs 480 visible lines: crop or letterbox? | **Defer to the oracle at TI.2** (the B2 sim gate already says "crop-vs-letterbox decided against the oracle"): pixel-double to 640×482 and either crop the last doubled row-pair or letterbox 240 rows. The chip-level twin's scanout checker compares both candidates against cosim's `vram.bin` rendering; whichever preserves the firmware's visible content wins and is frozen in `video-timing.json`. | Same D1.19 discipline: don't hand-pick a display decision the oracle can decide. The 241st row's content (blank vs used) is a firmware fact, not an opinion. |
| D2.5 | CPU/scanout contention strategy? | **Scanout has absolute priority; CPU waits.** The GAL asserts open-drain `WAIT_N` (the D1.4 ext line, pulled up on the backplane) for CPU framebuffer accesses that collide with active-region fetches; accesses land in blanking otherwise. Gate: the TI.2 **/WAIT phase sweep** (a CPU access launched at every dot-clock phase) must show zero lost/corrupted accesses and bounded wait. Mode overlays (MODE0/1) decode per the facts overlay table. | A fixed-priority design is provable by sweep; arbitration cleverness is not. This is exactly what the 10-pin extension exists for. |

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
