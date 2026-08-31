# Verification entry points

`sync/` contains the LVS comparison, fast behavioral regressions, and focused
subsystem/deep diagnostics. Reports under `docs/` are evidence outputs, not
independent specifications.

## Connectivity

```sh
sync/check.sh
```

The script regenerates the KiCad schematic from `kicad/juku.board.json`,
elaborates `hdl/juku_top.v` with Yosys, and compares mapped endpoint
partitions. It uses a real KiCad netlist when compatible `kicad-cli` is
available and the board JSON directly otherwise.

Placement-only footprints, unnetted pins, analog passives, and explicit
simulation-only ports are outside this result. Run the check for the current
mapped-instance and net totals.

Physical supply ports such as the 8080's GND, -5 V, +5 V, and +12 V pins are
also excluded from logic LVS by an explicit `POWER_ONLY` list. Their package
roles and board nets remain present in the source schematic and are checked by
the include-power ERC and dedicated power-readiness reports; tying Verilog
logic constants cannot validate real voltage rails.

Key files:

- `lvs.py` — comparison and diagnostics.
- `netlist_from_kicad.py`, `netlist_from_yosys.py`,
  `netlist_from_board.py` — normalizers.
- `map.json` — refdes/instance and physical-pin/logical-port mapping.
- `provenance.py` — source annotation summary for `board.json`.

## Fast behavioral checks

The complete native-Linux production-host promotion gate is:

```sh
sync/jukuhost_m2_check.sh
```

It compares the frozen Python-era oracle with the sole supported C host, then
runs stock, stock-assisted JF15, C8/JF16, disk, console, reconnect, recovery,
wrapper, and current network-ROM fault regressions. See
`docs/portable-c-host-m2-acceptance.md` for the accepted result and exact
platform-port boundary.

The retained C8 rollback and separately named C9/C10 bounded-host gates are:

```sh
sync/jukuhost_c8_cosim_check.sh
sync/jukuhost_c9_cosim_check.sh
sync/jukuhost_c10_cosim_check.sh
```

The C9/C10 gates use only the production N4 console PTY and exercise host
replacement without RESET. C10 additionally checks Port C/POF status and
`DIAG VIDEO` through the production host.

The complete Pocket8086/DOS desk gate is:

```sh
sync/jukuhost_dos_check.sh
```

It verifies the locally vendored Open Watcom toolchain, builds the 16-bit host
twice byte-identically, runs its self-test under DOSBox-X, and exercises the
actual EXE through emulated COM1 against stock 9,600-baud Janet and current C8
19,200-baud Fastboot/NetDisk/N4. See
`docs/portable-c-host-m2.2-dos-acceptance.md`. Physical Pocket8086 timing and
CS00015 behavior remain the separate M2.3 gate.

```sh
sync/boot_check.sh
sync/i8080_check.sh
sync/i8080_vm80a_diff_check.sh
sync/cosim_check.sh
sync/inta_bus_check.sh
sync/juk_disk_check.sh
sync/fdc_check.sh
sync/video_timing_check.sh
sync/video_readout_check.sh
sync/jukuravi_d0_check.sh
sync/jukuravi_nano_check.sh
sync/jukupoly_three_voice_check.sh
sync/jukupoly_check.sh
sync/jukupoly_library_check.sh
sync/jukupoly_baseline_check.sh
sync/jukupoly_wav_check.sh
sync/beeper_check.sh
sync/serial_check.sh
sync/ie7_check.sh
sync/ie10_check.sh
sync/ag3_check.sh
sync/basic_cart_check.sh
sync/d2_ready_path_check.sh
sync/network_first_rom_abi_check.sh
sync/network_first_rom_hdl_check.sh
```

