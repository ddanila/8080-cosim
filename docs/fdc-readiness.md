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
  512 bytes, side select changes the stream, Type-III write-track is rejected
  with write-protect for the read-only raw-image backend, and motor-off read
  reports not-ready.
- The same testbench also runs with `+disk=media/disks/JUKU1.CPM +disk_heads=2`
  and verifies that the HDL WD1793 path reads real bytes from the vendored raw
  disk image.
- `docs/fdc-core-survey.md` records why this remains a bounded boot shim rather
  than a growing manual replacement for a full upstream ВГ93/WD1793 core.
- `sync/juku_top_io_decode_probe.sh` proves the top-level diagnostics can see
  raw ROMBIOS I/O and settled D7/D9 chip-select decode before the long FDC probe
  reaches the post-banner window.
- `sync/juku_top_30000_state_probe.sh` proves the expensive top-level run now
  matches cosim through the post-PIC, pre-FDC first-frame anchor at 33,812 VRAM
  writes when frame IRQs are disabled, with effective PC `0x0E23`, a
  byte-identical 9,640-byte framebuffer dump, and matching visible
  CPU/PPI/PIC/FDC register state.
- `docs/juku-top-30520-reachability.md` records that a 360-second exact-PC stop
  at `0x02B9` and a 900-second 30,520-write comparison do not produce an HDL
  post-banner dump. That old boundary is now superseded by the checkpoint and
  uninterrupted Verilator prompt guards below.
- `sync/ekdos_checkpoint_reference.py` pins the matching cosim-side full
  machine checkpoint at that 30,000-write boundary, including CPU
  registers/flags, 64 KiB RAM hash, banking, keyboard/PIC/PPI/FDC state, and
  framebuffer hash, for a future post-banner HDL resume diagnostic.
- `sync/juku_top_checkpoint_load_check.py` proves the RAM and visible-state
  halves of that resume path can already be loaded into the LVS-checked
  `juku_top`: D84..D91 bit-sliced DRAM dumps back with matching 64 KiB RAM and
  VRAM hashes, and the checkpoint CPU architectural registers plus key
  PPI/PIC/FDC latches are injected and verified.
- `sync/juku_top_checkpoint_resume_probe.py` is a focused, non-CI checkpoint
  resume probe: it seeds the vm80a core at a clean M1 fetch boundary from that
  loaded checkpoint and, when run locally, reaches the pinned post-checkpoint
  PIC `0xD6` write and no-key keyboard `0xCF` read through decoded ports.
- `sync/juku_top_checkpoint_fdc_probe.py` extends that checkpointed
  diagnostic with frame IRQs and fixed `TDD` keyboard stimulus. Its default
  cycle-targeted checkpoint at 8,711,550 cycles / 63,095 framebuffer writes /
  PC `0xE643` resumes `juku_top` and drains 13 full 512-byte sectors
  (6,656 `IN 0x1F` data-register reads) after the decoded WD1793/VG93
  command/setup sequence. A second clean late-sector checkpoint at 10,066,690
  cycles / 73,386 framebuffer writes / PC `0xE5A0` resumes immediately before
  the `OUT 0x1C = 0x80` read-sector command and drains the remaining 8 full
  sectors (4,096 more `IN 0x1F` reads). Together these checkpoint windows cover
  the full 10,752-byte FDC data-read count seen on the cosim `A>` path. The
  same late checkpoint can continue past the final FDC sector burst and render
  the EKDOS `A>` prompt bitmap at `x=0`, `y=70` through checkpoint-resumed
  `juku_top` CPU execution. `sync/ekdos_checkpoint_prompt_check.sh` provides
  a named local/deep guard for that late checkpoint prompt proof. That split
  checkpoint proof is now superseded by the uninterrupted reset-driven
  Verilator prompt proof, but the first-FDC checkpoint at 63,085 framebuffer
  writes and the earlier 42,000-write key-window checkpoint remain available
  as non-CI narrowing runs.
