# 8080-cosim

Experiment: model an Intel 8080–based computer as **both** a physical PCB and a
runnable digital simulation, and keep the two models provably in sync — without a
GUI in the loop, so the whole thing can be driven by an LLM.

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

## Status

LVS pipeline **proven end-to-end on real tooling** (KiCad 10 + Yosys):
a generated KiCad schematic → `kicad-cli` netlist → `sync/lvs.py` → structural HDL
reports `IN SYNC` (and localizes faults on a miswired variant). Currently a 3-chip
subset (CPU/ROM/PPI0); next is extending to all 13 chips.

- ✅ `docs/hardware-map.md` — authoritative map (memory/banking/IO/video) from MAME
- ✅ `cosim/` — traced 8080 (boots real init; parked at the AT-keyboard handshake)
- ✅ `hdl/` — structural top (13 chips) → Yosys netlist
- ✅ `sync/` — connectivity LVS checker (KiCad ↔ HDL), CI-ready
- ✅ `kicad/` — schematic generator from a board spec; real `kicad-cli` round-trip
- ⏳ extend LVS to all 13 chips; swap in real Juku schematics when available

## Layout

| Dir      | Purpose                                                       |
|----------|---------------------------------------------------------------|
| `kicad/` | KiCad project — schematic + PCB (source of truth)             |
| `hdl/`   | Verilog models (8080 core, memory, decoder, peripherals)      |
| `cosim/` | Headless simulation harness (Verilator / CXXRTL driver)       |
| `sync/`  | LVS-style connectivity checker + part/pin mapping             |
| `rom/`   | ROM source + assembled images                                 |
| `docs/`  | Design notes / decisions                                      |
