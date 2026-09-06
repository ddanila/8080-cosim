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

## Coverage kept local

- Network ROM: CI retains the complete fast cosim ABI/fault matrix, elaborates
  both structural ROM testbenches, and executes the focused video POF guard.
  The complete firmware/ABI/NetDisk structural matrix took 25m48s in run
  `33953312773`; run it locally with
  `bash sync/network_first_rom_hdl_check.sh` (without `--ci`).
- Rev B TTL boot: CI retains the default 400-write framebuffer comparison
  against cosim. It took roughly seven minutes, so it has the sole eight-minute
  step exception (still a ten-minute job ceiling). To reproduce it, run
  `REVB_BOOT_PHASE=ttl bash spinoffs/minimal-vga/sim/revb_boot_check.sh` locally
  with the pinned tv80 core initialized.
- Rev B tier suite: `--ci` runs behavioral card, bus, serial, ROM-system,
  bring-up and video checks, with 1000-write decode-mode boot prefixes. Hosted
  CI splits these into independent `REVB_CI_GROUP=cards` and `system` matrix
  jobs; a local `--ci` invocation defaults to both. The default
  `bash spinoffs/minimal-vga/sim/revb_tier_suite.sh` retains full GAL synthesis,
  physical PCB, DRC and manufacturing-release checks with Galette/KiCad.
  A green hosted run does not qualify manufacturing release.
- The existing deep cosim/full-banner and hardware/endurance checks remain
  outside hosted CI.

When a bounded check outgrows its budget, inspect step timings first. Split
independent checks or add a meaningful, explicitly labelled smoke profile;
keep the full local command and assertions intact. Do not raise the deadline
or accept a timed-out simulation as successful.

The September 2026 failures also exposed a missing JukuPoly PCM manifest entry
and a missing `cpmtools` installation. Both are covered by the corrected
workflow; manifest validation now runs in generic CI even when HDL is skipped.