- `sync/juku_top_fdc_probe.sh` now also accepts `JUKU_TOP_FDC_STOPPC=HEX` plus
  optional `JUKU_TOP_FDC_STOPPC_SKIP=N`, which map to the `juku_top_tb`
  `+stoppc=HEX` / `+stoppc_skip=N` CPU-address stop hooks for focused ROMBIOS
  boundary diagnostics, `JUKU_TOP_FDC_TRACECHK=N` for the ROMBIOS checksum
  helper, `JUKU_TOP_FDC_STOPFDCDATA=N` for compact sector-drain stops, and
  `JUKU_TOP_FDC_STOPPROMPT=1`, which maps to the same uninterrupted harness's
  EKDOS `A>` bitmap oracle at `x=0`, `y=70`.
- `sync/juku_top_periph_bus_check.sh` drives `juku_top`'s buffered CPU bus
  directly and proves decoded keyboard/PIC/PPI/FDC access, including the pinned
  no-key `0xCF` keyboard poll, shifted-`T` `0x88` poll, frame INTA vector
  `0xFED4`, exact ROMBIOS first FDC restore command `0x02`, and a media-backed
  `JUKU1.CPM` sector byte, without waiting for the slow ROMBIOS draw loop.

## Command

```sh
sync/fdc_check.sh
sync/juku_top_io_decode_probe.sh
sync/juku_top_pc_stop_probe.sh
sync/juku_top_periph_bus_check.sh
sync/juku_top_30000_state_probe.sh
sync/ekdos_checkpoint_reference.py
sync/juku_top_checkpoint_load_check.py
sync/juku_top_checkpoint_resume_probe.py
sync/juku_top_checkpoint_fdc_probe.py
sync/ekdos_checkpoint_prompt_check.sh
sync/juku_top_fdc_prompt_check.sh
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
| Write-track command completes with WRITE PROTECT instead of BUSY forever | PASS |
| DRQ asserts during the sector transfer and INTRQ asserts on completion | PASS |
| Motor-off read reports NOT READY | PASS |
| `juku_top` raw I/O and settled PPI decode are visible in the fast decode probe | PASS |
| `juku_top` decoded keyboard/PIC/PPI/FDC direct-bus path mirrors pinned EKDOS I/O and reaches vendored `JUKU1.CPM` data | PASS |
| `juku_top` and cosim effective PC, VRAM, and visible CPU/PPI/PIC/FDC state match at 33,812 writes before the first frame IRQ/FDC window | PASS |
| cosim full-machine checkpoint is pinned at the same 30,000-write boundary | PASS |
| checkpoint RAM and visible CPU/PPI/PIC/FDC state load into `juku_top` | PASS |
| focused checkpoint-resumed `juku_top` probe reaches first post-checkpoint PIC write and no-key keyboard read | PASS (non-CI) |
| checkpoint-resumed `juku_top` from the cycle-targeted FDC checkpoint drains 6,656 data-register reads | PASS (non-CI) |
| checkpoint-resumed `juku_top` from the late FDC checkpoint drains 4,096 more data-register reads | PASS (non-CI) |
| checkpoint-resumed `juku_top` from the late FDC checkpoint reaches EKDOS `A>` prompt bitmap | PASS (local/deep) |
| `juku_top` loads vendored `JUKU1.CPM` and reaches first BIOS VRAM write under the FDC probe | PASS |
| `juku_top` matches cosim through the former post-30,180 checksum split and the 30,520-write first-PIC window | PASS |
| `juku_top` uninterrupted reset path drains 10,752 FDC data-register reads and reaches EKDOS `A>` | PASS (local/deep) |
| committed `juku_top` prompt report is freshness-guarded by a routine check | PASS |

## Remaining Boundary

- Keep the full `ROMBIOS 3.43` `<T>, <D>, <D>` prompt proof guarded while
  moving on to the remaining video/PROM/BASIC/PCB tasks. `sync/juku_top_fdc_prompt_check.sh`
  is the routine guard for the committed prompt evidence; set
  `JUKU_TOP_FDC_PROMPT_DEEP=1` to rerun the expensive Verilator prompt proof
  locally.
- `docs/juku-top-fdc-probe.md` now captures the current top-level boundary:
  disk media is loaded and the BIOS starts drawing, but the default 60-second
  bound still times out before the post-banner keyboard/PIC/FDC window.
- `docs/juku-top-io-decode-probe.md` captures the fast pre-banner decode sanity
  check: raw I/O is visible, the first mirrored PPI1 write decodes, and the
  early ROMBIOS sample counts PPI0 writes after the trace samples the decoder
  one timestep after the I/O edge.
- `docs/juku-top-periph-bus-check.md` captures the direct-bus top-level
  peripheral proof: PIC register readback, frame INTA vector `0xFED4`, no-key
  `0xCF` and shifted-`T` `0x88` keyboard scans, PPI0 motor-on latch, exact
  ROMBIOS first FDC restore command `0x02`, FDC seek/status, and the first
  `JUKU1.CPM` track 0 sector 2 byte all pass through decoded `juku_top` ports.
- `docs/juku-top-30000-state-probe.md` captures the slow comparison through the
  post-PIC, pre-FDC first-frame anchor: cosim stops at PC `0x0E23` and
  `juku_top` has effective PC `0x0E23` after 33,812 VRAM writes, with matching
  visible CPU/PPI/PIC/FDC state and framebuffer SHA256
  `559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d`.
- `docs/ekdos-checkpoint-reference.md` captures the corresponding full cosim
  RAM/CPU/peripheral checkpoint.
- `docs/juku-top-checkpoint-load.md` proves that checkpoint RAM and visible
  CPU/PPI/PIC/FDC latches can be injected into the top-level model.
- `docs/juku-top-checkpoint-resume.md` records a focused seeded M1-fetch
  resume from that checkpoint reaching the first post-checkpoint PIC
  programming write and no-key keyboard read through the decoded `juku_top`
  bus. This is not yet a mandatory CI invariant; the open hardening task is
  making the seeded vm80a microstate portable across runner schedules before
  extending it toward FDC I/O and EKDOS `A>`.
- `docs/juku-top-checkpoint-fdc-probe.md` records the next checkpointed
  boundary: with frame IRQs and fixed `TDD` stimulus state carried from cosim,
  the default cycle-targeted checkpoint resumes `juku_top` at PC `0xE643` and
  drains 13 full 512-byte sectors through decoded FDC data-register reads after
  the first read-sector setup. `docs/juku-top-checkpoint-fdc-late-probe.md`
  records the late cycle-targeted checkpoint at PC `0xE5A0`, which resumes
  immediately before a later read-sector command and drains the remaining
  8 full sectors. These split checkpoint windows cover all 10,752 FDC
  data-register reads observed before the cosim prompt.
- `sync/ekdos_checkpoint_prompt_check.sh` and
  `docs/juku-top-checkpoint-fdc-prompt-probe.md` record the same late
  checkpoint continuing past the final FDC sector burst to the EKDOS `A>`
  prompt bitmap. This older split proof is now superseded by the uninterrupted
  reset-driven Verilator prompt proof, but remains useful as a checkpointed
  diagnostic. GitHub push runners keep the lower-level raw sector and
  direct-bus FDC guards.
- `docs/ekdos-timing-reference.md` records the fast cosim timing target for the
  same vendored `TDD` path: first frame IRQ at 33,812 VRAM writes and first FDC
  command at 63,085 VRAM writes.
- `docs/juku-top-fdc-verilator-probe.md` records the faster reset-driven
  `juku_top` long-window diagnostic: with the D6 reset-overlay fix and
  live WD1793 motor/disk readiness, the Verilator path reaches decoded PIC
  setup, frame interrupts, WD1793 sector/data/command writes, drains all
  10,752 FDC data-register reads on the `TDD` path, and reaches the EKDOS
  `A>` bitmap at `x=0`, `y=70`.
- `docs/juku-top-fdc-alignment.md` summarizes that committed HDL report and
  keeps the current uninterrupted boundary explicit: reset-driven `juku_top`
  now reaches the full ROMBIOS `TDD` sector sequence to EKDOS `A>`.
- `docs/ekdos-ioseq-reference.md` records the full cosim I/O event stream that
  the direct-bus top-level guard mirrors for keyboard/PIC/PPI/FDC boundaries.
- Preserve the Arti `JUKU1.CPM` cosim proof from
  `docs/ekdos-media-acquisition.md` as the disk-backed reference.
- If deeper controller behavior becomes the blocker, decide whether GPL
  Sorgelig-lineage `wd1793.sv` is acceptable to vendor/adapt.
- Confirm D93 INTRQ/DRQ, MR, CLK, and D100 OE/T wiring during the owner session.
