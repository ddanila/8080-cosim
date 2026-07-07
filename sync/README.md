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
- `sync/juk_disk_check.sh` — raw Juku disk loader and minimal WD1793 model guard
  with synthetic media.
- `sync/fdc_check.sh` — HDL WD1793 synthetic-sector guard for restore, seek,
  read-sector, status, side-select, and motor-off behavior.
- `sync/ekdos_fdc_probe.py` — ROMBIOS `<T>, <D>, <D>` FDC path probe; defaults
  to vendored `media/disks/JUKU1.CPM`, and disk-backed runs must reach the
  EKDOS `A>` prompt bitmap.
- `sync/ekdos_timing_reference.py` — fast cosim timing reference for the same
  vendored `TDD` path; records first PIC/PPI/FDC port touches versus cycles and
  framebuffer writes.
- `sync/ekdos_checkpoint_reference.py` — fast cosim full-machine checkpoint
  reference at 30,000 framebuffer writes on the vendored `TDD` path; records
  CPU registers, RAM hash, banking/PIC/PPI/FDC state, and the byte-identical
  pre-PIC boundary needed by a future HDL resume harness.
- `sync/juku_top_checkpoint_load_check.py` — fast top-level checkpoint-load
  guard; regenerates the 30,000-write cosim checkpoint, loads RAM into the
  `juku_top` D84..D91 bit-sliced DRAM planes, injects visible CPU architectural
  registers plus key PPI/PIC/FDC latches, and verifies full RAM plus VRAM hashes
  after dumping them back from the top-level model.
- `sync/ekdos_ioseq_reference.py` — full cosim I/O-sequence reference for the
  vendored `TDD` path; pins exact ROMBIOS keyboard/PIC/PPI/FDC events mirrored
  by the top-level direct-bus guard.
- `sync/juku_top_fdc_probe.sh` — bounded HDL diagnostic for the remaining
  `juku_top` ROMBIOS-to-FDC boundary; enables vendored disk media, frame
  interrupts, fixed `TDD` keyboard stimulus, traces VRAM progress and PIC setup,
  and can stop on decoded PIC/PPI/WD1793 I/O.
- `sync/juku_top_periph_bus_check.sh` — fast direct-bus `juku_top` guard for
  the post-banner peripheral boundary; drives decoded keyboard/PIC/PPI/FDC
  ports, verifies frame INTA vector `0xFED4`, and verifies a vendored
  `JUKU1.CPM` sector byte through the top-level bus.
- `sync/juku_top_io_decode_probe.sh` — fast top-level I/O decode diagnostic; it
  stops after the first 20 raw I/O cycles and verifies delayed trace sampling
  sees settled D7/D9 peripheral selects before the long FDC probe reaches the
  post-banner keyboard/FDC window.
- `sync/juku_top_30000_state_probe.sh` — slow pre-PIC state comparison. It
  stops cosim and `juku_top` at 30,000 VRAM writes on the vendored `TDD` path
  and verifies both are still at PC `0x0484`, just before the cosim first-PIC
  point at 30,520 writes.
- `sync/video_readout_check.sh` — V2 video-readout guard: standalone ИР16
  serializer and `juku_top` `vid_out` both reconstruct the booted framebuffer
  byte-identically.
- `sync/jmon33_interrupt_probe.py` — cosim guard for Monitor 3.3's
  interrupt-driven path: 8259 setup, `0xFF54` frame interrupt, keyboard-port
  reads, and VRAM writes.
- `sync/jmon33_ready_probe.py` — cosim guard for Monitor 3.3's deterministic
  monitor-idle framebuffer oracle: full VRAM SHA256 plus solid cursor block.
- `sync/jmon33_hdl_probe.sh` — HDL guard proving `juku_top` runs Monitor 3.3
  to the first video-memory write with frame interrupts enabled.
- `sync/jmon33_hdl_cursor_probe.py` — bounded HDL diagnostic for the stronger
  jmon33 monitor-idle cursor oracle; currently documents that the 300-write
  HDL boundary is still blank while the first-write guard remains passing.
- `sync/basic_cart_check.sh` — optional BASIC cartridge-window guard: cosim
  `JUKU_CART` plus HDL D8/D22 expose `jbasic11.bin` at `0x4000`.
- `sync/basic_launch_probe.py` — bounded cosim diagnostic for the monitor `B`
  command path into the BASIC cartridge; Monitor 3.3 reaches cartridge
  execution through a zero-filled RAM window, while EktaSoft 3.43m #0037
  remains a documented compatibility boundary.
- `sync/beeper_check.sh` — D57 PIT channel 1 digital beeper-source guard:
  programmed `OUT1` toggles the traced `SOUND` net.

## Status

The LVS/boot path is no longer a small fixture: `juku_top` is the working
LVS-checked model and the guards above cover connectivity, boot behavior,
value-level lockstep, cosim FDC sector-read/prompt scaffolding, HDL WD1793
synthetic-sector behavior, a bounded `juku_top` FDC-path diagnostic, and
runnable video readout. The remaining
high-fidelity boundaries are disk-backed FDC in `juku_top`, the user-visible
jmon33 command prompt and
cosim-vs-HDL comparison at the monitor-idle oracle boundary, the BASIC prompt
oracle plus HDL coverage of the Monitor 3.3 BASIC path, the analog
speaker/current check, dumped PROM contents, and the РЕ3/АГ3-gated physical
video slot timing.
