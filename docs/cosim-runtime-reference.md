# Deep cosim CPU-bus guard — reference

`sync/cosim_check.sh` is the deep VALUE-level guard. It runs `juku_top` (the LVS-checked
structural model) and compares its ordered CPU-bus activity against the C emulator (`cosim`).
The shared event vocabulary is memory read/write (`MR`/`MW`), I/O read/write (`IR`/`IW`), and
interrupt acknowledge (`IA`); address and data are checked for every event, with the acknowledge
address treated as don't-care. `cosim` is the authoritative reference: a straightforward 8080 +
flat-memory model, written independently and in a different language, whose framebuffer
`boot_check` already validates. LVS checks connectivity and `boot_check` checks sampled memory;
this checks the live transaction stream value-by-value.

## How it works

1. `cosim` boots the real `ekta37` BIOS and dumps `TYPE addr data` lines through
   `JUKU_BUS_TRACE`, bounded by `JUKU_BUS_TRACE_LIMIT`. Paired reads retain real 8080 low-byte-first
   order, while stack pushes retain the CPU's high-byte-first write order.
2. `hdl/sim/cosim_ctrace_tb.v` runs `juku_top`, classifies DBIN and WR edges from the decoded bus
   strobes, consumes the next expected event, and compares its type, address, and CPU-visible data.
   Interrupt acknowledges compare the supplied opcode while ignoring the electrically undefined
   address. The first mismatch is reported with full context.

```sh
sync/cosim_check.sh
```

Runtime is dominated by driving `juku_top` to ~20 ms of simulated boot (a few minutes), not by a
multi-hour full-banner run. `WINDOW` (ns) and `TRACE_LIMIT` (events) bound it. The default boot
necessarily covers `MR`, `MW`, `IR`, and `IW`; separate interrupt guards exercise the interrupt
path, while the trace format and checker also support `IA`.

## EktaSoft block-1 checksum convention

The boot ROM stores at `0x000A` the eight-bit additive sum of bytes
`0x000B..0x07FF`. This is the convention exercised by the checksum routine at
`0x03E0`; `cosim/trace.c` logs its computed/stored comparison. All five
official repository images satisfy it: EktaSoft 2.4/3.1/3.2/3.5/3.7 store
`7B`/`D3`/`8F`/`EE`/`1A`, respectively. The homebrew 4.3 image is the known
counterexample: it stores stale `F2` while its covered bytes compute to `57`,
so the boot harness applies its explicitly logged compatibility patch.

Jukuravi rung 5a deliberately uses these exact offsets rather than inventing a
second short-ROM convention. Its D15-only diagnostic reserves `0x000A`, starts
framed protocol tables at `0x0800`, and recomputes all 2,037 covered bytes at
runtime before touching the USART or RAM.

## Why it references cosim, not a second Verilog model

Until 2026-07-14 this guard locked `juku_top` against a second Verilog model, `juku_struct` (a
behavioral oracle). Comparing two independently-timed Verilog models made the verdict depend on
sub-cycle event ordering, which Icarus resolves differently across versions — the guard "passed on
Linux, failed on Mac" for the same commit. Referencing `cosim` removes the second model: every
divergence is now a real `juku_top`-vs-reference difference, reproducible on any host. The
`juku_struct` oracle and the old `cosim_diff_tb.v` were retired.

## Current state

The default 130,000-event run reaches `BTRACE-END`: `juku_top` matches `cosim` in event type,
address, and data throughout the bounded trace, including the BIOS RAM test at `0xD300`. There is
no accepted divergence baseline; a malformed/short reference trace, absent default event class,
mismatch, or missing verdict fails `sync/cosim_check.sh`.

Promoting the guard from reads alone to the complete typed bus immediately found a previously
invisible oracle defect: the C core produced the right final stack bytes but wrote the low byte
before the high byte. The 8080 actually decrements SP and writes high first, then decrements and
writes low. `i8080_push_stack` now follows that bus order, which is also pinned by the independent
CPU conformance test.

The previously reported read #115878 mismatch was real but its first diagnosis was incomplete.
Signal-level instrumentation established that CAS did pulse on the failing read. Two zero-delay
modeling errors made the result depend on simulator event ordering instead:

- the behavioral D53 scaffold asserted RAS only during Φ1 and released it before the Φ2/CAS column
  phase, whereas a 4164-class transaction keeps RAS active through CAS; and
- the РУ5 model committed writes on an unrelated synthetic `sclk` edge while CAS and WE happened
  to be low. When control transitions shared a timestep, the sampled condition varied with event
  order.

The corrected functional transaction holds RAS from the row phase through the CAS column pulse.
The РУ5 model now implements the asynchronous-DRAM rule directly: the latter falling edge of CAS
or WE strobes DIN, covering both early writes (WE first) and delayed/read-modify writes (CAS first).
The synthetic DRAM sampling-clock pin is gone. `hdl/sim/dram_unit_tb.v` exercises early, delayed,
and coincident control edges, immediate read-after-write, the physical row permutation, and
non-aliasing addresses; `sync/boot_check.sh` runs it in CI.

The write-strobe rule comes from the contemporary Mostek MK4564 64K×1 DRAM data sheet,
“Data Input/Output”: the later negative transition of WRITE or CAS strobes the DIN register;
early-write timing references CAS, while delayed-write timing references WRITE. That data sheet is
now vendored locally as the 4164-class AC-timing reference for the К565РУ5Г bank
(`ref/datasheets/mk4564-64kx1-dram.pdf`, interpretation in `ref/datasheets/k565ru5-pinout.txt`)
([manufacturer data sheet scan](https://www.minuszerodegrees.net/memory/4164/datasheet_MK4564-12.pdf)).

One further zero-delay hazard survived until it was traced with Icarus 13.0 (the newer local
toolchain; CI’s older Icarus scheduled around it, so the guard passed on Linux while dropping BIOS
RAM-test writes on this host). The row/column address is multiplexed onto the shared MA lines by a
zero-delay mux (D48–D51, `sel = phi1`), so MA can switch in the same timestep that RAS/CAS assert.
Sampling *live* MA at the raw strobe therefore captured a half-settled column whose value depended
on event ordering — writes and reads of the same cell used inconsistent columns, so the `AA` half of
the `0xD300` checkerboard read back the stale `55`. The РУ5 model now honours the data sheet’s
address/data set-up contract (tASR/tASC = 0, hold > 0: the address is valid *at* its strobe): it
latches the row at RAS and the column at CAS, and strobes DIN on the later of CAS/WE, capturing the
**settled** address/data a sub-nanosecond delta after each strobe. That delta only outlasts the
zero-delay settling and stays far inside the compressed phase; it is not the real 120–200 ns access.
The result is simulator-independent — the 130,000-event guard now reaches `BTRACE-END` on both Icarus
generations. See `hdl/devices.v` `dram_64kx1`.

This closes the runnable CPU-memory timing defect, not the complete historical video-slot timing.
The exact D36.12/.13 source, D36/R57 propagation delay, CPU/video arbitration schedule, and precise
DOUT turn-off point remain evidence boundaries. Until those conductors are traced, the zero-delay
functional model keeps the sampled bit available through the access window and the runnable video
path retains its simulation-only second port. Those limitations are tracked separately in
`docs/memory-timing-boundary.md` and `docs/video-slot-timing-audit.md`.
