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

## Current guards

- `sync/check.sh` — KiCad/HDL LVS connectivity, using KiCad CLI when available
  and the board JSON fallback otherwise.
- `sync/boot_check.sh` — cosim and HDL boot-regression guard against the real
  `ekta37` ROM, including the LVS-checked `juku_top`.
- `sync/cosim_check.sh` — slower value-level lockstep check between `juku_top`
  and the behavioral oracle.
- `sync/juk_disk_check.sh` — raw `.juk` loader and minimal WD1793 model guard
  with synthetic media.
- `sync/ekdos_fdc_probe.py` — ROMBIOS `<T>, <D>, <D>` FDC path probe, with
  optional `EKDOS_PROBE_DISK=/path/to/JUKU-1.juk`.
- `sync/video_readout_check.sh` — V2 video-readout guard: standalone ИР16
  serializer and `juku_top` `vid_out` both reconstruct the booted framebuffer
  byte-identically.
- `sync/basic_cart_check.sh` — optional BASIC cartridge-window guard: cosim
  `JUKU_CART` plus HDL D8/D22 expose `jbasic11.bin` at `0x4000`.
- `sync/beeper_check.sh` — D57 PIT channel 1 digital beeper-source guard:
  programmed `OUT1` toggles the traced `SOUND` net.

## Status

The LVS/boot path is no longer a small fixture: `juku_top` is the working
LVS-checked model and the guards above cover connectivity, boot behavior,
value-level lockstep, FDC sector-read scaffolding, and runnable video readout.
The remaining high-fidelity boundaries are the external EKDOS image, the full
interactive BASIC prompt path, the analog speaker/current check, dumped PROM
contents, and the РЕ3/АГ3-gated physical video slot timing.
