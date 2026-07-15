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

1. **Verilog twin core (POC + DRAM). IN PROGRESS — root-caused.** `tv80`
   (Verilog Z80) is vendored at `external/tv80`; `hdl/vjuga_juku_top.v` +
   `hdl/vjuga_juku_tb.v` build and **boot** `roms/ekta37_z80.bin` on it with RAM
   served by the real `dram_64kx1` (К565РУ5) reused from `hdl/devices.v`. The CPU
   executes correctly (writes `0x55` to VRAM in mode 0). `raw_row` permutation
   math is verified correct.

   **Root cause of the remaining framebuffer mismatch (probed 2026-07-15):** the
   RAS-time row latch inside `dram_64kx1` captures the *column* value, not the
   row — for a write to `0xD800`, `raw_row(0xD8)=0x74` is expected but the latched
   `row` reads `0x00/01/02` (= `acc_addr[7:0]`). So in the clocked sequencer the
   `negedge ras_n` effectively samples `dram_ma` after it has switched to the
   column, corrupting the RAM address (writes land at `d070/d1f0/...`).

   **Completion plan (the steps to fully done):**
   a. Dump a VCD of `ras_n`, `dram_ma`, and the instance's internal `row`; find
      the exact edge where the row latch samples the column (the `dram_64kx1`
      `#TSU` settle vs the clocked-NBA `dram_ma` update is the prime suspect).
   b. Restructure the sequencer so `dram_ma = row` is unambiguously stable across
      the RAS fall and only switches to the column a full settled step later —
      mirror the PROVEN `hdl/sim/dram_unit_tb.v` ordering (`ma=raw_row; ras↓;
      ma=col; we↓; cas↓`), which passes against `dram_64kx1`. Latching row/col
      into explicit sequencer registers and driving the РУ5 from those (rather
      than reusing one `dram_ma` for both phases) is the likely clean fix.
   c. Validate byte-identical vs `cosim` on `ekta37_z80` at 64 → 6000 video
      writes (the VHDL `juku_boot_top` standard), and confirm the BIOS RAM-test
      reads return correct data (value path, not just writes).
   d. Add `sim/vjuga_boot_check.sh` (build cosim ref, boot the Verilog twin,
      `cmp` framebuffers) and wire it into `sim/check.sh` as a PASS gate.

   Until (a)-(d) are green the VHDL `juku_boot_top` stays the byte-identical POC
   reference and this twin is not in any passing check.
2. **Fold in the real РЕ3 (D8) and РТ4 (D6) in the functional path (goal 3).**
   Route VJUGA's ROM-select / memory-map decode through `re3_prom` (D8 `.039`)
   and `decode_prom` (D6 `.038`) so booting exercises them.
   - **Dependency:** the physical D6 `.038` table's *contents* are confirmed to
     encode the correct map (it boots byte-identical in the main twin), but
     adoption is blocked on the D6 output-polarity/`D13->D37->D58` chain — a
     uniform complement does not work and the byte-correct per-output polarity
     contradicts measured `D6.12->D8` continuity (root `PLAN.md` Actionable
     item 1). VJUGA Phase 2 routes its decode through the same physical D6 РТ4,
     so it rides on that same polarity resolution; D8 РЕ3 has no such blocker.
   - D8 РЕ3 has no such dependency; it is already validated in the main boot and
     can be reused immediately.
3. **KiCad board half + LVS.** Extend the Rev-A physical model to socket the
   real РУ5 / РТ4 / РЕ3 (and the Z80), then bring up `sync/` LVS so the Verilog
   twin and the PCB agree — closing the digital-twin loop for the fixture.
4. **Observability (bench).** Bring out CPU control bus + data + low address to a
   debug header for:
   - the **Arduino UNO** single-step rig (UNO drives the clock, reads the full
     bus via 74HC165 shift registers — 5 V-native, no level shifting), and
   - the **RP2350 24-channel analyzer** (has onboard TXU-series level shifters +
     a 5 V input-select switch, so it hangs directly on the 5 V bus).
   Optionally a POST-style latch, but hardware address-watchpoints are the
   lower-risk first choice (see root discussion).

## Per-chip pass/fail intent (bench)

| Part | Role on VJUGA | "Chip good" signal |
| --- | --- | --- |
| К565РУ5 DRAM | main RAM bank | boot RAM test passes; framebuffer matches cosim |
| D8 К155РЕ3 `.039` | ROM-select pager | correct ROM bank selects; boot proceeds |
| D6 К556РТ4 `.038` | memory-map decode | correct ROM/RAM overlay; boot proceeds (needs polarity resolution) |
| D2 К556РТ4 `.037` | WAIT/READY (optional) | correct wait-state timing on DRAM access |

## Done when

Each goal has a green check reusing the real part: DRAM bank + D8 РЕ3 (+ D6 РТ4)
boot the twin identically to cosim; the KiCad board LVS-matches the twin; and the
bench observability path is wired for UNO + analyzer bring-up.
