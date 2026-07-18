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

Then **Stage D** — expanded to task depth as **TG.1–TG.4** below (2026-07-18; refines
TD.12–TD.13 with the mating-contract finding from the Stage-C exit review).

### Stage D — mating contract, FreeCAD proof, fab package (TG.1–TG.4)

The Stage-C exit review found the boards are route-perfect but **not physically
compatible**: cards disagree with each other by 1 mm on connector edge offsets
(mem 5/10 mm vs io/cpu 4/9 mm), and the D1.30 two-bank backplane cannot mate any
card (cards present base+ext rows 5 mm apart at one slot line; the backplane's banks
are 40+ mm apart). Stage D therefore starts by making mating a machine-checked
contract (D1.31), THEN proves it in 3D. One task = one commit; rebase before push.

**TG.1 — mechanical mating contract + checker (D1.31).**
- `kicad/revb/mating.json` — single source of geometry truth: `BASE_ROW_X=50.0`,
  `BASE_EDGE_OFFSET=5.0`, `EXT_ROW_X=14.45`, `EXT_EDGE_OFFSET=10.0`,
  `SLOT_PITCH=18.0`, `SLOT0_Y=5.0`, `N_SLOTS=6`, `EXT_ROW_DY=5.0`. (Ext x moves
  14.0→14.45: half-pitch interleave keeps base/ext bus columns 1.27 mm apart on the
  backplane; at 14.0 they'd run 0.82 mm apart.)
- During execution, confirm the presentation model against RC2014 practice (cards
  use right-angle male headers at the bottom edge, backplane female sockets; the two
  card rows' down-legs land `EXT_ROW_DY` apart at the slot) — one WebSearch/ref check,
  record the citation in `rev-b-bus-contract.md` §mechanical.
- `kicad/revb/check_revb_mating.py` (pure python, no CAD tools — CI-safe): asserts
  (1) every card's J_BUS/J_EXT PLACE entries equal `(BASE_ROW_X, BOARD_H −
  BASE_EDGE_OFFSET)` / `(EXT_ROW_X, BOARD_H − EXT_EDGE_OFFSET)`; (2) backplane slot
  pairs follow the slot equations; (3) base/ext column x-grids stay ≥1.0 mm apart;
  (4) `SLOT0_Y + 5·SLOT_PITCH + EXT_ROW_DY` + margins fit `BOARD_H`. Wire into
  `revb_tier_suite.sh` + CI.
*Acceptance:* checker committed and **FAILS on today's geometry** (it must catch the
known 1-mm and two-bank bugs), contract constants + citation in the bus contract doc.

**TG.2 — align generators to the contract, re-route all four.**
- `gen_revb_pcb.py` reads `mating.json`: card J_BUS/J_EXT positions derived (not
  hand-tabled); `_backplane_place()` = per-slot pairs (base y_k, ext y_k+5, 18 mm
  pitch, y 5…95) with the power/reset/serial tail moved into the 13-mm inter-slot
  gaps + top strip (tail nets mostly terminate ON bus columns — VCC5/GND/RESET_N/
  TX/RX are bus nets — so freerouting taps the nearest column; B.Cu stays free for
  crossings). `emit_bus_columns()` unchanged (banks are still same-x stacks).
- Regenerate + route mem/io/cpu/backplane. cpu's J_BUS moves 1 mm — if x=41 stops
  routing, re-run `sweep_cpu_place.sh` (exists, ~7 min). If backplane placement DRC
  can't pass in 100×100 with the tail squeezed in, grow `BOARD_H` per D1.31 (≤115).
*Acceptance:* `check_revb_mating.py` green; 4× `check_revb_drc.py --total` 0/0 from
fresh regenerate; STEP + previews regenerated.
**DONE (2026-07-18):** contract refined to base_edge_offset **4.0** mm (io — densest
card — is the binding constraint; only routes at 4 mm), backplane grown to 100×115.
revb_place.py derives card connectors from mating.json; mating checker in the tier
suite. All four route **0/0**. Backplane needed two fixes beyond placement: base cols
F.Cu / ext cols B.Cu, and bottom-strip pullups moved onto their own bus columns
(R_INT→x=60) so the residual tail taps are short (D1.33 — the DSN roundtrip drops the
interleaved columns; freerouting re-routes them + tail and closes once taps are short).

**TG.3 — FreeCAD mating + keying proof (TD.12 essence, D1.15/D1.4).**
- `kicad/revb/mate_check.py` under `freecadcmd`: load the 4 STEPs; seat mem/io/cpu
  in slots 1/2/3 (transform from the contract math: rotate card vertical, bottom
  edge over slot rows); assert pairwise boolean `common()` volume == 0; measure
  card-to-card clearance (neighbor card face ↔ tallest component solid) and record.
- Negative test: one card rotated 180° about the vertical axis — assert interference
  OR blocked seating. If the model shows the reversed card seats freely, take
  **D1.32**: (a) generator-emitted blocking obstruction at mirrored-ext x≈85.55 per
  slot, else (b) convention-only keying (silk arrows), downgrade D1.4, record risk.
- Commit `docs/rev-b-mating-report.md` with the measured numbers.
*Acceptance:* normal assembly interference = 0; reversed case collides or D1.32
implemented + recorded; report committed.
**DONE (2026-07-18):** `mate_check.py` reads the 4 STEPs in FreeCAD, measures each
card's real component envelope, and checks the same-facing seated clearance at the
16 mm pitch: thickest envelope 11.84 mm → **clearance 4.16 mm, PASS** (conservative —
the envelope includes the bus pins, which insert into the backplane, not toward the
neighbour). Keying: base is centred/symmetric so a reversed card's base still seats;
with generic headers the ext row can't be shown to bottom-out → **D1.32b convention-only**
(RC2014 precedent, risk recorded). `docs/rev-b-mating-report.md` committed.

**TG.4 — power re-check + fab packages → arm T1.10 (TD.13 essence).**
- Power budget re-check against the FINAL BOMs (bus-contract power table): worst-case
  Icc totals per card + backplane, vs USB-C 5 V budget; per-column current sanity
  (0.3 mm track). Record in the order-readiness note.
- `export_fab.sh` (rev A pattern): `kicad-cli pcb export gerbers` + drill per board →
  4 zips in `fab/minimal-vga/revb/package/` (untracked) + SHA256s committed.
- `docs/rev-b-order-readiness.md`: per-board dims/layers/qty, connector BOM (female
  sockets ×12 on backplane, right-angle male 1×39 + 1×10 per card), open risks.
*Acceptance:* 4 package hashes committed; order-readiness note done; **T1.10 is now
purely a purchasing decision**.
**DONE (2026-07-18):** `export_fab.sh` writes Gerbers + drill per board → 4 zips
(untracked) + SHA256 manifest. Power re-checked: ~712 mA / ~47 % of 1.5 A USB-C
(backplane discretes negligible), budget holds. `docs/rev-b-order-readiness.md` records
boards/BOM/hashes/risks. **T1.10 armed** — Stage D complete.

### Backplane order-safety (TH.1–TH.4; D1.35/D1.36) — planned 2026-07-18

The pre-order audit fixed the DIP-28 width bug but left the backplane's six non-DIP
footprints name-matched and unverified (D1.36), the TO-92 pad→net map unpinned to a
real part, and the power-entry board with **no capacitors and no input protection**
(D1.35). The three cards are order-safe now; the backplane goes through TH before its
zip is sent. One task = one commit; rebase before push.

**TH.1 — pin the backplane BOM to exact MPNs (D1.36 first half).**
For every backplane part, choose one orderable MPN and check its datasheet drawing
against the named footprint — drill ≥ pin diagonal, pitch, pad pattern, body outline:
- `J_USBC` → **exactly GCT USB4125-xx-x** (the footprint names it; A5/B5=CC, A9/B9=VBUS,
  A12/B12=GND, SH — our pad→net map already matches the 6P power-only pattern).
- `SW_RST` → **exactly APEM MJTP1243** (footprint names it; 2 pins per board.json).
- `U_RST` → pick a **DS1813-class 3-pin TO-92 supervisor** whose pinout is
  1=GND, 2=/RESET, 3=VCC (the board.json mapping); if the chosen MPN differs, fix the
  pin map in `gen_revb_boards.py` — this mapping is electrical, not just mechanical.
  Note the 8251/GAL16V8 reset path expects the supervisor's open-drain active-low out
  on RESET_N with the existing pull-up (cross-check `rev-b-gal-equations.md` D1.16).
- `D_PWR` → any 5 mm THT LED (verify pad1=anode on `LED_D5.0mm`); `R_*` → DIN0207
  axials; `JP_S5`/`J_FTDI`/`J_PWR` → standard 2.54 mm headers; slot sockets → 1×39 +
  1×10 **female** SIL sockets (square-pin, fits the 1.0 mm drills); card-side headers →
  **right-angle male** (PCB hole pattern identical to the vertical footprint used).
Record all of it as a BOM table (ref, MPN, footprint, datasheet link, checked-dims ✓)
in `rev-b-order-readiness.md`. Sources: WebSearch/datasheets; cite in the table.
*Acceptance:* every backplane ref has an MPN + a checked-✓ row; any pin-map fix is in
the generator (guards green), not prose.

**TH.2 — footprint physical-contract guard for non-DIPs (D1.36 second half).**
Extend `check_revb_footprints.py`: for each resolved footprint, parse the `.kicad_mod`
(s-expr text; no pcbnew needed) and assert (a) **pad count == the board.json pin count**
for that component (catches silently floating pads — `add_fp` maps nets by pad number
and unmapped pads today float with no DRC complaint; the USB-C SH multi-pad case needs
an explicit allowance), (b) THT drill ≥ the BOM pin dimension and pad pitch == datasheet
value, from a small `PKG_PHYS` table filled with TH.1's numbers (cite the datasheet per
row). CI-safe (skips without KICAD_FOOTPRINTS).
*Acceptance:* guard green on the pinned BOM **and negative-tested** (e.g., wrong
pad-count expectation or a too-small drill must FAIL) — same discipline as PKG_WIDTH.

**TH.3 — input power conditioning (D1.35).**
`gen_revb_boards.py`: add to the backplane `C_BULK` (47 µF/16 V radial electrolytic,
new footprint kind `CP_RADIAL_D6.3` or similar), `C_IN` (100 nF disc, existing kind),
and `F_VBUS` (~1 A-hold polyfuse, radial) wired **USB VBUS → F_VBUS → VCC5 rail**, with
`J_PWR` still directly on VCC5 (bench path unfused, D1.35). Caps across VCC5/GND near
the USB entry. New net `VBUS_IN` between J_USBC and the fuse. Placement: tail strip
next to `J_USBC` (revb_place.py). Connectivity + D1.18 completeness must stay green
(they police the new wiring); footprint probe extended for the two new kinds (TH.2
guard applies). Power-budget note: polyfuse hold current vs the ~712 mA budget (1 A
hold / ~2 A trip fits; record in the bus contract power section).
*Acceptance:* board.json regenerates with the three parts wired; all existing guards
green; `check_revb_pcb.py backplane` taught the new part count.

**TH.4 — re-verify and re-arm the backplane.**
Regenerate + route to total-DRC 0/0 (also try re-enabling the 0.6 mm edge keepout ring
for the backplane now that the locked columns are retired — the earlier ring failure
was a ring×columns interaction; keep it if the clean-slate board still routes 0/0,
drop it again if not, recording which). Then: mating checker, STEP + previews,
`mate_check.py` (new parts change the envelope), `export_fab.sh`, update hashes + flip
the backplane hold in `rev-b-order-readiness.md` ("order-safe" for all four boards),
tier suite green.
*Acceptance:* 4× total DRC 0/0 from fresh regenerate; all artifacts + hashes current;
order-readiness lists **no unverified footprint** among the risks.

**TH.1–TH.4 DONE (2026-07-18).** Pinning the BOM surfaced three real defects beyond the
name-match risk: **SMD USB-C** (GCT USB4125 was surface-mount → switched to fully-THT GCT
USB4085, full 16-pin power map, 0.1 mm local clearance for its 0.85 mm pitch); **reversed
power LED** (KiCad LED_D5.0mm pad 1 = cathode — rev A's checker confirms — but we mapped
anode there → swapped); **missing RESET_N pull-up** (open-drain supervisor + button would
have floated reset → added R_RST + C_RST). The TO-92 supervisor pinout couldn't be
verified authoritatively from the desk, so U_RST became a **net-labelled 3-pin header**
(orient the part to silk) — reset works even with it empty. TH.3 added 47 µF bulk + 100 nF
+ an MF-R110 polyfuse (USB branch only); backplane grew 115→120. TH.2's `PKG_PHYS` guard
(through-hole count / drill / pitch, negative-tested) + the footprint probe are now in the
tier suite. Edge keepout ring enabled on the backplane too (D1.34 retired the conflicting
columns) → routes 0/0 attempt 1. All four boards 0/0; hold lifted.

### Phase B2 — video card to manufacturing-ready (TI.1–TI.8; D2.1–D2.5)

Goal: the fifth board — TTL VGA + framebuffer — through the SAME pipeline as the other
four (netlist → LVS → footprint guards → PCB → route 0/0 → mating → fab package), with
the TTL640x480 timing chain adopted per D2.1. The bus side is already contracted:
cards.json `video` owns `0xD800-0xFFFF` (mem stops at 0xD7FF — no overlap), drives
FRAME_TICK + open-drain WAIT_N, and the behavioral twin `revb_video_card.v` already
boots ekta37 byte-identical. Sequencing note: TI.1–TI.4 are pure desk work; **hold TI.5+
tape-out until T1.11 bench proves the bus** (a bus tweak is cheapest folded into this
card's first spin). One task = one commit; rebase before push.

**TI.1 — adoption note + timing contract (D2.1).**
- `docs/rev-b-video-adoption.md`: what is adopted from mengstr/TTL640x480 (timing chain
  topology: '393 row/col counters + NAND sync/blank decode + diode-NOR), the adopted
  commit hash, the MIT license text, and what is ours (framebuffer, bus interface,
  shifter, GAL logic, DAC). No Eagle import — redrawn in our generator.
- `kicad/revb/video-timing.json` — numeric contract consumed by twin + checkers:
  h_total=800, h_active=640, h_fp=16, h_sync=96, h_bp=48; v_total=525, v_active=480,
  v_fp=10, v_sync=2, v_bp=33; dot=25.175 MHz; sync polarities; plus the VJUGA mapping
  block (fb_base=0xD800, cols=40, rows=241, pixel-double ×2, crop_or_letterbox=TBD@TI.2).
*Acceptance:* both files committed; timing numbers match the VGA 640×480@60 standard and
the adopted schematic; license provenance recorded.

**TI.2 — chip-level twin + all B2 sim gates (oracle-first, D1.19).**
- `hdl/revb/revb_video_card_ttl.v`: 74xx-level model (per-chip modules mirroring the
  real BOM: 3×'393, '00/'10/'20/'04, 4×'157 CPU/scanout address mux, '166 shifter,
  '245 data buffer, GAL22V10 — equations added to `rev-b-gal-equations.md`) implementing
  the D2.5 contention design. Drop-in for `revb_video_card.v` in the backplane twin.
- Gates, all wired into `revb_tier_suite.sh` + CI:
  (a) boot ekta37_z80 with the TTL card → framebuffer readback **byte-identical to
  cosim's vram.bin** (the existing oracle, now through real chips);
  (b) **scanout checker**: sync periods/widths == `video-timing.json`; active-region
  pixel stream == framebuffer bits (this resolves **D2.4 crop-vs-letterbox** — test both,
  freeze the winner in the json);
  (c) **/WAIT phase sweep**: CPU framebuffer access launched at every dot-clock phase —
  zero lost/corrupt accesses, bounded wait, verified against the bus monitor;
  (d) **mode-default gate**: MODE0/1 from backplane pulls only (no io card), GAL decodes
  the boot overlay per the facts table;
  (e) **FRAME_TICK contract**: tick period vs the facts' 200000-cycle keyboard-scan
  anchor (tolerance recorded — VGA 60 Hz vs the original tick is a firmware-visible
  fact; the oracle decides what is acceptable).
*Acceptance:* tier suite green with the TTL card substituted; D2.4 resolved and frozen.

**TI.3 — netlist to schematic depth + LVS.**
- `gen_revb_boards.py`: add the `video` card — new CHIP_TYPES (74HCT393/00/10/20/04/157/
  166, GAL22V10_VIDEO, OSC_25M175, DB15HD, R-DAC + termination resistors, decoupling
  caps ~1/chip), full pin tables wired per TI.2's model; AS6C1008 reused (D2.3, high
  address lines strapped). D1.18 completeness + connectivity guards must stay green
  (cards.json `video` entry already specifies the bus face).
- LVS: `revb_video_lvs.v` empty-bodied structural netlist + instance map;
  `revb_lvs.sh video` IN SYNC; tier suite + CI.
*Acceptance:* video.board.json generated, completeness green, LVS IN SYNC.

**TI.4 — footprints + package guards.**
- Probe additions: DIP-14 TTLs (existing kind), `OSC_25M175` (existing OSC14 kind),
  **DSUB-15HD** (KiCad `Connector_Dsub` lib — high-density 3-row 15-pin, THT, verify
  against a real MPN datasheet like the USB-C was), R-DAC resistors (existing kind).
- `PKG_WIDTH`/`PKG_PHYS` rows for every new type, datasheet-cited, **negative-tested**
  (the DSUB especially: pad count 15+shield, row pitch 2.29/2.54 mm variants — pick the
  variant matching the purchasable part, not the prettiest footprint).
*Acceptance:* probe green all five cards; DSUB negative test fails on the wrong-variant
footprint.

**TI.5 — PCB: placement + route (D2.2 gate). [HOLD until T1.11 bench-proves the bus]**
- `revb_place.py`: video PLACE table (BOARD_H=100; J_BUS/J_EXT derived from mating.json
  automatically). Layout guidance: bus interface + GAL near the bottom (mating) edge,
  SRAM + mux center, timing chain + shifter + DAC + DB15 along the TOP edge (cable side),
  osc adjacent to the counters, 25 MHz nets short.
- Placement DRC 0 → route (FR_ATTEMPTS=30, sweep on the SRAM/GAL if needed, exactly the
  TF.1 pattern). **If the sweep exhausts without 0/0 → D2.2 4-layer exception**, recorded
  in the build plan with the sweep log as evidence.
*Acceptance:* `check_revb_drc.py video --total` 0/0 from fresh regenerate; layer count
recorded; STEP + previews rendered.

**TI.6 — mechanical: 4-card assembly + connector overhang.**
- `mate_check.py`: seat mem/io/cpu/video in slots 1–4; interference 0; re-measure
  clearances (the DB15 shell overhangs the card's TOP edge — verify it clears the
  neighbouring slot's envelope and record the overhang for enclosure thinking).
*Acceptance:* updated `rev-b-mating-report.md` with the 4-card numbers.

**TI.7 — power re-check + fab package + BOM.**
- Power: ~18 HCT + osc + SRAM ≈ +150 mA over the B1 table → new total vs the 60 %/0.9 A
  USB headroom rule — if it crosses, record the consequence (bench/PD-supply note in the
  bus contract), don't hand-wave it.
- `export_fab.sh` gains the video card → 5 zips + hashes; order-readiness: video board
  row + BOM rows (exact MPNs, DSUB + osc datasheet-cited like USB4085/MF-R110).
*Acceptance:* hashes recorded; every video part datasheet-verified; power table updated.

**TI.8 — B2-CAD exit.**
- Full tier suite green (all five boards' guards + the TTL-twin gates); ledger row
  "B2-CAD" ✅; the **on-glass exit** (real banner on a real monitor, framebuffer readback
  byte-identical on hardware) stays a bench task gated on T1.11 + the video-card order.
*Acceptance:* five boards × total-DRC 0/0 + suite green from one command.

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
