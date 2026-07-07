# North star — converge the two tracks on the schematic

Today we deliberately run **two orthogonal tracks**:

- **Behavioral track** (`cosim/`): a software 8080 emulator that actually executes
  the ROM headless. Its memory/I-O map is hand-coded C — fast path to "it runs,"
  but *not* derived from the schematic.
- **Structural track** (`hdl/` + `kicad/` + `sync/`): the schematic-derived netlist,
  **LVS-verified** against the drawing, but with **stub device behavior** — it proves
  *connectivity*, it can't *execute*.

## The far goal: merge them, schematic as source of truth
This has been reached for the boot path: `juku_top` is now the LVS-checked
structure that executes the real ROM, renders the banner, and reacts to input.
The remaining work is fidelity expansion around the still-bounded subsystems
tracked in `PLAN.md`.

The intended end state remains **one model rooted in the schematic**, so the same
schematic-verified structure is simultaneously:
1. the **PCB netlist** (fabrication),
2. the **LVS-checked structure** (correctness vs the drawing), and
3. a **runnable digital twin** — i.e. we literally *run emulation on the digital
   schematic*, not on a separate hand-coded model.

The scanned schematic (`ref/schematics/`) stays the **single source of truth**;
everything else derives from it.

## Convergence path (rough order)
1. **Harden the netlist** to fully scan-grounded (the "wiring" track) → the schematic
   model becomes trustworthy end-to-end (every net traced, not assumed).
2. **Attach behavioral models** to each chip in the structural model (fill the HDL
   device stubs / bind behavior to the verified netlist) so the *verified structure*
   executes the ROM.
3. **Cross-validate** the structural sim against the **oracles** — the `cosim/`
   software emulator and **MAME** — same boot, same banner in VRAM, same reactions.
4. **Outcome:** one schematic-rooted artifact = PCB + LVS-checked structure +
   executable digital twin. `cosim/` and MAME become *validation oracles*, not
   separate sources of truth.

## Roles in the merged world
| Artifact | Role |
|---|---|
| `ref/schematics/` | ground truth (structure) |
| `board.json` / netlist + `sync/` LVS | the verified bridge schematic↔model |
| `hdl/` | the structure; gains chip behavior to become the runnable twin |
| `cosim/` (software emu) + MAME | behavioral oracles to validate the twin against |

This is still the direction for the full machine. The boot-critical path now runs
on the verified structure; `cosim/` and MAME continue as validation oracles for
the remaining subsystems.
