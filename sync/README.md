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
- `sync/reference_artifact_check.sh` — hash guard for vendored reference
  artifacts under `ref/baltijets-tech-docs`, `ref/ekdos-source`,
  `ref/reconstructed-proms`, and `ref/wd1772-vg93`.
- `scripts/report_wd1772_pla_inspection.py` — generated shape check for the
  vendored WD1772/VG93 PLA/PLM table; CI verifies the report is fresh.
- `scripts/export_wd1772_pla.py` — emits normalized JSON/CSV copies of the
  same PLA/PLM table for future controller-equation work.
- `scripts/report_ekdos_source_inspection.py` — generated source-level check
  for vendored `EKDOS30.ASM`; verifies the ROMBIOS floppy entry constants,
  floppy work-area labels, and 40-entry sector translation tables used by the
  EKDOS/FDC probes.
- `scripts/report_vendored_disk_catalog.py` — generated catalog of visible
  CP/M directory entries in the vendored Arti disk images; CI verifies the
  report is fresh and records the disk-side `JBASIC.COM`/BASIC toolchain lead.
- `scripts/extract_basic_disk_files.py` — generated extraction of the strongest
  disk-side BASIC candidates under `ref/extracted-software/`; CI verifies the
  extracted binaries, including the EKDOS live-load `JUKPROG2` candidate,
  checksums, and report stay fresh.
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
- `sync/ekdos_jbasic_command_probe.py` — post-`A>` EKDOS command diagnostic;
  uses `JUKU_KEYS=TDD|JBASIC\r` so `|` waits for the prompt bitmap, then types
  `JBASIC` on `media/disks/JUKPROG2.CPM` and pins the current FDC/screen
  boundary plus final-RAM entry/string evidence for the live-load disk BASIC
  candidate.
- `sync/ekdos_timing_reference.py` — fast cosim timing reference for the same
  vendored `TDD` path; records first PIC/PPI/FDC port touches versus cycles and
  framebuffer writes.
- `sync/juku_top_fdc_probe.sh` — bounded reset-driven `juku_top` diagnostic
  for the vendored `TDD` path. It defaults to the CI-compatible Icarus flow and
  can run locally with `JUKU_TOP_FDC_SIM=verilator` for a faster long window;
  `docs/juku-top-fdc-verilator-probe.md` currently records the 70,000-write
  boundary with T/D/D stimulus observed but no decoded PIC/FDC path yet.
- `scripts/report_juku_top_fdc_alignment.py` — fast freshness guard comparing
  that committed Verilator long-window report against a regenerated cosim
  70,000-write checkpoint. It records that cosim is already in the FDC path
  while reset-driven `juku_top` has not reached PIC/FDC I/O.
- `sync/ekdos_checkpoint_reference.py` — fast cosim full-machine checkpoint
  reference at 30,000 framebuffer writes on the vendored `TDD` path; records
  CPU registers, RAM hash, banking/PIC/PPI/FDC state, and the byte-identical
  pre-PIC boundary needed by a future HDL resume harness.
- `sync/juku_top_checkpoint_load_check.py` — fast top-level checkpoint-load
  guard; regenerates the 30,000-write cosim checkpoint, loads RAM into the
  `juku_top` D84..D91 bit-sliced DRAM planes, injects visible CPU architectural
  registers plus key PPI/PIC/FDC latches, and verifies full RAM plus VRAM hashes
  after dumping them back from the top-level model.
- `sync/juku_top_checkpoint_resume_probe.py` — focused push-CI
  checkpoint-resume guard; loads the same checkpoint into `juku_top`, seeds the
  vm80a core at a clean M1 fetch boundary, and reaches the pinned
  post-checkpoint PIC `0xD6` write and no-key keyboard `0xCF` read through
  decoded ports.
