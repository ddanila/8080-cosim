# VJUGA workbench plan

Status: **PLAN / DIRECTION SET, BUILD PENDING CONFIRMATION**

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
   (D6 `.038`, provisional `~D0` correction) and `re3_prom` (D8 `.039`) — both
   reused verbatim from `hdl/devices.v` — so booting self-tests them. Byte-identical
   to the cosim oracle at 64 and 6000 video writes, with a decode-mismatch
   assertion guarding D6's decision against the reference map.
   - Rides on the main-twin's provisional D6 adoption (root `PLAN.md` item 1): if
     the level probe changes the D6 polarity call, this `~D0` correction updates
     with it. D8 РЕ3 had no blocker.
3. **Phase 3 — Rev-A physical board + digital-twin LVS.** Turn the byte-identical
   Verilog twin into the physical Rev-A fixture, keeping the twin and the PCB
   provably the same design.

   **Design decisions (fixed for Phase 3):**
   - **D6/D8 get real sockets, buffered by the GAL.** Add two DIP-16 sockets
     (К556РТ4 D6 decode, К155РЕ3 D8 pager) to Rev-A. Their outputs route
     **through the U5 GAL22V10**, not directly into the enables, so the
     provisional `~D0`/`~D3` polarity correction is a **GAL equation** —
     reprogrammable when the main-twin level probe resolves, no board respin.
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
   c. **LVS the twin against the board.** Map `vjuga_juku_top.v` instances to
      Rev-A refs (tv80→U1, ROM→U2, GAL→U5, ru5[0..7]→U10-U17, D6/D8→new refs,
      8255→U30) and extend `sync/check.sh` to compare the twin's netlist to
      `rev-a-physical.board.json`, replacing the old logical-blocks model one
      group at a time with LVS green after each swap (existing chip-map policy).
   d. Add the Mode-A (GAL-decode) path to the twin behind a parameter and prove
      **both modes boot byte-identical** to cosim, so each physical jumper
      setting has a simulated counterpart before fab.
   e. Update `docs/rev-a-power-budget.md` for the bipolar PROMs (~100-160 mA
      each when socketed) and re-check the fuse/regulator margins.
   f. Route/DRC/fab-package refresh through the existing `report_rev_a_*` gates,
      then independent schematic/copper/Gerber review. The board stays DESIGN
      HOLD until that review passes; only then is it an order candidate.

4. **Phase 4 — observability, assembly, and bench bring-up.**

   **Observability (design-in before fab):**
   - Keep J90-J93 debug headers; document a fixed **RP2350 24-channel map**
     (D0-D7, A0-A7, MREQ/IORQ/RD/WR/M1/RFSH, CLK, RESET_N) so captures are
     comparable across sessions. The analyzer's 5 V input mode hangs directly
     on the bus.
   - Add a **single-step clock jumper**: U50 oscillator vs external clock, so
     the Arduino UNO rig (5 V-native, 74HC165 chain reading the full bus) can
     drive the CPU statically. Sketch lives in `tools/` beside `rt4_dumper`.
   - **Framebuffer readback without video hardware:** the RP2350 captures all
     memory writes to `0xD800-0xFFFF` during boot; an offline script
     reassembles them into a 9640-byte framebuffer and `cmp`s against cosim's
     `vram.bin` — the bench twin of `sim/vjuga_boot_check.sh`. This makes the
     boot banner verifiable with zero display electronics (VGA stays deferred).

   **Assembly & bring-up ladder (each step gated by the previous):**
   a. Program + verify the GAL (test vectors from step 3d) and the 27C256
      (`ekta37_z80.bin`, checksummed).
   b. Assemble sockets/passives only; verify rails, fuse, and clamp with no ICs
      seated (PWR_OK LED).
   c. Oscillator + reset supervisor checks; then CPU free-run/NOP test (data
      bus forced to 0x00 via the debug header), watch address lines count on
      the analyzer.
   d. Mode A, western parts: ROM fetch → GAL decode → DRAM write/read →
      **banner via framebuffer readback** = board baseline PASS.
   e. Single-step rig session: UNO steps the first ~100 fetches; compare to the
      twin's trace (instruction-level cross-check).
   f. **Chip-test procedure (the workbench purpose):** swap ONE scarce part at
      a time into the proven baseline and re-run the banner readback —
      КМ4164→РУ5 bank first, then Mode B with the real D8, then the real D6.
      A byte-identical banner is that chip's PASS; log results per chip serial.
   g. **Bonus: VJUGA resolves the main-twin D6 question.** With the real D6
      booting in Mode B, probing D6.12/D8-enable levels at the reset fetch on
      VJUGA's own header answers the level-probe ask in root `PLAN.md` item 1 —
      the fixture becomes the instrument, no Juku board needed.

   **Exit criteria:** baseline board boots the banner in Mode A; each scarce
   chip class (РУ5, РТ4, РЕ3) has at least one part PASS in Mode B; the D6
   polarity observation is recorded and the provisional fit promoted or
   corrected in both twins.

## Per-chip pass/fail intent (bench)

| Part | Role on VJUGA | "Chip good" signal |
| --- | --- | --- |
| К565РУ5 DRAM | main RAM bank | boot RAM test passes; framebuffer matches cosim |
| D8 К155РЕ3 `.039` | ROM-select pager | correct ROM bank selects; boot proceeds |
| D6 К556РТ4 `.038` | memory-map decode | correct ROM/RAM overlay; boot proceeds (needs polarity resolution) |
| D2 К556РТ4 `.037` | WAIT/READY (optional) | correct wait-state timing on DRAM access |

## Done when

- **Simulation (phases 1-2): DONE.** The twin boots the real firmware on tv80
  through the real РУ5 + D6 РТ4 + D8 РЕ3 models, byte-identical to cosim
  (`sim/vjuga_boot_check.sh`).
- **Phase 3:** the Rev-A board sockets the scarce parts (dual-mode GAL decode),
  the twin LVS-matches `rev-a-physical.board.json`, both decode modes boot
  byte-identical in sim, and the fab package passes review (order candidate).
- **Phase 4:** the assembled baseline boots the banner in Mode A (verified by
  framebuffer readback); at least one РУ5, one РТ4, and one РЕ3 part PASS in
  Mode B; and the D6 level observation from the fixture promotes or corrects
  the provisional polarity fit in both twins.
