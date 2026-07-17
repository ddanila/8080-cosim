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

## Phase B0 — task breakdown (software only, no purchases)

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

## Phase B1 — checklist (expand to tasks at B0 exit)

- Bring-up ROM: source under `spinoffs/minimal-vga/roms/` (8080-subset, S13);
  cosim runs it as oracle (pattern: how `ekta37_z80.bin` is built/checked in
  `spinoffs/minimal-vga/tools/make_z80_rom.c` and `roms/README.md`). Monitor
  commands: dump/deposit/jump + RAM test + ROM checksum print.
- KiCad projects: `spinoffs/minimal-vga/kicad/revb/{backplane,cpu-card,mem-card,io-card}/`.
- Per-card LVS vs the revb HDL modules (pattern: `hdl/minimal_vga_lvs.*`).
- Manufacturing-readiness script variant (pattern:
  `kicad/check_replica_manufacturing_ready.sh`) + silk checklist from the build
  plan's coverage matrix.
- 3D/STEP card↔backplane mating check before order.
- Order at the ≤100×100 2-layer tier.
- Bench: backplane smoke → power-only → NOP plug + analyzer → bring-up ROM.
  Record expected-vs-observed per step in a bench log doc.
- Exit: monitor prompt + RAM test PASS via backplane FTDI header.

## Phase B2 / B3 / B4 — gates only (do not expand yet)

As specified in `rev-b-build-plan.md` Phases: B2 = /WAIT sweep + mode-default sim
gates, ekta37 banner on glass, byte-identical readback. B3 = keyboard/PIC
population, mode-switch overlay test, jmon33 + keyboard-react parity. B4 = FDC,
root FDC guard parity, EKDOS `A>` + write-sector readback on a writable copy.

## Deviations

(Executing sessions append dated entries here when reality contradicts the plan.
Empty so far.)
