# Verification entry points

`sync/` contains the LVS comparison, fast behavioral regressions, and focused
subsystem/deep diagnostics. Generated reports under `docs/` record evidence
from their source data and checks; use the subsystem guides for implementation contracts. Run the commands
below from the repository root.

## Connectivity

Requires Python 3 and Yosys. KiCad CLI enables the schematic round trip;
KiCad's Python module enables the additional silkscreen-overlap check.

```sh
sync/check.sh
```

The script regenerates the KiCad schematic from `kicad/juku.board.json`,
elaborates `hdl/juku_top.v` with Yosys, and compares mapped endpoint
partitions. A successful KiCad XML export enables the schematic round trip.
If the CLI is missing or the export fails for any reason, the script compares
the board JSON directly instead. Check the printed `real KiCad round-trip`
or `KiCad-free` mode: a fallback pass does not validate schematic export.
The command rewrites the schematic and HDL JSON, and the KiCad XML when exported.

It also checks silkscreen glyphs and board population, conditionally checks
silkscreen overlap when KiCad Python is available, and prints a provenance
summary. These additional checks do not establish routed connectivity or DRC.

Placement-only footprints, unnetted pins, analog passives, and explicit
simulation-only ports are outside this result. The comparison also drops HDL
constants and nets with fewer than two retained mapped endpoints. A pass does
not prove constant ties or no-connect dispositions. Run the check for the
current mapped-instance and net totals.

Physical supply ports such as the 8080's GND, -5 V, +5 V, and +12 V pins are
also excluded from logic LVS by an explicit `POWER_ONLY` list. Their package
roles and rail nodes remain in `kicad/juku.board.json`. The default schematic
generator skips nets tagged as power; use its `--include-power` output for
the ERC power audit. Dedicated power-readiness reports check rail assignments
separately; tying Verilog logic constants cannot validate real voltage rails.

Key files:

- `lvs.py` — comparison and diagnostics.
- `netlist_from_kicad.py`, `netlist_from_yosys.py`,
  `netlist_from_board.py` — normalizers.
- `map.json` — refdes/instance and physical-pin/logical-port mapping.
- `provenance.py` — source annotation summary for `board.json`.

## Behavioral checks

These entry points include focused regressions, complete platform gates, and
deep simulation. Their runtimes differ; use the
[CI coverage guide](../ci/README.md) for the bounded CI profiles.

The complete native-Linux production-host promotion gate is:

```sh
sync/jukuhost_m2_check.sh
```

It compares the frozen Python-era oracle with the sole supported C host, then
runs stock, stock-assisted JF15, stock-JF17 recovery, C8/JF16, disk, console,
reconnect, media, wrapper, and current network-ROM fault regressions.

The JF15 checks use [vendored fixtures](../tests/fixtures/jukuhost-v15/README.md)
by default. JF17 recovery instead requires the sibling `../cpm-plus-juku`
checkout, or `CPM_PLUS_JUKU_ROOT`, with these files under `out/`:
`cpm-plus-juku-stock-recovery-system.bin`,
`cpm-plus-juku-stock-recovery-fastboot-v17.bin`, and `cpm-plus-juku.img`.
Missing artifacts fail the test; they are not a skipped qualification.
After building `build/jukuhost` with `sync/jukuhost_linux_build.sh`, rerun
only the stock-JF17 target-reset test:

```sh
python3 tests/jukuhost_stock_recovery_cosim_test.py
```
See [native host acceptance](../docs/portable-c-host-m2-acceptance.md) for the
accepted result and exact platform-port boundary.

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
actual EXE through emulated COM1 against stock 9,600-baud Janet and retained C8
19,200-baud Fastboot/NetDisk/N4. See
[DOS acceptance](../docs/portable-c-host-m2.2-dos-acceptance.md). Physical Pocket8086 timing and
CS00015 behavior remain the separate M2.3 gate.

The native Windows Juku host desk gate is:

```sh
sync/jukuhost_win32_check.sh
```

