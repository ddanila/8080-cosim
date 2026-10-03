# Verification entry points

`sync/` contains the LVS comparison, fast behavioral regressions, and focused
subsystem/deep diagnostics. Generated reports under `docs/` record evidence from their source data and
checks; use the subsystem guides for implementation contracts.

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
runs stock, stock-assisted JF15, reset-safe stock JF17, C8/JF16, disk, console,
reconnect, recovery,
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

The native Windows Juku host desk gate is:

```sh
sync/jukuhost_win32_check.sh
```

It tests the embedded stock/C11/C12 catalog, strict INI and serial selection,
Win32 COM behavior through an API shim, two byte-identical Open Watcom GUI
builds, the exact legacy-safe PE import/resource boundary, and the exact
self-contained package. It runs the fast compiled self-test under Wine when
Wine is available and reports an explicit skip otherwise. The longer,
developer-invoked `sync/jukuhost_win32_wine_e2e.sh` maps Wine `COM1` through a
PTY bridge and runs the actual PE against stock/JF17, C11, and C12 co-simulation; it
is deliberately outside the ordinary CI gate. See
`docs/windows-jukuhost-client-wine-acceptance.md` and
`docs/windows-jukuhost-client-desk-acceptance.md`.
[Windows 95 guest execution](../docs/windows-jukuhost-client-win95-acceptance.md)
has also passed against the simulator. Physical serial qualification on
Windows still requires the real adapter and board.

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

The checks above cover these boundaries:

| Area | Coverage |
| --- | --- |
| CPU and boot | Real-ROM boot/framebuffer; independent 8080 ALU, flag and control checks; C/vm80a instruction differential; C/HDL bus-event and interrupt-acknowledge agreement. |
| Disk and FDC | Raw geometry and deterministic C/HDL command/event comparisons, including DRQ/lost-data boundaries, Type-I timing, Force Interrupt, deleted records and track streams. See [FDC readiness](../docs/fdc-readiness.md) for model limits. |
| Video and device slices | Raster/readout, beeper, USART, IE7/IE10 counters, AG3 trigger/timing and BASIC cartridge behavior. |
| Jukuravi | D0 fault/session checks, Nano transport/reset/liveness guards, optional AVR compile, and D2 upload/readback/run and heartbeat handling. See [Jukuravi](../spinoffs/jukuravi/README.md) for the hardware boundary. |
| JukuPoly | Chord, compiled-pattern and library players; cycle/memory/file-size baselines and deterministic WAV checks. See [JukuPoly](../spinoffs/jukupoly/README.md). |
| READY path | Physical D2 `.037` open-collector polarity through the D30 latch; this does not establish complete WAIT timing. |
| Network ROM | Artifact freshness and ABI, locale, transport, telemetry, video and boot checks through C12. Structural HDL checks include C4 boot, C9–C12 ABI, the C9/C10 POF boundary and a CRC-checked NetDisk-v3 DMA record; bounded CI profiles run a subset. See [network ROM](../spinoffs/jukuravi/network-rom/README.md). |

`sync/cosim_check.sh` is slower than the others (it drives `juku_top` to ~20 ms
of simulated boot); see `docs/cosim-runtime-reference.md`. Activate the tracked
hooks once per checkout with `git config core.hooksPath .githooks`. Before a
push, the hook blocks on the newest conclusive failed master workflow, then runs
the deep cosim guard when `hdl/`, `cosim/`, or `roms/` changed. `CI_GATE=off`
overrides only the remote-CI check; `git push --no-verify` bypasses the complete
hook and should be reserved for a deliberate, documented exception.

See [CI budgets and local-only coverage](../ci/README.md) for workflow
selectors, bounded profiles, and checks that require a local run.

After changing `kicad/juku.board.json` or report inputs, run
`scripts/regen_all.sh` for its selected fast report set. Add `--deep` for the
listed HDL/cosim report writers. Add `--placement` to run the FDC upper/lower
assembly placement writers; this requires `pcbnew`, Pillow, and their materialized
photo inputs. It refreshes their Markdown, JSON, and overlay images. For example,
`scripts/regen_all.sh --placement --check` checks their freshness along with the
fast report set.

Also run a changed report's own command when it is outside these lists. These
options do not refresh every generated report or execute the uninterrupted
Verilator prompt runs.

`--check` uses `git diff` against the index for tracked files under `docs/`,
`ref/`, and three named Rev A candidate reports. It includes pre-existing
unstaged edits in those paths and excludes staged changes and untracked files.
Review `git status --short` and both unstaged and staged diffs before committing
and pushing regenerated artifacts.

## Simulator compatibility

The current `juku_top_tb` build fails under the installed Verilator 5.032:
`hdl/devices.v` uses named-fork `disable` statements in the AG3 pulse
scheduler that this simulator rejects. This affects the reset-driven cursor,
EKDOS and JBASIC reruns. The [cursor report](../docs/jmon33-hdl-cursor-probe.md)
records the build error. The Icarus first-write guard still passes; it does
not establish either full prompt boundary.

Committed Verilator prompt reports retain their recorded runtime evidence.
The ordinary prompt guards check those reports; use their deep options to
verify current-source execution after resolving simulator compatibility.

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

- `reference_artifact_check.sh` verifies the checksum manifests in
  `ref/baltijets-tech-docs`, `ref/ekdos-source`, `ref/extracted-software`,
  `ref/firmware`, `ref/reconstructed-proms`, `ref/reconstructed-firmware`,
  `ref/wd1772-vg93`, and `ref/datasheets`. It also requires 52 owner-board and
  26 factory-assembly photos to be materialized JPEGs. It does not inspect
  photo content or verify photographed continuity. Physical PROM captures have
  their own manifest: `(cd ref/physical-proms && sha256sum -c SHA256SUMS)`.
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
wiring or the remaining connectivity of D96, D99, D100 and D101; those are
fabrication-release blockers tracked in [the FDC handoff](../docs/fdc-hardware-handoff.md)
and `PLAN.md`. D2 itself is no longer
missing: its validated physical table and measured D0/READY path are adopted,
and the X1.107B/R1 `H` handoff belongs to D105/D13. D30 provides the
common asynchronous `STB` path to D38, with R5.
