# FDC readiness

Status: **HDL WD1793 VENDORED-MEDIA SECTOR READY**

This guard proves the first HDL-side WD1793 behavior slice needed by WS-B1:

- `hdl/devices.v` implements D93-compatible restore, seek, step,
  step-in, step-out, read-sector, status, track, sector, data register,
  DRQ, and INTRQ behavior in `fdc_1793`.
- `hdl/sim/fdc_1793_tb.v` mirrors the C-side synthetic media guard:
  restore returns to track 0, seek copies the data register to the track
  register, step commands update or preserve the track register according
  to the command's update bit and previous direction, read-sector streams
  512 bytes, side select changes the stream, and motor-off read reports
  not-ready.
- The same testbench also runs with `+disk=media/disks/JUKU1.CPM +disk_heads=2`
  and verifies that the HDL WD1793 path reads real bytes from the vendored raw
  disk image.
- `docs/fdc-core-survey.md` records why this remains a bounded boot shim rather
  than a growing manual replacement for a full upstream ВГ93/WD1793 core.
- `sync/juku_top_io_decode_probe.sh` proves the top-level diagnostics can see
  raw ROMBIOS I/O and settled D7/D9 chip-select decode before the long FDC probe
  reaches the post-banner window.
- `sync/juku_top_30000_state_probe.sh` proves the expensive top-level run still
  matches cosim at PC `0x0484` after 30,000 VRAM writes, with a byte-identical
  9,640-byte framebuffer dump and matching visible CPU/PPI/PIC/FDC register
  state, immediately before the cosim first-PIC point at 30,520 writes.
- `docs/juku-top-30520-reachability.md` records that a 360-second exact-PC stop
  at `0x02B9` and a 900-second 30,520-write comparison do not produce an HDL
  post-banner dump, so the next M2 automation step should be
  checkpoint/fast-forward or a narrow post-banner harness.
- `sync/ekdos_checkpoint_reference.py` pins the matching cosim-side full
  machine checkpoint at that 30,000-write boundary, including CPU
  registers/flags, 64 KiB RAM hash, banking, keyboard/PIC/PPI/FDC state, and
  framebuffer hash, for a future post-banner HDL resume diagnostic.
- `sync/juku_top_checkpoint_load_check.py` proves the RAM and visible-state
  halves of that resume path can already be loaded into the LVS-checked
  `juku_top`: D84..D91 bit-sliced DRAM dumps back with matching 64 KiB RAM and
  VRAM hashes, and the checkpoint CPU architectural registers plus key
  PPI/PIC/FDC latches are injected and verified.
- `sync/juku_top_fdc_probe.sh` now also accepts `JUKU_TOP_FDC_STOPPC=HEX`,
  which maps to the `juku_top_tb` `+stoppc=HEX` CPU-address stop hook for
  focused ROMBIOS boundary diagnostics.
- `sync/juku_top_periph_bus_check.sh` drives `juku_top`'s buffered CPU bus
  directly and proves decoded keyboard/PIC/PPI/FDC access, including frame
  INTA vector `0xFED4` and a media-backed `JUKU1.CPM` sector byte, without
  waiting for the slow ROMBIOS draw loop.

## Command

```sh
sync/fdc_check.sh
sync/juku_top_io_decode_probe.sh
sync/juku_top_pc_stop_probe.sh
sync/juku_top_periph_bus_check.sh
sync/juku_top_30000_state_probe.sh
sync/ekdos_checkpoint_reference.py
sync/juku_top_checkpoint_load_check.py
sync/juku_top_fdc_probe.sh
```

## Evidence