- `sync/juku_top_checkpoint_fdc_probe.py` — focused non-CI checkpoint-resumed
  FDC diagnostic; enables frame IRQs and fixed `TDD` key stimulus from the
  generated cosim checkpoint, then stops on decoded FDC data-register reads if
  reached. The default cycle-targeted checkpoint at 8,711,550 cycles / 63,095
  framebuffer writes / PC `0xE643` drains 13 full sectors, 6,656 reads through
  `0x1F`; the older first-command checkpoint remains available with
  `JUKU_TOP_CHECKPOINT_FDC_CYCLES=0
  JUKU_TOP_CHECKPOINT_FDC_WRITES=63085 JUKU_TOP_CHECKPOINT_FDC_STOP_IO=1
  JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READ=0`, and the earlier key-window
  checkpoint with `JUKU_TOP_CHECKPOINT_FDC_WRITES=42000`.
- `sync/ekdos_checkpoint_prompt_check.sh` — local/deep guard for the strongest
  current HDL EKDOS prompt proof. It runs the late checkpoint window through
  `sync/juku_top_checkpoint_fdc_probe.py` and requires checkpoint-resumed
  `juku_top` to render the EKDOS `A>` prompt bitmap. It is intentionally not in
  push CI because GitHub runners are too slow for this vm80a resume window.
- `sync/juku_top_checkpoint_jbasic_probe.py` — checkpoint-resumed HDL bridge
  from the EKDOS `A>` prompt toward the disk BASIC path. It generates a
  `JUKPROG2.CPM` prompt checkpoint, loads it into `juku_top`, injects the exact
  `JBASIC` + Enter sequence with `+jbasickeys=1`, and documents the current
  command-stimulus boundary plus the new opt-in `+stopjbasicready=1` `READY`
  glyph oracle.
- `sync/ekdos_jbasic_checkpoint_check.sh` — local/deep guard for the strongest
  current HDL EKDOS BASIC proof. It runs the prompt-checkpoint JBASIC bridge and
  requires the visible `A>JBASIC` command line plus the final fixed-`0xD800`
  BASIC `READY` glyph. It is intentionally syntax-checked, not run, in push CI.
- `sync/juku_top_checkpoint_jbasic_late_probe.py` — late checkpoint-resumed
  HDL guard for the disk BASIC path. It generates the cosim `TDD|JBASIC\r`
  state after 19,968 WD1793 data-register reads, resumes `juku_top` with no
  keyboard stimulus, and requires the fixed-`0xD800` BASIC `READY` glyph oracle.
  Its opt-in `JUKU_TOP_CHECKPOINT_JBASIC_LATE_STOP_DATA_READS=N` mode also
  records bounded mid-transfer drains, currently used by
  `docs/juku-top-checkpoint-jbasic-mid-probe.md`.
- `sync/ekdos_ioseq_reference.py` — full cosim I/O-sequence reference for the
  vendored `TDD` path; pins exact ROMBIOS keyboard/PIC/PPI/FDC events mirrored
  by the top-level direct-bus guard.
- `sync/juku_top_fdc_probe.sh` — bounded HDL diagnostic for the remaining
  `juku_top` ROMBIOS-to-FDC boundary; enables vendored disk media, frame
  interrupts, fixed `TDD` keyboard stimulus, traces VRAM progress and PIC setup,
  and can stop on decoded PIC/PPI/WD1793 I/O. Set
  `JUKU_TOP_FDC_STOPPROMPT=1` and `JUKU_TOP_FDC_STOPFDC=0` for a long
  uninterrupted run that stops only if the EKDOS `A>` bitmap appears at
  `x=0`, `y=70`.
- `sync/juku_top_periph_bus_check.sh` — fast direct-bus `juku_top` guard for
  the post-banner peripheral boundary; drives decoded keyboard/PIC/PPI/FDC
  ports, verifies the pinned no-key `0xCF` and shifted-`T` `0x88` keyboard
  reads, frame INTA vector `0xFED4`, the exact ROMBIOS first FDC restore
  command `0x02`, and a vendored `JUKU1.CPM` sector byte through the top-level
  bus.
- `sync/juku_top_io_decode_probe.sh` — fast top-level I/O decode diagnostic; it
  stops after the first 20 raw I/O cycles and verifies delayed trace sampling
  sees settled D7/D9 peripheral selects before the long FDC probe reaches the
  post-banner keyboard/FDC window.
- `sync/juku_top_30000_state_probe.sh` — slow reset-path state comparison. It
  can stop cosim and `juku_top` at a selected VRAM write count on the vendored
  `TDD` path; the current committed proof uses 33,812 writes with frame IRQs
  disabled and verifies effective PC `0x0E23`, byte-identical framebuffer data,
  and matching visible CPU/PPI/PIC/FDC register state at the first-frame anchor.
