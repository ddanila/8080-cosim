# FDC readiness

Status: **HDL WD1793 VENDORED-MEDIA SECTOR READY**

This guard proves the first HDL-side WD1793 behavior slice needed by WS-B1:

- `hdl/devices.v` implements D93-compatible restore, seek, read-sector,
  status, track, sector, data register, DRQ, and INTRQ behavior in
  `fdc_1793`.
- `hdl/sim/fdc_1793_tb.v` mirrors the C-side synthetic media guard:
  restore returns to track 0, seek copies the data register to the track
  register, read-sector streams 512 bytes, side select changes the stream,
  and motor-off read reports not-ready.
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
  9,640-byte framebuffer dump, immediately before the cosim first-PIC point at
  30,520 writes.

## Command

```sh
sync/fdc_check.sh
sync/juku_top_io_decode_probe.sh
sync/juku_top_30000_state_probe.sh
sync/juku_top_fdc_probe.sh
```

## Evidence

| Check | Result |
| --- | --- |
| Restore command clears transfer and returns to track 0 | PASS |
| Seek command copies data register to track register | PASS |
| Read-sector command asserts BUSY/DRQ and streams 512 bytes | PASS |
| Side select affects the synthetic sector stream | PASS |
| Vendored `JUKU1.CPM` sector 2 bytes are streamed through the HDL FDC | PASS |
| DRQ asserts during the sector transfer and INTRQ asserts on completion | PASS |
| Motor-off read reports NOT READY | PASS |
| `juku_top` raw I/O and settled PPI decode are visible in the fast decode probe | PASS |
| `juku_top` and cosim PC plus VRAM match at 30,000 writes before the first-PIC window | PASS |
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
- `docs/juku-top-30000-state-probe.md` captures the slow pre-PIC comparison:
  cosim and `juku_top` both stop at PC `0x0484` after 30,000 VRAM writes, and
  their framebuffer dumps have the same SHA256
  `0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68`. The open
  problem is top-level simulation speed/checkpointing past the 30,520-write
  first-PIC point, not a proven pre-PIC functional divergence.
- `docs/ekdos-timing-reference.md` records the fast cosim timing target for the
  same vendored `TDD` path: first frame IRQ at 33,812 VRAM writes and first FDC
  command at 63,085 VRAM writes.
- Preserve the Arti `JUKU1.CPM` cosim proof from
  `docs/ekdos-media-acquisition.md` as the disk-backed reference.
- If deeper controller behavior becomes the blocker, decide whether GPL
  Sorgelig-lineage `wd1793.sv` is acceptable to vendor/adapt.
- Confirm D93 INTRQ/DRQ, MR, CLK, and D100 OE/T wiring during the owner session.
