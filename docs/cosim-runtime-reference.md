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

For a quick validation of the harness and progress output without claiming the
full deep guard:

```sh
WINDOW=200000 sync/cosim_check.sh
```

