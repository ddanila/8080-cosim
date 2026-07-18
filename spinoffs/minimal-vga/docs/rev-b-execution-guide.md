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

### B1 execution status (2026-07-17)

- **T1.0 DONE** — UART ports 0x08-0x0B in facts/contract/guard; extension placement recorded. Guard catches a wrong port value.
- **T1.1 DONE** — `roms/revb-bringup/` bring-up ROM (self-contained assembler). cosim OUT-0x08 stream = `VJUGA rev B bring-up / RAM PASS / ROM OK / READY`; corrupted build → `ROM BAD` (negative control verified).
- **T1.2 DONE** — minimum-tier twin (`VIDEO_PRESENT=0`, real `usart_8251` at 0x08) TX stream byte-identical to cosim (47 bytes), exercising the real TxRDY handshake; `sim/revb_bringup_check.sh`, in the tier suite + CI. ekta37 boot check unaffected (params default off).
- **T1.3-T1.6 DONE at the connectivity stage** — `kicad/revb/bus-pinout.json` + `cards.json` + `scripts/check_revb_boards.py` (driver-class rules, memory/IO ownership, card-HDL port consistency; negative control catches a decode overlap). In the tier suite + CI.

**Remaining (T1.7–T1.9): the B1-CAD continuation — planned below as tasks TC.1–TC.8.**
CORRECTION (2026-07-17, later session): the earlier note claiming `kicad-cli` is
absent on this Mac was wrong — KiCad 10.0.4 is installed as a Homebrew-cask app
bundle, merely off PATH; the repo's `scripts/find-kicad-cli.sh` / `find-kicad-python.sh`
locate it. Only FreeCAD is genuinely missing locally (brew cask, or the Linux box).
T1.10 order / T1.11 bench stay hardware-blocked by definition.

## B1-CAD continuation — task breakdown (TC.1–TC.8, planned 2026-07-17)

Design decisions D1.10–D1.15 in `rev-b-build-plan.md` are settled — don't reopen.
Same executor rules: one task per commit, red gate = stop, patterns over invention.
Everything except TC.7's FreeCAD step is runnable on this Mac via the locator
scripts; committed generated artifacts record their generating environment (D1.10).

**TC.1 — KiCad environment wrapper.**
`spinoffs/minimal-vga/kicad/revb/env.sh`: resolve `KICAD_CLI`/`KICAD_PYTHON` via
the locator scripts, set `KICAD_FOOTPRINTS` for the Mac app bundle (the
`gen_rev_a_pcb.py` documented path), print resolved versions. Every TC script
sources it and **skips-not-fails** when a tool is missing (CI pattern).
*Acceptance:* `env.sh` prints kicad-cli 10.x + pcbnew python on this Mac; a PATH
without KiCad yields the skip path, not an error.

**TC.2 — per-card board.json (4 specs, one commit each is fine).**
`kicad/revb/{backplane,cpu-card,mem-card,io-card}.board.json` — chips+nets in the
rev A shape (`kicad/minimal-vga.board.json`), bus connector as a component whose
pin numbers map 1:1 to `bus-pinout.json`. Extend `scripts/check_revb_boards.py`
with the D1.12 cross-check (connector nets ↔ cards.json roles ↔ pinout).
*Acceptance:* checker green; moving one connector net in a temp copy fails
(prove-then-restore).

**TC.3 — structural LVS models + structural boot oracle (D1.11).**
`hdl/revb/revb_{cpu,mem,io}_card_lvs.v` (+ backplane netlist top): chip-level
instances reusing `hdl/devices.v` models (`usart_8251`, `decode_prom`, `re3_prom`)
plus thin new ones ('245/'244, SRAM, ROM, GAL-equation module). Assemble a
structural twin; run the **banner boot oracle** and the **bring-up TX-stream
check** against it.
*Acceptance:* structural twin byte-identical to cosim on both checks — the LVS
models are thereby behaviorally validated, root-`juku_top` style.

**TC.4 — per-card LVS wiring.**
`spinoffs/minimal-vga/sync/revb_lvs.sh` per card: yosys-netlist the LVS model,
compare vs its board.json via `sync/lvs.py --board` (works everywhere) and via the
kicad-cli schematic round-trip when available (pattern: `spinoffs/minimal-vga/sync/check.sh`
+ `sync/map.json`). Wire into tier suite + CI (board-direct path).
*Acceptance:* LVS clean ×4; a mis-wired pin in a temp board.json copy fails.

