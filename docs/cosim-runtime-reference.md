# Lockstep cosim runtime reference

The deep `sync/cosim_check.sh` guard is intentionally much slower than the boot
checks. It executes two independent models in lockstep and compares every read.

## Observed baseline

| Field | Observation |
| --- | --- |
| Date | 2026-07-10 |
| Host CPU | AMD Ryzen 7 PRO 3700U, 4 cores / 8 threads, 2.3 GHz reported maximum |
| OS | Linux 7.0.0-15-generic x86_64 |
| Simulator | Icarus Verilog / VVP 12.0 stable |
| Window | `1600000000` ns (the default) |
| Result | PASS; 9,292,763 reads, no divergence |
| VVP wall time | approximately 2 h 2 min |

VVP used one logical CPU at essentially 100% for this run. Treat the time as a
host-specific planning baseline, not a performance requirement: thermal state,
background load, simulator version, and HDL changes can move it materially.
For this host, a first approximation is about **4.6 seconds of wall time per
1,000,000 ns of requested window**, or `baseline × WINDOW / 1600000000`.

The testbench prints a milestone every 5% and the shell streams those lines.
Milestones make a live run observable and allow a better ETA after the first
few samples. Only 19 progress lines are emitted, so their overhead should be
negligible relative to millions of compared reads.

## 2026-07-12 overlay regression (resolution does not currently reproduce)

**2026-07-14 status:** the resolution below does not reproduce on the
committed tree with local Icarus Verilog 13.0: `sync/cosim_check.sh`
diverges at read #115878 (`D300`, structural `55`, oracle `AA`) at every
commit tested from the fix onward, and at read #57 (`D75C`, `FF`/`00`)
immediately before it. The passing windows recorded below therefore came
from a different environment or tree. Fixing this is the top actionable
item in `PLAN.md`.

Verified 2026-07-14 with `WINDOW=25000000 sync/cosim_check.sh` (about 3
minutes per run; the window covers both divergence points) on macOS with
Icarus Verilog 13.0 (installed 2026-06-29, so the same local toolchain
predates the recorded passes):

| Commit | Result |
| --- | --- |
| `5b94c73` (parent of the fix) | DIVERGE read #57, `D75C`, structural `FF`, oracle `00` |
| `90c04fb` (the recorded fix) | DIVERGE read #115878, `D300`, structural `55`, oracle `AA` |
| `f3dc06e` with `90c04fb`'s `juku_top.v` | same #115878 divergence |
| `b283266`, `2a2414b`, `2bf607f`, `4978252`, `616f3d8`, `1d9eb1e` (HEAD) | same #115878 divergence |

Both mismatch patterns look like BIOS RAM-test checkerboard bytes, and the
faster `sync/boot_check.sh` (final sampled memory, all levels versus cosim)
still passes at HEAD, so the disagreement is in the lockstep read path, not
the end state. The guard runs in no CI workflow, so it fails silently.

### 2026-07-14 root cause: read sample-and-hold timing-model mismatch

Instrumented tracing of the `D300` case (read #115878) shows the memory
contents are correct in **both** models: the BIOS RAM test writes `0xAA` to
`0xD300`, and both `juku_top`'s bit-sliced РУ5 array and the oracle's flat
bank hold `0xAA` afterward. The divergence is purely in the **read data
path**:

- `juku_top`'s `dram_64kx1` latches its read byte into `held` only on
  `negedge cas_n` (`& we_n`). On this fast read-after-write to the same cell
  no fresh CAS edge falls between the write commit and the CPU's DBIN
  capture, so `held` still carries the pre-write `0x55` while memory holds
  `0xAA`. (`cas_n` is the `d53_cas_sim` scaffold behind the un-traced
  D36.11/R57 shared-DRAM slot-timing boundary.)
- The oracle's `dram_bank_b`/`eprom_b` latch on `negedge rd_n` (the memory
  read strobe) instead, so at `D300` the oracle returns the correct `0xAA`.

So the two independently-written models sample read data on **different
events** (structural = CAS edge; oracle = read-strobe edge), and they go
stale on **different** reads. Making the structural DRAM read reload on the
master clock while CAS is low (mirroring the existing write-side fix in the
same module) fixed `D300` but exposed the mirror case four reads later at ROM
address `0x00CE`, where `juku_top` was then correct (`0x3e = ekta37[0xCE]`)
and the **oracle** served a stale `0x1b`. Making all four read latches
(structural ROM/DRAM, oracle ROM/DRAM) level/clock-sensitive instead only
reshuffled the first divergence earlier (to read #74). Throughout, every
variant kept `boot_check` byte-identical.

Conclusion: this is **not** a datapath or memory-contents bug in `juku_top`;
it is over-sensitivity of the read-by-read bus comparison to sub-cycle
sample-and-hold timing that differs between the two models and resolves
differently across Icarus versions (hence "passed on Linux, fails on Mac").
A durable fix is a harness decision, not a latch tweak — options:

1. Compare at a defined settled point (the CPU's captured byte at a fixed
   T-state, or memory contents) rather than the transient bus at
   `negedge dbin`.
2. Give both models one shared, deterministic read-timing model.
3. Complete the physical shared-DRAM slot timing (D41/D36/one-shot/mux
   continuity) so `cas_n` pulses per CPU read — this is the P0 evidence item
   already tracked in `PLAN.md`, after which the structural CAS-edge latch is
   correct on its own.

Reproduce the instrumented trace from
`scratchpad/cosim-dbg/tb_d300.v` in the working session, or add a windowed
`$display` on `negedge dtop.dbin` keyed on `dtop.BA == 16'hD300`.

## Original note: resolved 2026-07-12 overlay regression

On 2026-07-12, both the default run and a focused `WINDOW=200000000` run
diverged at read 743,463: bus address `D830`, structural byte `00`, oracle byte
`B7` (122,571,350 ns). The testbench forces `dtop.ready=1`, so this mismatch is
independent of the unresolved D105 pin-10 WAIT input. The faster boot guard
continued to pass. The late read path was reconciled by replacing the oracle's
invented PPI0 `PC0/PC1` mode
with the board-traced D6 address inputs `PC2/PC3/PC4`. A focused
`WINDOW=130000000` run then passed 789,879 reads—past the former failure—and
the added completed-write comparison found no persistent RAM mismatch.

For a quick validation of the harness and progress output without claiming the
full deep guard:

```sh
WINDOW=200000 sync/cosim_check.sh
```
