# VJUGA workbench plan

Status: **REV-A SOFTWARE/BOARD MODEL ACTIVE / HARDWARE AND RELEASE REVIEW PENDING**

VJUGA is repurposed from "minimal VGA board" into a **bench fixture for the
scarce original Juku parts**. The single-+5 V Z80 board is the simplest rig that
can exercise those chips in their real functional roles; **booting the Juku
firmware is the self-test** — a bad socketed chip makes the boot fail in an
observable way.

## Goals (this effort)

1. **POC** — prove the minimal single-supply Z80 board actually runs the Juku
   firmware. (Digital half already done: `hdl/juku_boot_top.vhd` boots
   `roms/ekta37_z80.bin` and matches the cosim oracle — see `../README.md`.)
2. **Test DRAM chips** — socket and exercise the К565РУ5 (4164-class) parts.
3. **Test the bipolar PROMs** — use the **actual original Juku** РТ4 / РЕ3 chips
   in their functional roles: D6 `.038` (К556РТ4 memory-map decode), D8 `.039`
   (К155РЕ3 ROM pager). D2 `.037` (РТ4 WAIT/READY) optional.

Explicitly **out of scope**: FDC (D93/D94/support — overcomplicates the bench),
and — for this round — the VGA display path (original release-gate item 3 is
deferred; it is not needed for POC / DRAM / PROM testing).

## Design principles (carried from the main recreation)

- **Digital twin.** A simulatable HDL model and a KiCad PCB model of the *same*
  board, cross-checked by an LVS-style connectivity comparison — exactly the
  `sync/` discipline of the root project.
- **Reuse Juku parts.** Do not re-model chips VJUGA shares with the Juku. Reuse
  the validated device models from `../../hdl/devices.v` verbatim, loaded with
  the validated physical dumps:
  - `dram_64kx1` — К565РУ5 DRAM bit-slice (goal 2)
  - `re3_prom` — К155РЕ3, loads `d8_039.raw.hex` (goal 3, D8 pager)
  - `decode_prom` — К556РТ4, loads `d6_038` (goal 3, D6 decode)
  - `wait_prom_037` — К556РТ4, loads `d2_037` (optional, D2 WAIT/READY)
- **cosim is the oracle.** Validate by comparing memory-read/framebuffer output
  against the C emulator, as `sync/cosim_check.sh` / `sync/boot_check.sh` do.

## Architecture decision (recommended)

The reusable chip models are **Verilog** (`hdl/devices.v`); the current VJUGA top
is **VHDL** (T80/GHDL), and no free simulator mixes the two cleanly. Chosen
direction (best honors "reuse parts" + "same approach"):

> **Build the VJUGA twin in Verilog.** Use the Verilog Z80 core **tv80** (the
> Verilog sibling of T80, so the physical board is unchanged — still a real Z80)
> and instantiate the real РУ5 / РТ4 / РЕ3 models straight from `hdl/devices.v`.
> Run it on the same **iverilog + cosim value-level guard + LVS** flow as the
> recreation. The existing `hdl/juku_boot_top.vhd` (VHDL) is kept as the
> proof-of-concept reference; the Verilog twin becomes the maintained model.

Rejected alternative: port the chip models to VHDL and keep GHDL — that creates a
second copy of each chip model (drift risk vs `hdl/devices.v`) and forfeits the
direct cosim-vs-C reuse. Less reuse, weaker single-source-of-truth.

*(This was put to the owner; proceed on this recommendation unless redirected.)*

## Phased build

1. **Verilog twin core (POC + DRAM). DONE.** `tv80` (Verilog Z80) is vendored at
   `external/tv80`; `hdl/vjuga_juku_top.v` boots `roms/ekta37_z80.bin` on it with
   RAM served by the real `dram_64kx1` (К565РУ5) reused verbatim from
   `hdl/devices.v`, and the framebuffer is **byte-for-byte identical to the cosim
   oracle** at 64 and the full 6000-write banner. `sim/vjuga_boot_check.sh`
   gates this and is wired into `sim/check.sh` (PASS, ~9 s). This exercises the
   real DRAM part model (goal 2) and boots the real ROM on a real Z80 (goal 1);
   the byte-identical banner also validates the RAM read path (the BIOS RAM test
   reads back its writes).

   The bug found on the way (recorded for reference): a blanket
   `dram_ras_n <= 1'b1` default plus a per-state override made iverilog emit a
   spurious RAS transition that re-latched `dram_64kx1`'s row from the column.
   Fixed by driving RAS/CAS/WE explicitly per sequencer state (one clean edge
   each), mirroring the proven `hdl/sim/dram_unit_tb.v` drive ordering.
