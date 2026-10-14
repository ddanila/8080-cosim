# Hosted CI budgets

Actions jobs have a hard deadline of at most ten minutes; shell steps are
capped at five minutes except the Rev B TTL boot, capped at eight minutes. Timeouts fail the check: they are never converted into
passes. The always-on generic workflow validates these limits and the HDL
entrypoint manifest, with regression tests for both contracts.

The target is under five minutes per check. A lane containing several checks
may use up to ten minutes including checkout and tool installation. Path-based
selection and cancellation of superseded runs still apply. Scheduled and
manual `full` HDL runs mean **all bounded CI lanes**, not every local test.
The HDL schedule is daily at 03:23 UTC. It skips the lanes when the latest
successful scheduled run already checked the exact current commit; manual
`full` dispatch still selects all lanes. Manual `changed` compares `HEAD^`
with `HEAD`, and an unavailable change set selects all lanes.

The watched-write checkpoint test has its own workflow. Changes to `cosim/`,
its test, CI helpers, or workflow configuration run the same Linux/macOS
matrix; a weekly schedule and manual dispatch also exercise runner updates.
It supplies its own ROM, so reference-image changes and documentation outside
the watched directories skip those two jobs. Changes under `cosim/`, `ci/`,
or `.github/` trigger the matrix even when they only edit Markdown. Its checkout
includes only the cosim sources and test.

Generic CI retains Markdown links and release-status consistency on every
push. The consistency check also runs the automatic-completion freshness
audit, so a second invocation is unnecessary. Local links must stay within
the repository: references to sibling projects use source URLs so a developer's
extra checkouts cannot conceal failures on hosted runners.

## Workflow scope

| Workflow | Trigger and coverage |
| --- | --- |
| Generic | Every push and pull request; syntax, Markdown, evidence consistency, native Linux host, disassembly and board guards |
| HDL | Relevant source/input changes, tag pushes, daily schedule and manual dispatch; `hdl-ci.json` selects lanes after the workflow is triggered |
| Checkpoint | Relevant inputs, weekly Monday 04:43 UTC schedule and manual dispatch; watched-write checkpoint test on Linux and macOS |
| Reports | Listed generator/input changes and manual dispatch; generated-report freshness, PROM captures and photo evidence |
| Windows host | Listed host, packaging and guide changes on pushes to `master` or pull requests, plus manual dispatch; reproducible PE/package checks and Windows Server 2022 runtime checks; public release only for non-PR runs on `master` |
| Smoke kit | Listed simulator/host/container inputs on `master`, or manual dispatch; publishes the downstream simulator container |

Exact path filters and assertions are in [the workflows](../.github/workflows).
Within an invoked HDL workflow, unknown paths select all lanes; paths excluded
by the workflow trigger do not reach that selector. Tag pushes force all lanes.
The Windows runtime checks do not establish physical serial or Windows 95
qualification. Report checks verify their listed artifacts; they do not amount
to a semantic review of every document.

## Coverage kept local