| Check | Result |
| --- | --- |
| Restore command clears transfer and returns to track 0 | PASS |
| Seek command copies data register to track register | PASS |
| Step, step-in, and step-out commands update the track register when requested | PASS |
| Read-sector command asserts BUSY/DRQ and streams 512 bytes | PASS |
| Side select affects the synthetic sector stream | PASS |
| Vendored `JUKU1.CPM` sector 2 bytes are streamed through the HDL FDC | PASS |
| DRQ asserts during the sector transfer and INTRQ asserts on completion | PASS |
| Motor-off read reports NOT READY | PASS |
| `juku_top` raw I/O and settled PPI decode are visible in the fast decode probe | PASS |
| `juku_top` decoded keyboard/PIC/PPI/FDC direct-bus path reaches vendored `JUKU1.CPM` data | PASS |
| `juku_top` and cosim PC, VRAM, and visible CPU/PPI/PIC/FDC state match at 30,000 writes before the first-PIC window | PASS |
| cosim full-machine checkpoint is pinned at the same 30,000-write boundary | PASS |
| checkpoint RAM and visible CPU/PPI/PIC/FDC state load into `juku_top` | PASS |
| `juku_top` loads vendored `JUKU1.CPM` and reaches first BIOS VRAM write under the FDC probe | PASS |
| `juku_top` reaches decoded FDC I/O within the bounded probe window | NO |

## Remaining Boundary

- Drive the full `ROMBIOS 3.43` `<T>, <D>, <D>` path through `juku_top` with
  `+disk=media/disks/JUKU1.CPM` and promote the HDL boundary from sector-ready
  to EKDOS-prompt-ready.
- `docs/juku-top-fdc-probe.md` now captures the current top-level boundary:
  disk media is loaded and the BIOS starts drawing, but the default 60-second
  bound still times out before the post-banner keyboard/PIC/FDC window.
- `docs/juku-top-io-decode-probe.md` captures the fast pre-banner decode sanity
  check: raw I/O is visible, the first mirrored PPI1 write decodes, and the
  early ROMBIOS sample counts PPI0 writes after the trace samples the decoder
  one timestep after the I/O edge.
- `docs/juku-top-periph-bus-check.md` captures the direct-bus top-level
  peripheral proof: PIC register readback, frame INTA vector `0xFED4`, shifted
  `T` keyboard scan, PPI0 motor-on latch, FDC seek/status, and the first
  `JUKU1.CPM` track 0 sector 2 byte all pass through decoded `juku_top` ports.
- `docs/juku-top-30000-state-probe.md` captures the slow pre-PIC comparison:
  cosim and `juku_top` both stop at PC `0x0484` after 30,000 VRAM writes, and
  their framebuffer dumps have the same SHA256
  `0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68`. The same
  run now also matches visible CPU registers/flags, PPI/PIC latches, and stable
  FDC register latches. The open problem is top-level simulation
  speed/checkpointing past the 30,520-write first-PIC point, not a proven
  pre-PIC functional divergence.
- `docs/ekdos-checkpoint-reference.md` captures the corresponding full cosim
  RAM/CPU/peripheral checkpoint. The next automation step is loading that state
  into a narrow HDL post-banner diagnostic; the checkpoint itself is not an HDL
  resume proof.
- `docs/juku-top-checkpoint-load.md` proves that checkpoint RAM and visible
  CPU/PPI/PIC/FDC latches can be injected into the top-level model. CPU
  microcycle-state initialization remains the resume boundary.
- `docs/ekdos-timing-reference.md` records the fast cosim timing target for the
  same vendored `TDD` path: first frame IRQ at 33,812 VRAM writes and first FDC
  command at 63,085 VRAM writes.
- `docs/ekdos-ioseq-reference.md` records the full cosim I/O event stream that
  the direct-bus top-level guard mirrors for keyboard/PIC/PPI/FDC boundaries.
- Preserve the Arti `JUKU1.CPM` cosim proof from
  `docs/ekdos-media-acquisition.md` as the disk-backed reference.
- If deeper controller behavior becomes the blocker, decide whether GPL
  Sorgelig-lineage `wd1793.sv` is acceptable to vendor/adapt.
- Confirm D93 INTRQ/DRQ, MR, CLK, and D100 OE/T wiring during the owner session.