2. **Fold in the real РЕ3 (D8) and РТ4 (D6) in the functional path (goal 3). DONE.**
   `hdl/vjuga_juku_top.v` now routes the ROM/RAM decode through `decode_prom`
   (D6 `.038`, corrected active-low D0/`ROM_N`) and `re3_prom` (D8 `.039`) — both
   reused verbatim from `hdl/devices.v` — so booting self-tests them. Byte-identical
   to the cosim oracle at 64 and 6000 video writes, with a decode-mismatch
   assertion guarding D6's decision against the reference map.
   - Corrected reader-3 packing and direct continuity close D6's output order;
     Mode B inverts active-low `ROM_N` only when deriving the internal boolean
     `is_rom`. D8 РЕ3 had no blocker.
3. **Phase 3 — Rev-A physical board + digital-twin LVS.** Turn the byte-identical
   Verilog twin into the physical Rev-A fixture, keeping the twin and the PCB
   provably the same design.

   **Progress:** steps (a) board model + socket contract, (b) dual-mode GAL
   equations + test vectors, (d) both decode modes boot byte-identical, and
   (e) power budget are **DONE**. Step (c) — the physical-board socket↔twin
   contract is enforced by `check_rev_a_physical`; the independently
   authored physical-LVS stages now close the POWER/CLOCK_RESET, complete
   decode socket/glue, complete Z80/ROM core, complete eight-chip DRAM bank,
   and complete address-mux groups with exact endpoint projections. U22's
   74HCT393 halves are now physically cascaded and its active-high resets are
   grounded; complete-instance refresh-counter LVS remains staged (see below).
   Step (f) routing/DRC is **DONE** on the current 119-ref board; fab
   regeneration and review remain.

   **Design decisions (fixed for Phase 3):**
   - **D6/D8 get real sockets, buffered by the GAL.** Add two DIP-16 sockets
     (К556РТ4 D6 decode, К155РЕ3 D8 pager) to Rev-A. Their outputs route
     **through the U5 GAL22V10**, not directly into the enables, so the
     corrected active-low D0/`ROM_N` polarity is a **GAL equation**
     (`ROM_B=/DEC_ROM_N`), with no board respin.
   - **Dual decode mode via jumper.** Mode A (bring-up): the GAL decodes
     ROM/RAM internally (current draft equations) with the PROM sockets empty —
     the board is fully testable with western parts only. Mode B (chip test):
     the GAL passes/conditions the real D6/D8 outputs — booting then exercises
     the scarce chips. One jumper (GAL input pin) selects the mode.
   - **DRAM sockets unchanged.** U10-U17 are 4164-class DIP-16, and К565РУ5 is
     pin-compatible (pin 1 NC on a populated РУ5). KM4164B-10 is the western
     baseline; РУ5 parts are inserted only for the chip test.
   - **ROM stays 27C256** carrying the `ekta37_z80` image (16 KiB used). Testing
     original D15/D16 EPROMs is out of Rev-A scope.
   - **Baseline-first policy.** Every bring-up step is proven with western parts
     (Mode A) before any scarce chip is socketed.

   **Steps:**
   a. Extend `kicad/rev-a-physical.board.json` + `docs/rev-a-chip-map.md`: D6/D8
      sockets, mode jumper, GAL pin reassignment, PROM pull-ups; regenerate the
      schematic; keep `check_rev_a_physical` green at each step.
   b. Update `docs/rev-a-gal-equations.md` for both modes and add the polarity
      terms; derive GAL test vectors from the twin so the equations are
      simulated, not just written (release-gate item 4).
   c. **LVS the twin against the board.** DONE for the new decode group: the
      РТ4/РЕ3 socket wiring (addressing, enables, outputs-into-GAL, Port C mode
      bits) is enforced against the twin's decode semantics by the
      `DECODE_SOCKET_CONTRACT` in `check_rev_a_physical.py`. STAGE 1 DONE:
      `sync/rev_a_power_clock_reset_lvs.sh` independently compares all POWER
      and CLOCK_RESET placement refs, J93, and the U1 power/clock/reset boundary
      against `rev-a-physical.board.json` (17 refs / 9 partitions), including
      power rails; moving J3.A9 to GND in a temporary model must fail. STAGE 2
      DONE: `sync/rev_a_decode_lvs.sh` independently closes all 22 decode
      socket/glue parts and every non-power endpoint they touch (28 mapped refs /
      37 partitions / 5 NC pads); an RT4 output miswire and a missing inverter
      NC declaration must both fail. STAGE 3 DONE:
      `sync/rev_a_cpu_rom_lvs.sh` maps every U1 Z80 and U2 ROM pin plus C1/C2,
      and every endpoint on their 36 non-power nets (35 mapped refs / 38
      partitions / 2 NC pads); address-swap, missing-NC, and open-scope
      mutations must fail. STAGE 4 DONE:
      `sync/rev_a_dram_bank_lvs.sh` maps every U10-U17/C6-C13 pad and every
      endpoint on all 19 non-power bank nets (25 mapped refs / 21 partitions /
      8 NC pads); data-pin, missing-NC, and open-scope mutations must fail.
      STAGE 5 DONE: `sync/rev_a_dram_mux_lvs.sh` maps every U20/U21/C14/C15
      pad and every endpoint on all 25 non-power mux nets (19 mapped refs / 27
      partitions); input, output, grounded-enable, and open-scope mutations
      must fail. STAGED:
      full chip-accurate yosys LVS of the *whole* board — mapping the tv80 core
      and the behavioral DRAM sequencer and replacing the old 8-instance logical
      model group-by-group — remains a larger effort. Exact coverage and the
      remaining groups are recorded in `docs/rev-a-lvs-coverage.md`.
      Whole-board LVS is a bare-board release gate unless the owner records a
      specific waiver backed by independent schematic, pinout, and copper
      review; the five physical stages must not silently stand in for it.
   d. Add the Mode-A (GAL-decode) path to the twin behind a parameter and prove
      **both modes boot byte-identical** to cosim, so each physical jumper
      setting has a simulated counterpart before fab.
   e. Update `docs/rev-a-power-budget.md` for the bipolar PROMs (~100-160 mA
      each when socketed) and re-check the fuse/regulator margins.
   f. Route/DRC/fab-package refresh through the existing `report_rev_a_*` gates,
      then independent schematic/copper/Gerber review. The board stays DESIGN
      HOLD until that review passes; only then is it an order candidate.