- Native host: generic CI runs `sync/jukuhost_linux_check.sh`, covering the
  build, configuration, PTYs, vendored JF15 boot/delay, reconnect and Python-host
  retirement checks. The complete `sync/jukuhost_m2_check.sh` remains a local
  promotion gate; generic CI does not execute its five-system stock sweep,
  JF17 target-reset recovery or C8 host co-simulation. See
  [verification entry points](../sync/README.md#behavioral-checks) for the
  separate commands and JF17 artifact prerequisites. The network-ROM ABI/fault
  matrix runs in its selected HDL lane.
- Network ROM: CI retains the complete fast cosim ABI/fault matrix, elaborates
  both structural ROM testbenches, and executes the focused video POF guard.
  Run the complete firmware/ABI/NetDisk structural matrix locally with
  `bash sync/network_first_rom_hdl_check.sh` (without `--ci`).
- Rev B TTL boot: CI retains the default 400-write framebuffer comparison
  against cosim, with the sole eight-minute step exception and a ten-minute
  job ceiling. To reproduce it, run
  `REVB_BOOT_PHASE=ttl bash spinoffs/minimal-vga/sim/revb_boot_check.sh` locally
  with the pinned tv80 core initialized.
- Rev B tier suite: `--ci` runs behavioral card, bus, serial, ROM-system,
  bring-up and video checks, with 1000-write decode-mode boot prefixes. Hosted
  CI splits these into independent `REVB_CI_GROUP=cards` and `system` matrix
  jobs; a local `--ci` invocation defaults to both. The default full suite
  includes GAL compilation, physical PCB, DRC and release-source checks.
  Some individual checks can skip missing tools, but R5.I7 fails without
  KiCad Python. See the [Rev B execution guide](../spinoffs/minimal-vga/docs/rev-b-execution-guide.md#verification-commands)
  for dependencies, generated outputs and the separate package-validation gate.
  A green hosted run does not qualify manufacturing release.
- The existing deep cosim/full-banner and hardware/endurance checks remain
  outside hosted CI.

The tracked [pre-push hook](../.githooks/pre-push) runs the deep cosim guard
for pushes touching `hdl/`, `cosim/`, or `roms/` when `cc` and Icarus Verilog
are available. Git must be configured to use that hook (for example,
`git config core.hooksPath .githooks`); committing the file does not enable it.
The hook requires `git-lfs` and runs `git lfs pre-push` first on every push.
Missing Git LFS or a failed LFS upload check blocks the push before either guard.
Missing `cc` or Icarus Verilog skips the deep guard with a warning. Run
`sync/cosim_check.sh` manually when the hook did not run it.

The hook also runs `scripts/ci_gate.sh` before the deep guard. See the
[local CI gate contract](../docs/development-workflow.md#local-ci-gate) for
repository selection, failure handling and the limits of its recent-run sample.

When a bounded check outgrows its budget, inspect step timings first. Split
independent checks or add a meaningful, explicitly labelled smoke profile;
keep the full local command and assertions intact. Do not raise the deadline
or accept a timed-out simulation as successful.

## Extracted emulator dependency

Native jobs initialize only `third_party/dac-emulation` before compiling the compatibility sources. Its gitlink is a shared-model input for lane selection and the checkpoint, reports, and smoke-kit workflows. Generic CI runs `sync/emulation_check.sh`, a fast native check with no HDL or external images. Smoke-kit context preparation exports the pinned dependency and retains its license notices.

## RAVI refactor baseline

The `jukuravi-current` lane runs the clock-safe T34 diagnostic and the complete
T36 suite in three bounded steps: `sync/jukuravi_t36_check.sh contract`, `ram`,
and `raster`. Running the script without arguments still runs all three.
The contract group rebuilds and checks pinned ROM bytes, tests the host stream
boundary and protocol, verifies saved physical evidence, and executes the
current monitor through real host/PTY co-simulation with DRAM decay. The RAM
group retains the complete local sweep and injected bad-bit attribution. The
raster group retains both successful entry paths and the missing-return
negative control, using short test-only deadlines for the intentionally dead
target. Firmware, production timeouts, and qualified ROM bytes are unchanged.

The lane is selected for its actual host, builder, batch, RAM and raster inputs;
its dedicated test changes do not start the old diagnostic or network lanes.
Shared firmware/model changes remain conservative. Batch/local-RAM sources are
included in the workflow trigger as well as the selector. Documentation-only
changes select no lane. T28-T32 compatibility checks remain in the existing
regression lane; historical experiments beyond those need not all execute for
every refactor. T35's falsified refresh image is still a required negative
control within the T36 tests.

Before extracting shared RAVI components, preserve exact ROM builds, the
loader's reserved/load ranges, CALL return/state restoration, CRC-protected
stored commands, lost-RETURN replay without duplicate side effects, and idle
reattachment. The fast transport contract pins a wire fixture, every split of
that frame, corruption recovery, partial writes, bounded deadlines, descriptor
ownership, and the absence of an explicit DTR reset during normal open. This
does not prove that every USB driver leaves electrical DTR unchanged on open.

A new target needs its own ABI/ROM-map and bootstrap integration tests. In
particular, a 1715 backend must separately prove stackless early feedback,
2 KiB ROM fit, SIO/CTC initialization, and workspace verification before CALL.
Do not make the existing 8080 CPU/refresh expectations into Z80 requirements.
Saved physical evidence guards are not fresh bench runs, and emulator success
does not qualify new wiring or analog timing. The DOSRAVI repository owns its
separate DOS execution and file-transfer gates; neither wire protocol changes
as part of this preparation.

Local validation on 2026-10-14 passed T28, T34 and all three T36 groups, the
fast transport/DTR/heartbeat/liveness guards, 36 CI selector and timeout tests,
the manifest validator, and actionlint. The T36 groups took approximately
94 seconds (contract), 171 seconds (RAM), and 18 seconds (raster) on the local
machine; these measurements are not hosted-runner timing guarantees.

T28, T34 and all T36 groups were rerun successfully after rebasing onto the
pinned DAC Emulation 0.1.1 dependency. The current-monitor CI lane initializes
that submodule explicitly before compiling its emulator harness.