- `sync/video_readout_check.sh` — V2 video-readout guard: standalone ИР16
  serializer and `juku_top` `vid_out` both reconstruct the booted framebuffer
  byte-identically.
- `sync/video_timing_check.sh` — runnable raster-geometry guard: parses the
  vendored MAME Juku constants and proves `video_raster` emits a 40 x 241 byte
  scan with one load phase plus seven shift phases per framebuffer byte.
- `scripts/report_video_slot_timing_audit.py` — generated M4/V3 boundary audit:
  verifies the traced physical serializer/mux/decode pieces are present, the
  runnable model still uses the explicit sim-only video read path, and the D94
  `.092` РЕ3 timing PROM dump/table is still absent.
- `scripts/report_d94_reconstruction_constraints.py` — generated D94 `.092`
  reconstruction boundary; proves the address side is traced to `BA11..BA15`
  and records the still-missing enable/output nets plus absent `.092` dump/table
  before any burnable replacement is attempted.
- `sync/jmon33_interrupt_probe.py` — cosim guard for Monitor 3.3's
  interrupt-driven path: 8259 setup, `0xFF54` frame interrupt, keyboard-port
  reads, and VRAM writes.
- `sync/jmon33_ready_probe.py` — cosim guard for Monitor 3.3's deterministic
  monitor-idle framebuffer oracle: full VRAM SHA256 plus solid cursor block.
- `sync/jmon33_hdl_probe.sh` — HDL guard proving `juku_top` runs Monitor 3.3
  to the first video-memory write with frame interrupts enabled.
- `sync/jmon33_hdl_cursor_probe.py` — bounded HDL diagnostic for the stronger
  jmon33 monitor-idle cursor oracle; documents that the uninterrupted HDL path
  reaches the full 10/10-row cursor and exact cosim framebuffer hash under
  Verilator, while the first-write guard remains passing.
- `sync/jmon33_checkpoint_cursor_probe.py` — checkpoint-resumed HDL diagnostic
  for the same jmon33 cursor oracle. It starts from a blank late cosim
  checkpoint at 3,801,005 cycles / PC `0xF2C0`; the resumed `juku_top` path
  services frame interrupts, scans keyboard reads, and reaches the cosim
  monitor-idle cursor framebuffer hash.
- `sync/jmon33_checkpoint_deep_check.sh` — local/deep aggregate for the
  checkpoint-resumed jmon33 HDL cursor, `A`, `B`, and FDC-aware `T` command
  oracles. It is syntax-checked in push CI, but intentionally not run there
  because the vm80a resume windows are long on shared runners.
- `sync/jmon33_command_probe.py` — cosim guard for Monitor 3.3's user-visible
  command surface. It uses a jmon33-appropriate keyboard hold window and proves
  typed `A`, `T`, and `B` plus return are sampled through port `0x05` and move
  the visible command cursor to deterministic screen positions.
- `sync/jmon33_idle_command_probe.py` — cosim guard for the same Monitor 3.3
  commands typed after the idle cursor is already visible; this is the reference
  oracle for checkpoint-resumed HDL command work.
- `sync/jmon33_fdc_command_probe.py` — cosim diagnostic for Monitor 3.3's
  idle-prompt `T` command when the FDC is visible. It compares no-disk behavior
  with vendored `media/disks/JUKU1.CPM` and pins the `0xFD` write-track /
  write-protect polling boundary used by HDL `T` command debugging.
- `sync/jmon33_hdl_fdc_command_probe.py` — checkpoint-resumed HDL oracle
  for the same FDC-aware `T` boundary. It resumes from the disk-backed cosim
  checkpoint with `+disk=media/disks/JUKU1.CPM`, traces FDC I/O, and requires
  the structural path to read write-protect status `0x40`.
- `sync/jmon33_hdl_a_command_probe.py` — named guard for the currently passing
  checkpoint-resumed HDL command row. It pins the late Monitor 3.3 phase where
  the command key has already been consumed and requires the `A` command to
  reach the delayed idle-prompt framebuffer oracle.