**TC.5 — PCB generators (D1.13).**
`kicad/revb/gen_revb_pcb.py` (parameterized clone of `gen_rev_a_pcb.py`): outlines
(backplane ≤100×100, cards ~100×~60), 39+10 connectors per D1.4 geometry, 19 mm
slot pitch on the backplane, generator-emitted silk (full checklist). Regeneration
must be deterministic (same JSON in → byte-stable PCB out, rev A convention).
*Acceptance:* four `.kicad_pcb` generated on this Mac; regen diff-clean; silk
items present in the PCB text (grep-checkable).

**TC.6 — DRC + fab readiness (D1.14).**
`kicad/revb/check_revb_ready.sh`: `kicad-cli pcb drc` per board (zero errors),
2-layer cheap-tier constraint checks, silk machine-checks, plus the rev A
placement/footprint check patterns (`check_rev_a_placement.py`, `check_rev_a_footprints.py`).
*Acceptance:* all four boards DRC-clean + checks green; an injected
overlapping-footprint temp copy fails.

**TC.7 — STEP export + FreeCAD mating/keying (D1.15).**
`kicad-cli pcb export step` ×4; `kicad/revb/mate_check.py` under `freecadcmd`:
assemble at 19 mm pitch, boolean interference = zero; **reversed-card placement
must collide** (keying proof). If headless FreeCAD proves unworkable, fall back to
GUI assembly + committed screenshots/clearances and say so in the doc.
*Acceptance:* interference report committed (`docs/rev-b-mating-report.md`):
normal = no collision, reversed = collision.

**TC.8 — CAD exit review → order gate.**
Re-run tier suite + TC.4/TC.6/TC.7; re-check the power budget table against final
BOMs; produce the fab package (pattern: `export_fab.sh` + `package_rev_a_upload.py`)
with SHA256 recorded. This closes T1.7–T1.9 and arms **T1.10 (order)**.
*Acceptance:* everything green in one session; package hash recorded; T1.10 is
purely a purchasing decision.

### B1-CAD execution status (2026-07-17)

- **Tools installed + resolved:** KiCad 10.0.4 (was only off-PATH) + FreeCAD 1.1.1 (`~/Applications`), both via `env.sh`.
- **TC.1 DONE** — `kicad/revb/env.sh` resolves kicad-cli/python/footprints/freecadcmd; skip-not-fail; zsh-safe.
- **TC.2 DONE** — `gen_revb_boards.py` deterministically emits four `<card>.board.json` (bus connectors from `bus-pinout.json` + IC DIP pinouts); `check_revb_boards.py` cross-checks connector==pinout and chip-bus-pins==roles. **Caught a real bug**: the mem GAL had inherited rev A's mem+I/O decode; rev B is memory-only.
- **TC.3 PARTIAL** — board.json now carries the `nets` section (LVS-ready shape for `netlist_from_board.py`) + a nets-in-sync check. **Correction to D1.11:** its "structural model must boot" was the `juku_top` precedent; the applicable **rev A spinoff** precedent keeps the booting model (`revb_backplane_top`, already byte-identical) SEPARATE from an empty-bodied LVS netlist. So TC.3-full = author an *independent* structural netlist (rev A `minimal_vga_lvs.v` style), not make the behavioral model structural.

## B1-CAD REVAMPED breakdown (TD stages, planned 2026-07-17 — supersedes TC.3-full–TC.8)

