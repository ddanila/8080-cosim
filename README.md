# 8080-cosim

Experiment: model an Intel 8080–based computer as **both** a physical PCB and a
runnable digital simulation, and keep the two models provably in sync — without a
GUI in the loop, so the whole thing can be driven by an LLM.

## Board previews

The recreated ДГШ5.109.006 processor board (auto-routed 2-layer, 310×266 mm), regenerated
from `kicad/juku_routed.kicad_pcb` by `kicad/render_views.sh`. A repo pre-commit hook
(`.githooks/pre-commit`; enable once with `git config core.hooksPath .githooks`) refreshes
these whenever the routed board is committed, so they never go stale.

| 3D | 2D |
|---|---|
| ![3D top](renders/board_3d_top.png) | ![component side](renders/board_2d_front.png) |
| ![3D perspective](renders/board_3d_persp.png) | ![solder side](renders/board_2d_back.png) |


## Goal

1. **PCB** — schematic + board for an 8080 system (CPU + ROM + RAM + glue +
   peripherals + keyboard) in KiCad.
2. **Simulation** — a headless, scriptable model of the same machine that can:
   - load a ROM image,
   - clock the CPU,
   - inject keystrokes,
   - let us read **video RAM** to confirm something was printed,
   - feed commands and observe the machine react.
3. **Sync glue** — automated checking that the PCB and the simulation describe
   the *same* circuit (connectivity equivalence, a.k.a. LVS), so the two models
   can't silently drift apart.

## Approach (see `docs/architecture.md` for the full reasoning)

- **PCB:** KiCad. Source of truth for connectivity. ERC/DRC here.
- **HDL:** structural + behavioral Verilog mirroring the schematic
  (open-source 8080 core, ROM/RAM/VRAM, address decoder, 8255-style keyboard port).
- **Headless sim:** Verilator (or Yosys CXXRTL) compiled to C++, driven by a thin
  harness (load ROM, tick clock, inject keys, dump VRAM). LLM drives the harness
  over CLI/stdin — no UI.
- **Sync checker (the interesting bit):** KiCad netlist (`kicad-cli sch export
  netlist`) and Verilog (elaborated to a netlist via Yosys `write_json`) are both
  reduced to connectivity graphs and diffed against a part/pin mapping file. A
  mismatch fails CI.

KiCad stays the single source of truth — we **generate/verify** the HDL side from
it, not the other way round. No bidirectional sync.

## North star
Long-term, the two tracks **converge on the schematic as the single source of truth**
— one schematic-rooted model that is simultaneously the PCB netlist, the LVS-checked
structure, and a **runnable digital twin** (run emulation *on the digital schematic*),
with the `cosim/` software emulator + MAME as validation oracles. See
[`docs/vision.md`](docs/vision.md).

## Status

The north-star merge is reached for the boot path: the LVS-checked structural
`juku_top` netlist runs the real Juku ROM, matches cosim, renders the boot banner,
and reacts to keyboard input. CI now guards status-audit freshness, LVS, fast
subsystem probes, and the bounded boot regression.

- ✅ `cosim/` — software oracle for boot, keyboard, FDC/EKDOS probes, BASIC and
  monitor diagnostics.
- ✅ `hdl/` — structural runnable twin rooted in the same board/netlist evidence.
- ✅ `sync/` — LVS, boot, FDC, video, BASIC, sound, and monitor guard scripts.
- ✅ `kicad/` — routed replica main board: 237 footprints, 1548/1548 routed
  connections, 0 unconnected items, and 0 clearance/short blockers.
- ✅ **Replica manufacturing packet** — `kicad/check_replica_manufacturing_ready.sh`
  reports `READY TO UPLOAD`; final upload ZIP:
  `fab/gerbers/upload/juku-replica-gerbers-drill.zip`, SHA256
  `0f52569a63601573c300ef099561f93bda1845cf51985a530b9e46863232a211`.
- ⏳ Remaining work is external or higher-fidelity: vendor preview/order evidence,
  parts/PROMs, assembly, bench bring-up, exact factory media/PROM dumps, and the
  stronger video/jmon33/BASIC/EKDOS HDL boundaries tracked in `PLAN.md`.

## Layout

| Dir      | Purpose                                                       |
|----------|---------------------------------------------------------------|
| `kicad/` | KiCad project — schematic + PCB (source of truth)             |
| `hdl/`   | Verilog models (8080 core, memory, decoder, peripherals)      |
| `cosim/` | Headless simulation harness (Verilator / CXXRTL driver)       |
| `sync/`  | LVS-style connectivity checker + part/pin mapping             |
| `roms/`  | ROM images and policy notes                                   |
| `docs/`  | Design notes / decisions                                      |
