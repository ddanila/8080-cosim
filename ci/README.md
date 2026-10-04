# Hosted CI budgets

Every Actions job has a ten-minute hard deadline; shell steps have a
five-minute deadline except the measured seven-minute TTL boot, capped at
eight minutes. Timeouts fail the check: they are never converted into
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
It supplies its own ROM, so documentation and reference-image changes do not
need those two jobs. Its checkout includes only the cosim sources and test.

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
| Windows host | Listed host, packaging and guide changes, or manual dispatch; reproducible PE/package checks and Windows Server 2022 runtime checks; public release publication on `master` |
| Smoke kit | Listed simulator/host/container inputs on `master`, or manual dispatch; publishes the downstream simulator container |

Exact path filters and assertions are in [the workflows](../.github/workflows).
Within an invoked HDL workflow, unknown paths select all lanes; paths excluded
by the workflow trigger do not reach that selector. Tag pushes force all lanes.
The Windows runtime checks do not establish physical serial or Windows 95
qualification. Report checks verify their listed artifacts; they do not amount
to a semantic review of every document.

## Coverage kept local

- Network ROM: CI retains the complete fast cosim ABI/fault matrix, elaborates
  both structural ROM testbenches, and executes the focused video POF guard.
  Run the complete firmware/ABI/NetDisk structural matrix locally with
  `bash sync/network_first_rom_hdl_check.sh` (without `--ci`).
- Rev B TTL boot: CI retains the default 400-write framebuffer comparison
  against cosim. It took roughly seven minutes, so it has the sole eight-minute
  step exception (still a ten-minute job ceiling). To reproduce it, run
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
Missing tools skip the deep guard with a warning. Run
`sync/cosim_check.sh` manually when the hook did not run it.

The hook also runs `scripts/ci_gate.sh` before the deep guard. With an
available, authenticated `gh`, it queries the latest 15 `master` runs and
blocks a push if a workflow's newest conclusive completed run in that window
has conclusion `failure`. Running, cancelled and skipped runs are ignored;
missing authentication or a failed query produces a warning and skips this
check. It neither waits for running jobs nor establishes that every workflow
passed at the current commit. Inspect the relevant commit's runs separately.

When a bounded check outgrows its budget, inspect step timings first. Split
independent checks or add a meaningful, explicitly labelled smoke profile;
keep the full local command and assertions intact. Do not raise the deadline
or accept a timed-out simulation as successful.