Why revamped: TC execution showed the remaining work is (a) missing **schematic
depth** (in-path buffers, I/O selects, reset polarity, backplane passives), (b)
LVS needs independently-authored netlists, and (c) the pipeline is **iterative**.
New decisions D1.16–D1.20 in the build plan address these — don't reopen them.
Process rules: one task = one commit; **stages are session boundaries** (never
start a new stage in a session's tail); equations-to-silicon follow the
**behavioral-twin-first rule (D1.19)**.

### Stage A — netlist completion to schematic depth (no CAD tools needed)

**TD.0 — oracle-test the control equations (D1.19).**
Encode in the behavioral models: '245 DIR/OE + '244 terms in `revb_cpu_card.v`
(D1.17), the I/O-select GAL terms + 8251 reset inversion in `revb_io_card.v`
(D1.16). Re-run boot + bring-up oracles (`revb_tier_suite.sh`).
*Acceptance:* byte-identity holds with the explicit control terms; deliberately
inverting the '245 DIR term breaks the boot (prove-then-restore).

**TD.1 — checker: D1.18 completeness rule.**
Extend `scripts/check_revb_boards.py`: on a populated card, internal nets need
≥2 endpoints or `_TIE`/`_NC`/DNP tags; bus nets exempt.
*Acceptance:* the current (incomplete) board.jsons FAIL this check — that failure
list *is* the Stage A worklist. (Guard goes in first, red; TD.2–TD.5 turn it green
card by card. Keep it out of the tier suite until TD.5.)

**TD.2 — mem card netlist complete.**
ROM A14/VPP ties, SRAM ties, GAL decode wiring (memory-only, D1.19-derived terms),
decoupling, NOP-plug + J95-style headers (S9). Plus
`docs/rev-b-gal-equations.md` — the mem-decode + I/O-select GAL programming doc,
derived from the oracle-tested behavioral terms (pattern: `rev-a-gal-equations.md`).
*Acceptance:* mem card passes the D1.18 check; GAL doc terms textually match the
behavioral source (cite lines).

**TD.3 — io card netlist complete.**
ATF16V8 selects (D1.16), 8251 support wiring (C_D=A0, TXC/RXC from the local baud
osc, RESET inversion, modem-control ties), DNP 8255/PIC footprint stubs.
*Acceptance:* io card passes D1.18.

**TD.4 — cpu card netlist complete.**
Buffers in-path per D1.17 (local nets), oscillator, observability header.
*Acceptance:* cpu card passes D1.18.

**TD.5 — backplane netlist complete.**
6 parallel slots, MODE/wired-OR pulls (S4/S11), reset supervisor (sole RESET_N
driver), USB-C 5V (CC resistors, rev A pattern), FTDI header + S5 jumper, power
LED. *Acceptance:* backplane passes D1.18; D1.18 check joins the tier suite (all
four green).

### Stage A status — ✅ DONE (2026-07-17)

TD.0–TD.5 complete + committed. All four card netlists (`kicad/revb/*.board.json`,
generated by `gen_revb_boards.py`) pass D1.18 completeness, now gating in the tier
suite + CI. Boot + bring-up stay byte-identical to cosim. Findings folded in:
D1.17 corrected (refresh+glitch-safe '245 /OE) with a monitor refresh-drive
assertion; mem GAL needs A11–A15 to clear the 0xD800 video window
(`rev-b-gal-equations.md`); io I/O-selects + 8251 reset inversion via an ATF16V8
(D1.16); **D1.21 — CPU card unbuffered in B1** (RC2014 precedent; '245/'244 = optional
margin). Next session: **Stage B (TD.6, mem card pipeline)** — the first task that
uses kicad-cli/yosys.

### Stage B — pipeline-prove on the mem card only (D1.20)
*(Detailed 2026-07-17; decisions D1.22–D1.25 in the build plan. One task = one
commit. Everything runs through `kicad/revb/env.sh`; steps needing a missing tool
SKIP, never fail, except where marked mandatory.)*

**TD.6.1 — pinmap emitter (D1.22).**
`kicad/revb/gen_revb_lvs_map.py`: emit `spinoffs/minimal-vga/sync/revb_mem_map.json`
from `gen_revb_boards.py`'s CHIP_TYPES + the instance map (U1→U_ROM, U2→U_SRAM,
U3→U_DEC). Shape: rev A `sync/map.json` (`instances` + `pinmaps.kicad` keyed by
chip type, pin number → logical name).
*Acceptance:* regen is diff-clean; the emitter imports the pin tables from
`gen_revb_boards.py` (no literal pin copies in the emitter source).

**TD.6.2 — structural LVS netlist.**
`hdl/revb/revb_mem_lvs.v`: **empty-bodied** modules (`rom_27c256_lvs`,
`sram_as6c1008_lvs`, `gal22v10_memdec_lvs`) + a top that wires them per the bus
contract and the card's internal nets (ROM_CE_N, RAM_CE_N, MEM_RD/WR_N) — rev A
`minimal_vga_lvs.v` style, LVS-only (the *booting* model stays `revb_mem_card.v`).
*Acceptance:* `yosys write_json` succeeds on it (pattern: spinoff `sync/check.sh`).

**TD.6.3 — LVS runner + wiring (mandatory board-direct).**
`spinoffs/minimal-vga/sync/revb_lvs.sh`: yosys → `sync/lvs.py --hdl <json>
--board kicad/revb/mem.board.json --map sync/revb_mem_map.json`. Bonus path when
kicad-cli present: `kicad/gen_kicad_sch.py` → `kicad-cli sch export netlist` →
`--kicad` round-trip. Wire into `revb_tier_suite.sh` gated on `command -v yosys`
(skip-not-fail — the CI behavioral job has no yosys; the CI lvs job does).
*Acceptance:* LVS PASS; a mis-wired pin in a temp board.json copy FAILS
(prove-then-restore); tier suite green both with and without yosys on PATH.

**TD.7.1 — footprint availability probe (D1.23 risk).**
`kicad/revb/check_revb_footprints.py`: resolve every needed footprint
(**THT 1×39** + 1×10 pin headers, DIP-24/28/32 sockets, C_100N, R axial, LED,
USB-C, switch) against `KICAD_FOOTPRINTS`; write the chosen names into
`kicad/revb/footprints.json`. If THT 1×39 is absent, record the decision to
generate the pad row programmatically instead (documented fallback, not a stall).
*Acceptance:* every mem-card footprint resolves (or has its fallback recorded).

**TD.7.2 — PCB generator.**
`kicad/revb/gen_revb_pcb.py` (parameterized clone of `gen_rev_a_pcb.py`, run via
`KICAD_PYTHON`): mem-card outline + connector geometry per **D1.23**, DIP
placement per `rev-a-placement-rules.md`, 2-layer stackup + JLC cheap-tier rules,
**generator-emitted silk** (name+rev, pin-1 marks, bus pin labels, extension key
arrow, NO HOT-PLUG, J_OBS/J_NOP labels).
*Acceptance:* emits `fab/minimal-vga/revb/mem.kicad_pcb`; TD.7.3 check green.

**TD.7.3 — PCB content check (D1.25).**
`kicad/revb/check_revb_mem_pcb.py` (pattern: `check_rev_a_pcb.py`): outline is
100×60, base-row pin 1 at the left/bottom-edge position, extension row 2.54 mm
above and end-aligned, every board.json ref placed, silk list present.
*Acceptance:* green; a silk item deleted from a temp copy fails (prove-restore).

**TD.7.4 — routing (D1.24).**
Clone `route_rev_a_pcb.sh` → `kicad/revb/route_revb_pcb.sh`: DSN export →
freerouting → SES import → zones. Probe Java per the rev A order; if no JRE,
this task (only) is tool-blocked — record it, don't hand-route.
*Acceptance:* zero unrouted nets reported on import.

**TD.8.1 — DRC to zero.**
`kicad-cli pcb drc --exit-code-violations` in `kicad/revb/check_revb_ready.sh`
(mem only for now); iterate the generator (not the .kicad_pcb) until clean.
*Acceptance:* zero violations; report under `fab/minimal-vga/revb/` with its
SHA256 recorded in `docs/rev-b-status.md`.

**TD.8.2 — STEP + measured sanity.**
`kicad-cli pcb export step`; `kicad/revb/mem_step_sanity.py` under `freecadcmd`:
bounding box == 100×60 (±0.1), connector row on the bottom edge at the D1.23
coordinates. STEP stays in untracked `fab/`, SHA256 recorded.
*Acceptance:* sanity script prints PASS with measured numbers.

**TD.8.3 — Stage B exit.**
One wrapper `kicad/revb/check_revb_mem.sh` chaining TD.6.3 → TD.7.2/7.3 → TD.8.1
(STEP step gated on tools); update status doc; expand Stage C per rule 6 —
replication should be brief since the pipeline is now machinery, not exploration.
*Acceptance:* one command green end-to-end. **Pipeline proven.**

### Stage B status — PARTIAL (2026-07-17)

The mem-card pipeline **machinery is proven** — every stage runs and produces
validated output — with two stages tool/interaction-blocked:

- **TD.6.1–6.3 LVS ✅** — structural netlist IN SYNC with the generated board.json
  (28 nets, mis-wire caught); in the tier suite + CI lvs job.
- **TD.7.1 footprints ✅** — all 7 mem types resolve (THT 1×39 present; no fallback).
- **TD.7.2/7.3 PCB gen + content check ✅** — `gen_revb_pcb.py` emits
  `fab/minimal-vga/revb/mem.kicad_pcb` (100×60, 10 footprints, 62 nets, bus on the
  bottom edge, silk present); `check_revb_mem_pcb.py` green. (fab/ is untracked;
  PCB sha256 `01d797d3…`.)
- **TD.8.2 STEP ✅ (pipeline)** — exports and loads in FreeCAD, X measured 100.00.
- **TD.7.4 routing ⛔ tool-blocked** — freerouting needs a **Java 25** runtime +
  freerouting.jar (only Java 17 here). `route_revb_pcb.sh` is ready and skips
  cleanly; note KiCad 10's kicad-cli has no specctra export, so DSN uses pcbnew.
- **TD.8.1 DRC / placement ⬜ needs visual layout iteration** — first DRC pass shows
  courtyard/clearance overlaps (rough hardcoded placement) + 90 unrouted items;
  STEP bbox Y=155 vs 60 confirms a component 3D extent overshoots. Getting a
  DRC-clean routed board is the watch-KiCad work: iterate `PLACE` in
  `gen_revb_pcb.py` (spread/rotate DIPs, move silk off copper) with the board open,
  then route (needs Java 25), then DRC to zero.

`check_revb_mem.sh` runs the proven (tool-independent-where-possible) stages end to
end. **Resume:** placement iteration + Java 25 routing, in a KiCad-visible session.

### Stage B completion — TE tasks (planned 2026-07-17; D1.27 applies)

**TE.1 — Java 25 + freerouting install (home folder, user's convention).**
Temurin 25 JRE → `~/.jdks/` (or repo `.tools/jre25`, the `route_rev_a_pcb.sh`
probe path); freerouting.jar → `.tools/freerouting/freerouting.jar` (both
untracked). Record versions in the bench-log-style note.
*Acceptance:* `route_revb_pcb.sh mem` passes its gates and *reaches* freerouting
(no SKIP lines).

**TE.2 — placement iteration to placement-clean (no Java needed).**
Iterate `PLACE` in `gen_revb_pcb.py` against `kicad-cli pcb drc` JSON until
**placement-class violations = 0** (D1.27): spread/rotate DIPs, move silk off
copper, respect courtyards; find the STEP Y=155 overshoot (a 3D model extent) and
fix the offending placement/rotation. Add `render_revb_preview.sh` (rev A
`render_*_preview.sh` pattern) and commit a PNG to `docs/` for eyeball review.
*Acceptance:* placement-class = 0 in DRC JSON; STEP bbox ≈ 100×60 (X and Y);
preview committed. (Unconnected count is ignored here.)

**TE.3 — route + total-zero DRC.**
`route_revb_pcb.sh mem` (freerouting, TE.1) → `kicad-cli pcb drc`:
**violations 0, unconnected 0**. Record PCB/STEP/DRC-report SHA256s in the status
doc (D1.25).
*Acceptance:* total-zero DRC JSON; hashes recorded.

**TE.4 — Stage B exit.**
`check_revb_mem.sh` gains the D1.27 post-route gate; status/ledger flipped to ✅;
Stage C begins. *Acceptance:* one command green end-to-end, including DRC.

### Stage C status (2026-07-18)

- **TD.9 io ✅ DONE** — full D1.26 B3 wiring (8255/8259/74148/keyboard, DNP; GAL adds
  INT_N/INTA_N/IO_RESET inversion), io LVS IN SYNC, **D1.26 wiring assertion** in the
  board checker, placement-clean + **fully routed, DRC 0/0** at 100×100, STEP + preview.
- **TD.10 cpu 🟡 placement-clean, 47/48 routed** — netlist + LVS-trivial (one logic IC)
  + placement-clean at 100×70; A8 is a **deterministic** 2-layer fan-out constraint
  (12/12 route attempts leave it) that needs address-pin-order-matched placement or a
  manual trace. The layout-craft tail.
- **TD.11 backplane ⬜** — needs a PCB-gen enhancement first: `gen_revb_pcb.py` splits
  a REVB_BUS_39_10 into hardcoded `J_BUS`/`J_EXT`, but the backplane has **six**
  (`J_S1..J_S6`) — the split must use per-slot ref names. Then a 22-part layout
  (6 slots @ 19 mm + power/reset/pulls/FTDI/LED) and parallel-bus routing. No LVS.

Resume: cpu A8 + backplane are visual/gen work best done with KiCad open.

### Stage C finish — TF tasks (planned 2026-07-18; D1.28/D1.29 in the build plan)

One task = one commit; `git pull --rebase` before every push (the remote moves).

**TF.1 — cpu A8 via placement sweep (D1.28).**
`kicad/revb/sweep_cpu_place.sh`: loop U1 x ∈ {25..45 step 2} × rot ∈ {90, 270};
per point: patch a copy of the PLACE entry → regenerate → `check_revb_drc.py cpu
--placement` (skip point if not 0) → export DSN → ≤2 freerouting attempts → import
→ `--total`. Stop at the first **0/0**; write the winning coordinates back into
`gen_revb_pcb.py` permanently (with a comment naming the sweep) and delete the
sweep's temp boards. Fallback if all points fail: emit ONE generator-authored
track for A8 (documented in the PLACE comment).
*Acceptance:* `check_revb_drc.py cpu --total` = 0/0 from a fresh regenerate+route;
winning placement committed in the generator, not just in fab/.
**DONE (2026-07-18):** sweep hit at **U1 x=41, rot=90** (was x=35) — candidate #9,
first 0/0 in the grid. x∈{25..33} routed but left DRC dirty; x∈{35..39} did not
converge (the known deterministic A8 failure); x=41 routes clean. Winning coord
folded into `gen_revb_pcb.py`; fresh regenerate+route → `--total` 0/0; STEP + preview
regenerated. `REVB_SWEEP_{REF,X,ROT}` env hook in the generator drives the search;
`FR_ATTEMPTS` env caps route retries for the sweep.

**TF.2 — multi-slot connector support in the PCB generator (D1.29 prerequisite).**
`gen_revb_pcb.py`: the `REVB_BUS_39_10` branch derives refs from the component ref
(`J_S3` → `J_S3_BUS`/`J_S3_EXT`; a bare `J_BUS` keeps today's names, cards
unaffected). Backplane PLACE: six slot pairs at the same x-origin, y = 19 mm pitch
(base rows at y ≈ 8, 27, 46, 65, 84, 103 → needs BOARD_H check vs 100 — if 6×19
overflows, drop pitch to 18 mm, NOT the slot count; record the final pitch in the
bus contract). Power/reset/FTDI/LED parts go in the inter-slot gaps and margins.
*Acceptance:* backplane regenerates with 12 connector footprints + all 16 discrete
parts placed; `check_revb_pcb.py backplane` green (teach it the 12-connector
expectation); placement-DRC 0.
**DONE (2026-07-18):** 28 footprints placed, placement DRC 0/0. **Deviation → D1.30:**
the 39-pin base spans nearly the full width, so co-located base+ext-per-slot pairs
would put ext bodies on top of base bus columns. Instead the six base connectors form
a column-aligned bank in the UPPER region and the six ext connectors a separate bank
LOWER-LEFT (two independent bussed banks, each cleanly column-routable); power tail in
the free lower-right quadrant. Footprint probe + `USB_C_PWR` logical-pin→pad map added.

**TF.3 — backplane column-route (D1.29).**
Generator emits vertical F.Cu tracks joining pin N of slot k to slot k+1 for all
49 columns (straight segments, same x per column), then `route_revb_pcb.sh
backplane` handles only the power tail (pulls/USB-C/supervisor/FTDI/LED nets).
*Acceptance:* `check_revb_drc.py backplane --total` = 0/0; STEP + previews
rendered; hashes recorded.
**DONE (2026-07-18):** `emit_bus_columns()` emits 245 locked F.Cu column segments
(49 pins × 5 gaps); freerouting fills only the tail → **0/0 on attempt 1**. Two fixes
found: (a) bus-signal pullups moved into the interior band between the banks so each
taps its column with a short stub — a long cross-board pullup trace otherwise dragged
a via into a corner (copper-edge fail); (b) `route_revb_pcb.sh` now exports the DSN
once from a pristine copy and gates each retry on TOTAL DRC 0/0 (freerouting can log
success yet leave a net island). STEP + previews rendered.

**TF.4 — Stage C exit.**
Re-run the tier suite + all per-card gates (mem/io/cpu/backplane: content check,
placement, total DRC); regenerate all previews; flip the Stage C ledger row to ✅;
expand nothing (Stage D is already at task depth).
*Acceptance:* four boards, four 0/0 DRC results, one command each.
**DONE (2026-07-18):** `check_revb_drc.py {mem,io,cpu,backplane} --total` = 0/0 ×4;
board connectivity + D1.18 completeness green; Stage C ledger flipped to ✅.

Then **Stage D (TD.12–TD.13)** as already specified: FreeCAD mating/keying with the
reversed-card collision proof → gerber fab packages + power re-check → **arms T1.10**.

### Stage C — replicate (order: io → cpu → backplane; D1.20)

**TD.9 — io card (the big one: D1.26 full-B3 wiring first).**
- TD.9.1 Extend `gen_revb_boards.py`: 8255 (DIP-40) + 8259-class PIC (DIP-28) +
  keyboard header, **fully wired, listed DNP** — pin tables from `hdl/juku_top.v`
  wiring + the facts file (PIC at 0x00/0x01, selects from the ATF16V8's
  PIC_CS_N/PPI_CS_N, INT_N open-drain out, IRQ_A/B + FRAME_TICK in). Completeness
  (D1.18) must hold including the new nets. Update `cards.json` populated/dnp.
- TD.9.2 Extend `revb_io_lvs.v`-style structural netlist + map (emitter grows an
  io instance table); `revb_lvs.sh io` IN SYNC; tier suite + CI.
- TD.9.3 Footprint probe (adds DIP-40, DIP-20 GAL16V8, DIP-14 osc) → PCB gen
  (`PLACE` table for io) → content check (generalize `check_revb_mem_pcb.py` →
  `check_revb_pcb.py --card`) → placement-clean → route → total-zero DRC → STEP.
*Acceptance:* same gates as mem, plus D1.26 wiring present-and-complete.

**TD.10 — cpu card.** Same pipeline; smallest board (Z80 + osc + diag header).
*Acceptance:* mem-equivalent gates.

**TD.11 — backplane.** No LVS (passive; the connector==pinout check already
covers all six slots). 100×100 outline, 6 slots at 19 mm pitch, USB-C/supervisor/
pulls/FTDI/jumper/LED placement; probe adds USB-C, SOT/TO-92 supervisor, switch,
2×2 jumper footprints. Route (power + slot parallels) → total-zero DRC → STEP.
*Acceptance:* mem-equivalent gates minus LVS.

### Stage D — assembly + exit

**TD.12 — FreeCAD mating/keying (D1.15).**
`kicad/revb/mate_check.py` under `freecadcmd`: load the four STEPs, seat the three
cards in slots at 19 mm pitch, boolean interference == 0; then a **deliberately
reversed card must collide** (keying proof). Committed `docs/rev-b-mating-report.md`
with measured clearances (card-to-card, tallest-part).
*Acceptance:* normal = no collision, reversed = collision, numbers in the report.

**TD.13 — CAD exit review → order gate.**
Tier suite + all TD/TE gates green; **power budget re-check** against the final
BOMs (bus-contract table); fab package per board (`kicad-cli pcb export gerbers` +
drill, zipped; pattern `export_fab.sh` + `package_rev_a_upload.py`) with SHA256s;
order-readiness note (rev A `order-readiness` pattern). **Arms T1.10** — ordering
becomes a purchasing decision, nothing else.
*Acceptance:* package hashes recorded; T1.10 unblocked.

At B1 exit (after the hardware tiers), expand Phase B2 to task level (rule 6).

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
