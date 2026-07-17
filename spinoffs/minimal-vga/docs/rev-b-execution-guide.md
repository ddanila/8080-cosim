# VJUGA rev B — execution guide

Task-level companion to `rev-b-build-plan.md`, written to be executed step by step
in later sessions. The **design is decided** — this guide is about executing it.

## Rules for the executing session (read first, every time)

1. **Do not redesign.** Decisions live in `rev-b-build-plan.md` (decisions table,
   S1–S13, C1–C7). If a discovered fact contradicts a decision: STOP the task,
   record the contradiction in this file under "Deviations", and surface it to the
   user. Never silently adapt.
2. **One task at a time, commit each.** Every task below is one commit-sized unit.
   Do not batch. Do not proceed past a red acceptance check.
3. **Copy repo patterns, don't invent.** Each task names the existing file to
   pattern-match. When in doubt, the existing artifact wins over general knowledge.
4. **Root is read-only for behavior.** Spin-off work must not change what root
   cosim/HDL/guards compute. Adding new files under `spinoffs/`, `ref/`,
   `scripts/`, `.github/` per the tasks below is fine.
5. **Fixed vs free.** Fixed: bus contract, memory/IO maps, card boundaries, gates,
   file names given below. Free (executor's judgment, no approval needed):
   testbench internals, script structure, component values, footprints, exact
   connector pin ordering *within* the contract.
6. **Progressive elaboration.** Only B0 is decomposed to task level. When a phase's
   exit gate goes green, the FIRST task of the next phase is to expand that phase's
   checklist to the same task level, using what was just learned. Do not expand
   ahead of time.

## Phase B0 — task breakdown (software only, no purchases) — ✅ ALL DONE 2026-07-17

Every T0 task below is complete and committed; one command re-verifies the phase:
`spinoffs/minimal-vga/sim/revb_tier_suite.sh` (green = B0 holds). See the Deviations
section for the T0.4 rewrite-vs-move resolution.

**T0.1 — `ref/juku-machine-facts.json`.**
Create the machine-facts file. Sections: `memory_map` (ROM/RAM/overlay modes from
`spinoffs/minimal-vga/docs/rev-a-gal-equations.md`), `framebuffer` (base 0xD800,
bytes 9640, geometry 40×241 — `docs/phase4-bench-bringup.md`), `io_ports` (PIC
0x00/0x01, 8255 0x04–0x07 — read them out of `cosim/trace.c`, cite line numbers in
a `provenance` field per entry), `pic_wiring` (ir0..ir7 from `hdl/juku_top.v`
~line 709), `timing` (frame-IRQ period 200000 from `docs/jmon33-hdl-probe.md`,
FDC 2 MHz-equivalent constants from `cosim/juku_fdc.c`).
*Acceptance:* every entry has `value` + `provenance`; values match the cited
sources when re-checked.

**T0.2 — commons guard.**
`scripts/check_spinoff_commons.py`, patterned on
`scripts/check_documentation_consistency.py`. It verifies constants in
`spinoffs/minimal-vga/hdl/revb/` and rev-b docs against T0.1's facts file.
*Acceptance:* passes on clean tree; fails when you locally edit a constant to a
wrong value (test both, then revert the test edit).

**T0.3 — bus contract doc.**
`spinoffs/minimal-vga/docs/rev-b-bus-contract.md`: the full 39-pin table (values
from the build plan's Bus contract section), 10-pin extension table, MODE0/1
default rules, memory map table and I/O port table *copied from the facts file*
(guard from T0.2 must cover these tables).
*Acceptance:* commons guard green; every bus signal from S11/S12 has a pin.

**T0.4 — HDL repartition.**
Create `spinoffs/minimal-vga/hdl/revb/`: `revb_cpu_card.v`, `revb_mem_card.v`,
`revb_io_card.v`, `revb_video_card.v`, `revb_backplane_top.v`. Ports = the bus
contract signals, exactly and only (plus per-card external connectors). Content:
split from `spinoffs/minimal-vga/hdl/vjuga_juku_top.v` — move logic, do not
rewrite it.
*Acceptance:* `revb_backplane_top` passes the existing boot oracle
(`spinoffs/minimal-vga/sim/boot_check.sh` pattern) byte-identical to cosim.
This is the phase's keystone check.

**T0.5 — bus-functional model + per-card unit testbenches.**
`revb_bus_bfm.v` driving one card at a time: mem/IO read/write cycles, /WAIT
handling, MODE0/1 levels. One TB per card.
*Acceptance:* all card TBs pass; a deliberately wrong address in the mem-card TB
fails (prove the TB can fail, then restore).

**T0.6 — bus-conflict assertions.**
In `revb_backplane_top`: assert never two drivers on D0–D7, and no card responds
in another's decode range (Memory must stay silent at 0xD800–0xFFFF window per
the overlay mode).
*Acceptance:* full boot runs assertion-clean; an injected double-drive test
trips the assertion (prove-then-remove the injection).

**T0.7 — tier-suite hook.**
Make the assembled rev B twin runnable under the root banner/boot guard the same
way `vjuga_juku_top` is run today (see `sync/boot_check.sh` and the spinoff
`sim/` wrappers). Deeper guards (jmon33, keyboard-react, FDC) hook up in their
tiers, not now.
*Acceptance:* one command runs the rev B banner check end to end.

**T0.8 — CI wiring.**
Path-gate the rev B sims into `.github/workflows/hdl.yml` (new paths trigger:
`spinoffs/minimal-vga/hdl/revb/**`); add the commons guard to `ci.yml` generic job.
*Acceptance:* CI green on push; touching a revb file triggers the HDL job.

**T0.9 — B1-population power budget.**
One table in the bus-contract doc: per-card current estimate (method + numbers
patterned on `rev-a-power-budget.md`) for backplane+CPU+Memory+I/O(UART-only),
vs the USB-C 5 V budget.
*Acceptance:* total ≤ 60% of budget (headroom rule); commons guard covers the
framebuffer/map numbers cited.

**T0.10 — B0 exit review.**
Re-run everything: boot oracle, all card TBs, assertions, commons guard, CI.
Update `rev-b-build-plan.md` marking B0 done; expand Phase B1 checklist to task
level (rule 6).
*Acceptance:* all green in one session; B1 tasks written.

## Phase B1 — task breakdown (planned to B0 depth, 2026-07-17)

Minimum tier: backplane + CPU + Memory + I/O(UART-only). Design decisions D1.1–D1.9
in `rev-b-build-plan.md` are settled — do not reopen them. T1.0–T1.9 are
software/sim/CAD and can proceed now; T1.10–T1.11 are **hardware-blocked** (need
the ordered boards) — never mark them done from a desk. One commit per task.

**T1.0 — serial facts + contract update (D1.1, D1.4).**
Add `serial_ports` to `ref/juku-machine-facts.json`: data 0x08 (A0=0),
control/status 0x09 (A0=1), decoded window 0x08–0x0B; provenance
`docs/serial-handoff.md` ("bus-visible at the decoded 0x08..0x0B USART window") +
`hdl/juku_top.v` '138 row (`cs_sio0_n`). Add the row to the bus-contract I/O map
and the 0x08/0x09 values to the guard's canonical list. Record D1.4's extension
placement (second 0.1" row, 2.54 mm behind base, pin-1-end aligned) in the bus
contract's extension section.
*Acceptance:* `scripts/check_spinoff_commons.py` green AND fails if the contract's
0x08 row is deleted (prove, restore).

**T1.1 — bring-up ROM source + cosim oracle (S13, D1.2, D1.3).**
`spinoffs/minimal-vga/roms/revb-bringup/`: a commented listing + a Python
byte-emitter build script (no new assembler dependency; builder pattern:
`scripts/export_reconstructed_proms.py`-style self-contained generator) producing
`revb_bringup.bin` (org 0x0000, 8080-subset opcodes only). Behavior: init 8251
(mode, then command with **TxEN so bit0 doubles as cosim's "ready"** — D1.2,
document in source); print banner; walking-1s + address-in-cell RAM test over
**0x4000–0xD7FF** (D1.3); print `RAM PASS nnnn` / `RAM FAIL @addr`; ROM checksum
print; then a dump/deposit/jump monitor loop on the UART. Every TX via a bounded
TxRDY poll.
*Acceptance:* cosim boots the image; the `[IOSEQ] OUT port=0x08` stream contains
the banner and `RAM PASS`; a deliberately corrupted build (flip one ROM byte)
prints the checksum mismatch (prove, restore).

**T1.2 — minimum-tier twin + serial-stream gate (D1.2).**
Parameterize `revb_backplane_top` with `VIDEO_PRESENT` (0 = Video card absent;
MODE0/1 fall to backplane defaults, framebuffer window unowned) and add the UART
to `revb_io_card` for simulation by instantiating the **root `usart_8251` model
verbatim** at 0x08/0x09 with a TX-byte `$display` logger. New
`sim/revb_bringup_check.sh` (pattern: `revb_boot_check.sh`): build cosim, extract
its OUT-0x08 stream; run the minimum-tier twin on the T1.1 ROM to CPU HALT or
watchdog; diff the two TX byte streams. Wire into `revb_tier_suite.sh`.
*Acceptance:* TX streams byte-identical; `RAM PASS` present; bus monitor
conflict-clean with the framebuffer window unowned.

**T1.3–T1.6 — board specs, one card per task (D1.5, D1.7, S11).**
`spinoffs/minimal-vga/kicad/revb/{backplane,cpu-card,mem-card,io-card}.board.json`
+ a shared generator/check pair cloned from the rev A flow
(`kicad/minimal-vga.board.json`, `gen_rev_a_pcb.py`, `check_rev_a_physical.py`).
Contents per the bus contract + chip map: backplane = 6 slots @ 19 mm, 39+10
connectors per D1.4, USB-C power, reset supervisor (sole RESET_N driver, S7),
FTDI header + S5 jumper, MODE0/1 default pulls (S11), wired-OR pull-ups (S4);
cpu-card = Z80 + socketed osc + '245/'244 buffers; mem-card = 27C256 + AS6C1008 +
GAL22V10 + NOP-plug/J95-style headers (S9); io-card = 8251 + local baud osc +
decode, with 8255/PIC/keyboard footprints marked DNP (D1.7).
*Acceptance (each):* board.json validates; generated connectivity matches the bus
contract pin table (checked, not eyeballed); ≤100×100 outline.

**T1.7 — per-card LVS.**
Yosys-netlist each `hdl/revb/revb_*_card.v` vs its board.json connectivity
(pattern: `hdl/minimal_vga_lvs.*` + `sync/check.sh` board-direct fallback). Sim-only
constructs (`$fopen`/vw counter/monitor) excluded via the same conventions rev A
uses for LVS-invisible adjuncts.
*Acceptance:* LVS clean per card; a deliberately mis-wired pin in a board.json
copy fails (prove, restore); wired into CI paths.

**T1.8 — manufacturing-readiness + silk checks.**
`kicad/revb/check_revb_ready.sh`: DRC/fab rules (2-layer, ≤100×100, cheap-tier
constraints) + machine-checkable silk items (pin-1 marks, card name+rev, bus pin
labels, extension-key arrow, "NO HOT-PLUG", NOP/J95 header labels) per the
coverage-matrix checklist.
*Acceptance:* passes all four boards; removing a silk item from a board.json copy
fails (prove, restore).

**T1.9 — 3D/STEP mating check.**
Export STEP per board, assemble in FreeCAD, verify connector mating, 19 mm pitch
clearance (tallest part vs neighbor card), extension-row keying blocks reversed
insertion geometrically.
*Acceptance:* assembled screenshots committed to `docs/`; no clash; keying
confirmed by attempting the reversed placement in CAD.

**T1.10 — order gate + order (hardware-blocked).**
All of T1.0–T1.9 green + power budget re-check (bus-contract table) → order at the
≤100×100 2-layer tier. *Acceptance:* order placed; fab package SHA256 recorded in
the bench log doc skeleton.

**T1.11 — bench bring-up (hardware-blocked, D1.9).**
Create `docs/rev-b-b1-bench-log.md` (expected-vs-observed per step, pattern:
`docs/phase4-bench-bringup.md`): backplane-alone (5 V at every slot, RESET_N pulse,
CLK present) → power-only cards (current draw vs budget) → NOP free-run plug +
analyzer on A0–A15 (+ bus-timing spot-check vs the S1 clock) → bring-up ROM.
*Acceptance:* monitor prompt + `RAM PASS` over the backplane FTDI header; log
committed.

At B1 exit, expand Phase B2 to task level (rule 6).

## Phase B2 / B3 / B4 — gates only (do not expand yet)

As specified in `rev-b-build-plan.md` Phases: B2 = /WAIT sweep + mode-default sim
gates, ekta37 banner on glass, byte-identical readback. B3 = keyboard/PIC
population, mode-switch overlay test, jmon33 + keyboard-react parity. B4 = FDC,
root FDC guard parity, EKDOS `A>` + write-sector readback on a writable copy.

## Deviations

- **2026-07-17 — T0.4 "move logic, do not rewrite" is infeasible; rewrote instead
  (oracle-gated).** `vjuga_juku_top.v` is a DRAM machine (РУ5 + U24 sequencer) with
  the framebuffer *inside* main memory. Rev B decision C1 is SRAM (no U10–U24) and
  the framebuffer lives on a separate Video card (bus contract: Memory card must not
  respond at 0xD800). A mechanical "move" can't satisfy both — it would keep DRAM
  (violating C1) or leave the framebuffer in the Memory card (defeating the very
  boundary the repartition exists to prove). Resolution: the rev B card modules
  **model the rev B architecture** (SRAM main memory on the Memory card; SRAM
  framebuffer at 0xD800 on the Video card; no DRAM/U24/wait sequencer), reusing
  `vjuga_juku_top.v`'s *functional* decode/overlay/IO logic verbatim where it is
  memory-technology-independent (decode_prom/re3_prom Mode A/B, overlay(), rom_idx,
  Port-C mode handling). This is a design-faithful realization of an already-made
  decision (C1), not a new design choice; the keystone byte-identity check vs cosim
  still gates it. **Future simpler-model sessions: treat T0.4 as "realize the rev B
  card architecture, oracle-gated," not "mechanically split the DRAM twin."**