These cover the real-ROM boot/framebuffer path, an independent and mostly
exhaustive 8080 ALU/flag/control guard (`i8080_check.sh`), a one-instruction
C/vm80a differential over every opcode and architectural flag combination
(`i8080_vm80a_diff_check.sh`), typed
memory/I/O bus-event agreement between `juku_top` and the C emulator
(`cosim_check.sh`, cosim-referenced), focused end-to-end `CD low high` interrupt
acknowledge agreement (`inta_bus_check.sh`), raw disk geometry, and a generated C/HDL
FDC differential over deterministic command/event vectors with isolated writable
images.  The five [`JukuPoly`](../spinoffs/jukupoly/README.md) guards build and
cycle-qualify the simple chord, compiled-pattern player, and reusable disk-song
library player; lock the OPL work's hot-loop, cycle, memory, file-size, and WAV
baseline; then render the
chord's D57 Mode-0 writes into a
deterministic 16-bit WAV whose format, duration, pulse level, and staggered
voice entrances are checked without committing generated audio.
That FDC differential includes exact read/write DRQ boundaries, normal/deleted
single and multiple writes, Read Address, and complete Read/Write Track streams.
The bounded WD1793
subset also includes Type-I physical-head,
update/verify/status, D95-selected 3/6/10/15 or 6/12/20/30 ms step timing plus
15/30 ms settle timing, and
15-idle-index head-unload semantics plus the Type-II/III E-flag 15 ms delay and Type-II multi-record,
streaming one-byte DRQ/LOST-DATA service semantics, completion/status and all Type-IV Force Interrupt event semantics, Read Address, and reconstructed
one-revolution MFM Read Track plus index-gated, preloaded writable-track formatting
and optional cross-run deleted-mark companion metadata,
raster/serializer behavior,
the Jukuravi stack-free D0 diagnostic ladder (including injected CPU-bad and
stuck-TX paths), its host-session round trip, guarded DTR restart, bounded
pre-banner retry policy, and the Nano bridge's byte-transparent bounded
pump, rollover-safe isolated startup reset, active-low D5 hold/reassert gate,
optional exact AVR compile, and the cumulative D2 loader's guarded chunk/write/
readback/run API plus real host-CLI file orchestration through cosim, including
exact upload logs, versioned/consecutive post-RUN heartbeat acceptance, and
bounded heartbeat-timeout evidence; its host-control unit separately proves
default-off real-port recovery budgets and non-retry boundaries. The same
Nano/host guards cover default-off rollover-safe RESET/clock/`-MRDC`
observation, exact liveness framing, durable decoding, and the evidence-bearing
no-banner boundary, plus beeper and USART slices,
the full standard К555ИЕ7/74LS193 asynchronous
load/clear, bidirectional-count, terminal-pulse and cascade contract, and the
К555ИЕ10/74LS161 direct-clear/synchronous-load contract plus D103's traced
`0011`-preset modulo-13 feedback loop, and the BASIC cartridge window.
The focused АГ3 guard covers the dual К155АГ3/74123 trigger/clear/complement,
retrigger-inhibit and pulse-extension contract plus D56's photo-proved grounded
A inputs and traced board RC timing parameters.
`d2_ready_path_check.sh` separately guards the physical `.037` open-collector
raw polarity through the D30 READY latch; it does not claim complete WAIT timing.
`network_first_rom_abi_check.sh` rebuilds and checks the exact historical
images through C8 plus the C9/C10 ABI 1.4 transport, telemetry, locale and boot
matrices. `network_first_rom_hdl_check.sh` boots the exact C4 production ROM
to its target-ready marker, retains its structural boundaries, and also proves
the C9/C10 ABI, the dedicated C9-blank/C10-visible POF boundary, and one
CRC-checked NetDisk-v3 DMA record in structural HDL.

`sync/cosim_check.sh` is slower than the others (it drives `juku_top` to ~20 ms
of simulated boot); see `docs/cosim-runtime-reference.md`. Activate the tracked
hooks once per checkout with `git config core.hooksPath .githooks`. Before a
push, the hook blocks on the newest conclusive failed master workflow, then runs
the deep cosim guard when `hdl/`, `cosim/`, or `roms/` changed. `CI_GATE=off`
overrides only the remote-CI check; `git push --no-verify` bypasses the complete
hook and should be reserved for a deliberate, documented exception.