It tests the embedded stock/C11/C12 catalog, strict INI and serial selection,
Win32 COM behavior through an API shim, two byte-identical Open Watcom GUI
builds, the exact legacy-safe PE import/resource boundary, and the exact
self-contained package. It runs the fast compiled self-test when `wine`,
`wineboot`, and `xvfb-run` are available; otherwise that self-test is explicitly
skipped. The longer,
developer-invoked `sync/jukuhost_win32_wine_e2e.sh` maps Wine `COM1` through a
PTY bridge and runs the actual PE against stock/JF17, C11, and C12 co-simulation; it
is deliberately outside the ordinary CI gate. The wrapper exits zero with
`SKIP` if `wine`, `wineboot`, `xvfb-run`, or `socat` is absent. Missing
generated CP/M payloads or disk images fail the harness instead. See the
[Wine rerun instructions](../docs/windows-jukuhost-client-wine-acceptance.md#rerunning-the-current-source)
and [desk acceptance](../docs/windows-jukuhost-client-desk-acceptance.md).
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
sync/jukupoly_envelope_check.sh
sync/jukupoly_wav_check.sh
sync/jukupoly_pcm_check.sh
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
| JukuPoly | Chord, compiled-pattern and library players; cycle/memory/file-size baselines, envelope compatibility, packed-PCM playback and deterministic WAV checks. See [JukuPoly](../spinoffs/jukupoly/README.md). |
| READY path | Captured D2 `.037` raw-output polarity and D30 sampling in HDL, with asynchronous controls inactive; hardware timing and the complete WAIT path remain outside this bench. |
| Network ROM | Artifact freshness and ABI, locale, transport, telemetry, video and boot checks through C12. Structural HDL checks include C4 boot, C9–C12 ABI, the C9/C10 POF boundary and a CRC-checked NetDisk-v3 DMA record; bounded CI profiles run a subset. See [network ROM](../spinoffs/jukuravi/network-rom/README.md). |

`sync/cosim_check.sh` uses a default 30 ms simulated-time window and
130,000-event limit; a successful event verdict can stop it earlier. See
[the cosim reference](../docs/cosim-runtime-reference.md). Activate the tracked
hooks once per checkout with `git config core.hooksPath .githooks`. Before a
push, the hook checks the latest 15 `master` workflow runs and blocks on a
workflow whose newest conclusive result in that sample is `failure`. Unavailable
or unauthenticated `gh` skips that remote check with a warning. It then runs
the deep cosim guard when `hdl/`, `cosim/`, or `roms/` changed and both `cc`
and Icarus Verilog are available; missing tools produce a skip warning. `CI_GATE=off`
overrides only the remote-CI check; `git push --no-verify` bypasses the complete
hook and should be reserved for a deliberate, documented exception.

The remote-CI query uses GitHub CLI's selected repository. Set
`GH_REPO=ddanila/8080-cosim` when pushing so the hook checks the user's fork;
see [the local CI gate](../docs/development-workflow.md#local-ci-gate) for
its sampling limits.

See [CI budgets and local-only coverage](../ci/README.md) for workflow
selectors, bounded profiles, and checks that require a local run.

## Regenerating reports

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

Regeneration stops at the first failing command and leaves earlier outputs in
place. `--check` still runs the writers; it is not a read-only inspection.
Only after all selected commands succeed does it use `git diff` against the
index for tracked files under `docs/`,
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
  checks, kept out of push CI because of runtime.
- `jukuravi_d55_clock_audit.sh` — slow full-ROM T31 negative control plus T34
  clean, D55-data, D54-clock, D56-clock, and D9-select structural fault matrix.
  The current rerun stops in T31: bitmap `18` differs from the expected `08`
  because the D57 bit is also set. No T34 case is reached; see
  [the D55 audit](../docs/jukuravi-d55-diagnostic-audit.md) for the recorded
  earlier matrix and the current failure boundary.
- `janet_netboot_check.sh` — frozen Python-era fixture regression through
  simulator D11 PTYs. It boots the five vendored systems plus an optional
  external image, then checks automatic station discovery with a nondefault
  client. It verifies byte-exact staging and resident installation before the
  cold-start handoff. See [the NetBios notes](../docs/ekta37-netbios-notes.md)
  for layout, concurrency controls, and prerequisites; this is a regression
  entry point.

Use checkpoint load/resume tools to narrow regressions. Use uninterrupted
reset-to-prompt reports to establish the complete boot path.

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
  unique `ekta37.bin` (RomBios 3.43m, serial #0037) byte identity among its
  eight candidates without claiming fitted-chip contents.
- `scripts/check_documentation_consistency.py` ensures user-facing status and
  package hashes do not contradict the active design blockers.

## Limits

The FDC, USART, PIT/PPI/PIC, memory timing, and video helpers are scoped to
guarded Juku behavior. They are not complete drop-in models of every original
chip. Behavioral success does not close physical release blockers: D94's
hidden D0 load, the D96 continuity/clear boundaries, and remaining D99/D100
sheet continuations still require evidence. D101's selected write-data path
is source-closed; its physical continuity and waveform quality remain bring-up
checks. Use [the FDC handoff](../docs/fdc-hardware-handoff.md) and
[the active plan](../PLAN.md) for the exact current boundaries. D2’s validated physical table and measured D0/READY path are adopted,
and the X1.107B/R1 `H` handoff belongs to D105/D13. D30 provides the
common asynchronous `STB` path to D38, with R5.
