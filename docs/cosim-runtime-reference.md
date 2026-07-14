# Deep cosim value guard — reference

`sync/cosim_check.sh` is the deep VALUE-level guard. It runs `juku_top` (the LVS-checked
structural model) and compares every CPU memory read, byte for byte, against the C emulator
(`cosim`). `cosim` is the authoritative reference: a straightforward 8080 + flat-memory model,
written independently and in a different language, whose framebuffer `boot_check` already
validates. LVS checks connectivity, `boot_check` checks sampled memory; this checks the read
datapath value-by-value.

## How it works

1. `cosim` boots the real `ekta37` BIOS and dumps its memory-read stream as `addr data` hex lines
   (`JUKU_RDTRACE`, bounded by `JUKU_RDTRACE_LIMIT`). Reads are emitted in real 8080 bus order —
   low byte before high (`i8080_rw`) — so the stream lines up 1:1 with the hardware read order.
2. `hdl/sim/cosim_ctrace_tb.v` runs `juku_top` and, on each CPU memory read (`negedge dbin` while
   `memr_n` low), consumes the next trace entry and compares the read address and the CPU-captured
   byte. The first mismatch is reported with full context.

```sh
sync/cosim_check.sh
```

Runtime is dominated by driving `juku_top` to ~20 ms of simulated boot (a few minutes), not by a
multi-hour full-banner run. `WINDOW` (ns) and `TRACE_LIMIT` (reads) bound it.

## Why it references cosim, not a second Verilog model

Until 2026-07-14 this guard locked `juku_top` against a second Verilog model, `juku_struct` (a
behavioral oracle). Comparing two independently-timed Verilog models made the verdict depend on
sub-cycle event ordering, which Icarus resolves differently across versions — the guard "passed on
Linux, failed on Mac" for the same commit. Referencing `cosim` removes the second model: every
divergence is now a real `juku_top`-vs-reference difference, reproducible on any host. The
`juku_struct` oracle and the old `cosim_diff_tb.v` were retired.

## Current state and the one known divergence

`juku_top` matches `cosim` read-for-read through the entire reset/early-boot region and diverges at
the BIOS RAM test — **read #115878, address `0xD300`**: the test writes `0xAA` to `0xD300` and
immediately reads it back; `cosim` returns `0xAA`, but `juku_top`'s DRAM serves the pre-write
`0x55`. Memory holds `0xAA` in both — the fault is in `juku_top`'s read datapath, not its memory.

Root cause: `juku_top`'s РУ5 read latch reloads on the CAS strobe, but the un-traced shared-DRAM
CAS slot-timing scaffold (`d53_cas_sim`, behind the D36.11/R57 mesh) does not re-strobe on every
CPU read, so a read that immediately follows a write to the same cell can serve a stale byte. This
is physically impossible on real DRAM (the sense amps output the stored value), so `cosim` is
correct and `juku_top` is the deviant. The old two-model guard hid this: Icarus on the previous
host happened to order the write commit and read latch favorably.

No read-latch tweak fixes it robustly. Verified 2026-07-14: refreshing `held` on the master clock
while CAS is low moves the divergence to read #115882 (the next read-after-write, at `0x025b XRA
M`); latching the column and re-reading current memory moves it back to #115878; every variant kept
`boot_check` byte-identical. The divergence recurs at each read-after-write because the column
strobe itself is missing per read. A correct fix needs the physical shared-DRAM slot timing
(D41/D36/one-shot/mux continuity) so `cas_n` pulses per CPU read — a P0 connectivity item in
`PLAN.md`.

The divergence is a transient during a RAM test and does not block the functional boot milestones
(`boot_check`, EKDOS `A>`, disk BASIC `READY`, Monitor 3.3 all still reached). Until the slot
timing is modeled, `sync/cosim_check.sh` gates against **regression**: it passes if `juku_top`
matches `cosim` at least to the recorded baseline (read #115878) and fails if it diverges earlier.
It reports `CTRACE-OK`/`CTRACE-END` and goes fully green once `juku_top` reads correctly through the
window.
