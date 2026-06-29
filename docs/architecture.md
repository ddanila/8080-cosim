# Architecture & reasoning

## The actual problem

We are not "syncing two programs". We are checking that **two netlists describe
the same connectivity**:

- A KiCad schematic *is* a netlist (components + which pins join which nets).
- A structural Verilog top-level *is* a netlist (chip instances + wires).

Keeping them in sync is the same problem the IC world calls **LVS / netlist
equivalence checking**. That framing is why no tool fork is needed — the glue is a
graph comparison that lives *outside* both tools.

## Why not fork KiCad / Verilator

Forking buys nothing and creates merge maintenance against two fast-moving
upstreams. Both already expose the needed extension points:

- KiCad: `kicad-cli sch export netlist`, the Python API, and custom netlist
  exporters as *plugins*.
- Verilog side: Yosys reads structural Verilog and emits a flattened netlist as
  JSON (`read_verilog; hierarchy; proc; write_json`).

So both sides can be turned into comparable graphs by *consuming their outputs*.

## Pipeline

```
KiCad schematic  ──kicad-cli sch export netlist──►  netlist  ──┐
                                                               ├─► normalize → graph diff → pass/fail
Verilog top      ──yosys write_json──►  netlist  ──────────────┘
```

- Nodes = pins, edges = nets.
- A mapping file relates KiCad refdes/pin ↔ Verilog instance/port.
- Mismatch fails CI.

## Single source of truth

KiCad schematic is authoritative. We **generate or verify** the HDL from it.
No bidirectional sync (edit-either-side-propagate) — that's a tar pit and
unnecessary.

## Effort tiers

- **Tier 1 — sync checker (MVP, ~a week):** hand-write the Verilog, build the
  graph-diff guardrail. Catches "rewired the board, forgot to update the model"
  in both directions. ~80% of the value for ~20% of the effort.
- **Tier 2 — auto-generator (KiCad → Verilog, weeks, brittle):** only if the
  design churns enough to justify it.

## Known hard parts

- **Tri-state buses.** The data bus has many drivers (CPU/ROM/RAM/peripherals)
  on shared nets. Verilog needs `inout`/`tri`; each model drives `z` when
  deselected. KiCad has no concept of drive direction — it comes from the models,
  not the schematic.
- **Passives & analog.** Pull-ups, decoupling caps, crystal + clock gen (8224)
  don't map to digital Verilog. Filter or hand-model them.
- **Part/pin library.** Each KiCad symbol needs a matching Verilog model with a
  pin-number ↔ port map. 74xx libraries exist; CPU/ROM/RAM/peripherals are
  custom. For an 8080 box this is ~20–40 unique parts — bounded but the bulk of
  the labor.

## Important limitation

Structural sync only proves the **wiring matches**. It does **not** prove the
chip behavioral models are *correct*. Model correctness is a separate axis,
covered by simulation/tests — don't let a green sync check imply correct models.