4. **Phase 4 — observability, assembly, and bench bring-up.** Detailed plan:
   **`phase4-bench-bringup.md`**. **Software + board-model half DONE** (design-ins
   J96/J97/J98, framebuffer-readback oracle validated vs twin + cosim,
   single-step sketch + twin reference trace); the physical ladder is pending the
   fabricated board (Phase 3 step f). In brief:
   - **Design-ins before the step (f) copper freeze** (found by auditing the
     board model): J96 clock-control jumper (`OSC_OE_N`→GND tri-states U50 so
     the UNO can drive `CLK`), J97 high-address header (A8-A15 + `MEM_WR_N` are
     currently on NO header), J98 control-bus header (MREQ/IORQ/RD/WR/M1/RFSH/
     WAIT), and a documented NOP-plug free-run provision (no copper needed).
   - **Two fixed RP2350 24-channel capture profiles**: Profile FB (A0-A15 +
     D0-D7, clocked by `MEM_WR_N` — exactly 24 channels) for framebuffer
     readback, Profile CTL for single-step/decode debug.
   - **Framebuffer readback = the bench boot oracle**: capture boot writes,
     reassemble `0xD800`+9640 bytes, `cmp` vs cosim — banner verified with zero
     display electronics. The readback tool is validated *against the twin*
     (twin emits the same capture format) before any hardware exists.
   - **Arduino UNO single-step rig**: J96 + 4×74HC165 chain; per-M1-fetch trace
     diffed against a twin-generated reference trace.
   - **Bring-up ladder** (a-h): GAL/ROM programming → rails → clock/reset →
     free-run NOP → Mode A baseline banner → single-step diff → one-scarce-
     chip-at-a-time PASS logging (РУ5 → РЕ3 observed → РТ4 driving in Mode B),
     with per-chip failure signatures and a `bench-log.md` per-serial record.
   - **D6 polarity guard on VJUGA itself:** probe J95.1 (`DEC_ROM_N` = D6.12)
     at reset in Mode B; it must read low while ROM is selected, matching the
     corrected reader-3 capture and direct factory/continuity evidence.

   **Exit criteria:** baseline board boots the banner in Mode A (proven by
   readback); each scarce chip class (РУ5, РТ4, РЕ3) has at least one part
   PASS in its functional role; the D6 active-low observation is recorded and
   agrees with both twins.

## Per-chip pass/fail intent (bench)

| Part | Role on VJUGA | "Chip good" signal |
| --- | --- | --- |
| К565РУ5 DRAM | main RAM bank | boot RAM test passes; framebuffer matches cosim |
| D8 К155РЕ3 `.039` | ROM-select pager | correct ROM bank selects; boot proceeds |
| D6 К556РТ4 `.038` | memory-map decode | corrected active-low D0/`ROM_N` level observed; correct ROM/RAM overlay and boot |
| D2 К556РТ4 `.037` | WAIT/READY (optional) | correct wait-state timing on DRAM access |

## Done when

- **Simulation (phases 1-2): DONE.** The twin boots the real firmware on tv80
  through the real РУ5 + D6 РТ4 + D8 РЕ3 models, byte-identical to cosim
  (`sim/vjuga_boot_check.sh`).
- **Phase 3:** the Rev-A board sockets the scarce parts (dual-mode GAL decode),
  the twin LVS-matches `rev-a-physical.board.json` (or an explicit owner waiver
  carries equivalent independent review), both decode modes boot byte-identical
  in sim, and a fresh fab package passes review (order candidate).
- **Phase 4:** the assembled baseline boots the banner in Mode A (verified by
  framebuffer readback); at least one РУ5, one РТ4, and one РЕ3 part PASS in
  Mode B; and the D6 level observation from the fixture promotes or corrects
  the corrected active-low polarity in both twins.