CI is split by relevance: `ci.yml` (always-on, syntax + doc consistency),
`reports.yml` (report-freshness + PROM/photo validation, gated on generator and
data paths), and `hdl.yml` (LVS + behavioral boot, gated on `hdl/`, `cosim/`,
`roms/`, `sync/`, `media/`, and the board JSON).

After changing `kicad/juku.board.json`, timing-relevant HDL, or any
`report_*.py`, run `scripts/regen_all.sh`; add `--deep` when HDL/cosim behavior
changed. Commit every resulting artifact, and use `--check` for a CI-style
nonzero exit when generated `docs/` or `ref/` output drifts.

## Current user-visible oracles

- `ekdos_fdc_probe.py` — ROMBIOS `TDD` to EKDOS `A>` in the C oracle.
- `juku_top_fdc_prompt_check.sh` — committed uninterrupted HDL EKDOS prompt
  evidence; set its documented deep-rerun option to refresh the long trace.
- `ekdos_jbasic_command_probe.py` and `juku_top_jbasic_prompt_check.sh` — disk
  BASIC command and uninterrupted HDL `READY` evidence.
- `jmon33_ready_probe.py`, `jmon33_command_probe.py`, and
  `jmon33_hdl_probe.sh` — Monitor 3.3 reference and structural checks.
- `jmon33_checkpoint_deep_check.sh` — long checkpoint-resumed cursor/A/B/FDC-T
  checks, kept out of push CI because of runtime. Its superseded cursor
  intermediate is written to a temporary file.
- `jukuravi_d55_clock_audit.sh` — slow full-ROM T31 negative control plus T34
  clean, D55-data, D54-clock, D56-clock, and D9-select structural fault matrix.
- `janet_netboot_check.sh` — frozen Python-era fixture regression: five
  parallel stock-ROM NetBios clients served only through simulator D11 PTYs;
  proves Janet retry/turn handling, exact 52-sector system installation at
  `B400h`, and the `CA00h` cold-start handoff for every `media/system/*.BIN`
  image. It is not an operational host command.

Checkpoint load/resume tools remain useful for narrowing regressions, but their
old intermediate report files are not project milestones. The uninterrupted
reset-to-prompt reports are the stronger evidence where both exist.

## Reference and generated-evidence checks

- `reference_artifact_check.sh` verifies checksums for vendored factory,
  firmware, media, and WD1772/VG93 references.
- Scripts under `scripts/report_*.py` regenerate constraint and boundary
  reports used by CI.
- `system_bus_connector_check.sh` checksum-guards the recovered `.106.103`
  XP and `.031.011` system drawings, proves the shared X1 signal map, and
  preserves their incompatible power-contact maps as a safety boundary.
- `dgsh5_106_106_check.sh` reconstructs the photographed 2 KiB factory BASIC
  table, guards its single archive correction, and proves exact cartridge-page
  identity.
- `keyboard_matrix_check.sh` checksum-guards all three `.104.015` factory
  frames, regenerates the complete 15-by-6 keyboard/X1 transcription, and
  proves every cosim ASCII tuple against it.
- `dgsh5_109_009_e3_check.sh` checksum-guards all 23 recovered processor
  schematic frames and regenerates the reviewed sheets-1/2 divergence plus
  complete sheet-3 circuit index against adopted board endpoints.
- `d15_d16_firmware_lineage_check.sh` checksum-guards the factory census,
  archival EPROM halves, ROM candidates, and owner overview while proving the
  unique EktaSoft 3.7 byte identity without claiming fitted-chip contents.
- `scripts/check_documentation_consistency.py` ensures user-facing status and
  package hashes do not contradict the active design blockers.

## Limits

The FDC, USART, PIT/PPI/PIC, memory timing, and video helpers are scoped to
guarded Juku behavior. They are not complete drop-in models of every original
chip. Most importantly, behavioral success cannot supply the remaining D94
wiring or the functional connectivity of the 3 still-open FDC-support ICs; those are
fabrication-release blockers tracked in `PLAN.md`. D2 itself is no longer
missing: its validated physical table and measured D0/READY path are adopted,
and native/.009 evidence now closes D30 section B's X1.107B/R1 `H` handoff.