- `sync/jmon33_hdl_b_command_probe.py` — named guard for the analogous
  checkpoint-resumed HDL `B` command row. It uses the same late-phase command
  checkpoint recipe and requires the delayed idle-prompt `B` framebuffer oracle.
- `sync/jmon33_hdl_command_probe.py` — checkpoint-resumed HDL diagnostic for
  the same command surface. It delays keyboard stimulus until after the proven
  HDL cursor boundary and compares against `docs/jmon33-idle-command-probe.md`.
  The `A` command now reaches its HDL framebuffer oracle; the preserved
  `docs/jmon33-hdl-t-command-fdc-diagnostic.md` run shows `T` entering heavy
  FDC I/O, so that path needs an FDC-aware oracle before more keyboard timing
  scans.
- `sync/basic_cart_check.sh` — optional BASIC cartridge-window guard: cosim
  `JUKU_CART` plus HDL D8/D22 expose `jbasic11.bin` at `0x4000`.
- `sync/basic_launch_probe.py` — bounded cosim diagnostic for a monitor command
  path into the BASIC cartridge; default `JUKU_KEYS=B`. Monitor 3.3 compares
  `jbasic11.bin` with the legacy BAS0-3 image, validates the cartridge header
  from high ROM, copies from the `0x4000` cartridge window to low RAM at
  `0x0100`, and later reaches the same zero-filled `0x4000` RAM execution
  boundary. The report also records that the cartridge body from `0x0200` is
  copied into matching low RAM for 7,680 bytes with 0 body mismatches, while
  the low entry/control area has 14 byte mismatches, plus the MAME Monitor
  3.3/JBASIC compatibility warning and the BASIC images' absolute
  `JMP 0x0107` entry.
- `scripts/report_basic_low_stub_inspection.py` — generated inspection of that
  14-byte low-stub boundary. It groups the sparse deltas, records the
  `0x0100` stack-pointer patch to `0xFFFE`, includes the Monitor 3.3 high-ROM
  header/copy/jump disassembly, and keeps the remaining cartridge-BASIC work
  focused on the post-`0x0100` handoff through low workspace/control bytes.
- `sync/basic_factory_command_probe.py` — bounded cosim matrix for the Baltijets
  doc 003 factory BASIC `A` command. It runs all vendored public monitor ROMs
  against both BASIC payload shapes and records that Monitor 3.3 reaches the same
  zero-filled RAM boundary, while no tested pairing reaches BASIC
  banner/`READY`.
- `sync/basic_entry_probe.py` — bounded cosim diagnostic rejecting the direct
  reset-ROM theory for the same BASIC images; both direct runs stop at
  `PC=0x0038` after the first video write to `0xFFFE`, with no BASIC prompt.
- `sync/prom_fallback_check.sh` — fast HDL consistency guard for the exported
  reconstructed D6/D8 PROM fallback images. It compares
  `ref/reconstructed-proms/` against the actual `decode_prom` and `re3_prom`
  modules in `hdl/devices.v`.
- `scripts/report_re3_firmware_inspection.py` — generated inspection for the
  owner-scan К155РЕ3 `.113`/`.117` programming-table excerpts under
  `ref/firmware/`. It guards their hashes and shape while preserving the
  current conclusion that they are not the processor-module D8 `.039` or D94
  `.092` contents.
- `sync/beeper_check.sh` — D57 PIT channel 1 digital beeper-source guard:
  programmed `OUT1` toggles the traced `SOUND` net.

## Status

The LVS/boot path is no longer a small fixture: `juku_top` is the working
LVS-checked model and the guards above cover connectivity, boot behavior,
value-level lockstep, cosim FDC sector-read/prompt scaffolding, HDL WD1793
synthetic-sector behavior, a bounded `juku_top` FDC-path diagnostic, and
runnable video readout/raster geometry. The remaining
high-fidelity boundaries are disk-backed FDC in `juku_top`, the user-visible
jmon33 command prompt, HDL coverage of the pinned EKDOS disk-backed BASIC prompt
path, the analog
speaker/current check, dumped PROM contents, and the D94 `.092` РЕ3/АГ3-gated
physical video slot timing.
