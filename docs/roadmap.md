# Structural-track roadmap (toward the digital twin)

**Goal (north-star, see `vision.md`):** the schematic is the single source of truth →
one model that is simultaneously the **PCB netlist**, the **LVS-checked structure**,
and a **runnable digital twin**.

**Where we are:** 52-chip full-module model, LVS green on real KiCad+Yosys, CI-guarded.
Provenance **28/99 scan-grounded, 71 assumed/boundary** — structure complete, but most
detailed pin-wiring is inferred, not yet traced.

---

## Phase A — Harden the wiring (assumed → scan)  ⟶ *trustworthy netlist*
Convert the 71 assumed/boundary nets to scan-traced, subsystem by subsystem (the way
the CPU core already is 100% scan). LVS stays green throughout; `provenance.py` tracks
the climbing scan fraction. Rough order by leverage:

- **A1 — Address bus B-side:** trace the 8286 buffer outputs → `BA` (input side done).
- **A2 — Memory bus:** EPROM/РУ5 data-pin order + per-chip chip-selects (which decode line).
- **A3 — Clock subsystem:** real pins of D59/D35/D38 + the phase-gate logic (D33/D38).
- **A4 — ИД7 I/O decoder:** isolate its refdes (un-found so far) + A2:A0 / enable / Y wiring.
- **A5 — Address mux + DRAM org:** КП14 select source + pin→`MA` map; how the 20 РУ5 split into banks/video.
- **A6 — Peripheral pins:** 8253 clock sources, 8255 port pins, USART/SIO signals → connectors.

**Milestone A:** provenance ≈ 99/99 scan-grounded → the netlist is fabrication-faithful.

### Progress log
- **A1 done** — 8286 B-side derived from the traced A-side + datasheet (8286 A_n↔B_n):
  D4 B-pins BA8←19, BA9←18, BA10←12, BA11←13, BA12←16, BA13←15, BA14←14, BA15←17.
  BA13–15 (buffer+decode only) → `scan`; BA8–12 stay `assumed` (EPROM taps = A2).
  Provenance **28 → 31/99**.
- *Note:* provenance is per-net (weakest link), so a net flips to `scan` only when
  ALL its endpoints are traced — progress is lumpy (later steps flip nets in batches).
  A per-endpoint provenance refinement would make the grind more measurable.

## Phase B — Real PCB artifact  ⟶ *fabricable board*
- Swap in the **real Juku schematics** when available (parsers unchanged; only pin maps).
- Either keep the generated net-label schematic and go netlist→footprints→layout, or
  author a proper graphical KiCad schematic (symbols + routed wires).
- **Milestone B:** a KiCad project with footprints + a DRC-clean PCB layout.

## Phase C — Merge the tracks  ⟶ *the schematic runs (north-star)*
- Give the **verified structure** behavior: replace HDL device stubs with behavioral
  models (8080 core + ROM/RAM with content + 8255/8253/8259/…), or bind the `cosim/`
  behavioral models onto the netlist chips.
- Simulate the structural model executing the ROM (Verilator/iverilog) → **banner in VRAM**.
- **Cross-validate** against the oracles: `cosim/` software emulator + MAME (same banner,
  same reactions). LVS already guarantees the structure matches the schematic.
- **Milestone C:** run emulation *on the digital schematic*; cosim/MAME become validation oracles.

---

## Sequencing — DECIDED: harden-first (A → B/C)
Make the structure trustworthy *before* giving it behavior, so when the schematic
finally runs (Phase C) it runs on verified truth, not assumptions — consistent with
the project's "scan = source of truth" discipline. Phase C waits until Phase A is
substantially done.

**Immediate next step: A1 — trace the 8286 address-buffer B-side outputs → `BA`**
(then A2 memory bus, A3 clock, A4 ИД7, A5 mux/DRAM, A6 peripheral pins). Each:
read the scan → flip the net's provenance `assumed → scan` → re-run LVS (stays green)
→ watch `provenance.py` climb toward 99/99.
