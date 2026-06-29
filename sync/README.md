# sync/ — KiCad ↔ HDL connectivity checker (LVS)

Proves the KiCad schematic and the structural Verilog describe the **same circuit**,
by comparing **net membership** (not names). Two netlists are equivalent iff they
partition the (instance, pin) endpoints into nets the same way. See
`../docs/architecture.md` for the rationale (no tool forks; both sides reduced to
graphs and diffed).

## Pipeline
```
KiCad schematic ─ kicad-cli sch export netlist --format kicadxml ─► net.xml ─┐ netlist_from_kicad.py
                                                                             ├─► lvs.py ─► IN SYNC / MISMATCH
hdl/*.v ─ yosys: read_verilog; hierarchy -top juku_top; write_json ─► .json ─┘ netlist_from_yosys.py
```

## Tools
- `netlist_from_yosys.py` — Yosys JSON → normalized `{instance:{type,pins}}` (Verilog side)
- `netlist_from_kicad.py` — KiCad XML netlist → same normalized shape (schematic side)
- `lvs.py` — diff core: maps refdes↔instance + KiCad pin#→logical name, builds
  per-net endpoint sets (bus pins expand per bit), reports HDL-only / KiCad-only nets
- `map.json` — the mapping: `instances` (refdes↔hdl instance) + `pinmaps.kicad`
  (pin number → logical name per component type). HDL logical pins are auto-derived.

## Run
```sh
yosys -q -p "read_verilog hdl/devices.v hdl/juku_top.v; hierarchy -top juku_top; write_json hdl/juku_top.json"
python3 sync/lvs.py --hdl hdl/juku_top.json --kicad <net.xml> --map sync/map.json
# exit 0 = in sync, 1 = mismatch  (suitable for CI)
```

## Status
Working on a 3-chip subset (CPU/ROM/PPI0) via hand-authored KiCad fixtures in
`testdata/` (one matching → IN SYNC, one miswired → MISMATCH, fault localized).
The fixtures stand in until the real schematic exists; the parsers/checker are
unchanged when fed real `kicad-cli` output.

Next: real KiCad schematic from `../docs/hardware-map.md`, export its netlist,
extend `map.json` to all 13 chips, run the same check.
