# Deep cosim CPU-bus guard — reference

`sync/cosim_check.sh` is the deep VALUE-level guard. It runs `juku_top` (the LVS-checked
structural model) and compares its ordered CPU-bus activity against the C emulator (`cosim`).
The shared event vocabulary is memory read/write (`MR`/`MW`), I/O read/write (`IR`/`IW`), and
interrupt acknowledge (`IA`); address and data are checked for every event, with the acknowledge
address treated as don't-care. `cosim` is the authoritative reference: a straightforward 8080 +
flat-memory model, written independently and in a different language, whose framebuffer
`boot_check` already validates. LVS checks connectivity and `boot_check` checks sampled memory;
this checks the live transaction stream value-by-value.

The C CPU also records the address and byte of the last instruction actually
fetched, distinguishing an interrupt acknowledge from a memory opcode. This
supports execution-aware compatibility gates without mistaking embedded data
for code. The Juku trace checkpoint uses it to report total TPA opcode fetches
and separate Z80-prefix and undocumented-8080 counts for `0100h..99FFh`.
That numerical range deliberately also covers resident code in compact legacy
layouts, so it is a broad fetched-opcode safety gate rather than a per-program
code-size oracle.

For attributable CP/M transient stack measurements, `trace` has a separate
command-scoped interface. Send `SIGUSR2` immediately before submitting the
command: the emulator arms on the next `0100h` entry, excludes resident BDOS
excursions reached by `CALL 0005h` or the equivalent `JMP 0005h` tail call,
follows internal CALL/RET depth, and freezes the SP low-water result at the
top-level return. For a tail call it records the existing return address from
the transient stack, waits for that exact address rather than merely the next
instruction in the broad TPA address range, and mirrors the implicit unwind.
That return may be the page-zero warm-boot vector rather than another TPA
instruction; the tracer observes and freezes that non-TPA exit explicitly.
It also freezes a top-level tail return into a still-resident CCP inside the
broad TPA range, using semantic call depth rather than mistaking CCP execution
for continued transient stack use.
It also recognizes BDOS function 0 reached by either form as a non-returning
system reset. This distinction is required by ordinary DRI PL/M startup code
and small assembly utilities and prevents the
following CCP/BDOS stack from being charged to the completed transient. Send
`SIGUSR1` after the prompt to write the configured
`JUKU_CHECKPOINT_PREFIX` `.ram` and `.state` files without stopping execution.
Repeated requests are generation-counted, so one emulator session can measure
a complete command matrix. The state records entry SP, the anchor and low SP
of the deepest segment, minimum and maximum segment anchors, segment count,
observed bytes, explicit SP writes, measurement generation, and armed/frozen
status. `SIGTERM` and `SIGINT` retain the final stop-and-checkpoint behavior.
The CP/M Plus compiler comparison uses this interface for all six
representative programs and checks the exact results during its strict rebuild
gate; the DRI utility admission matrix additionally exercises function-0 and
BDOS-tail termination.

For CP/M Plus NetDisk analysis, set
`JUKU_CPM_DISK_TRACE=/path/to/disk-trace.txt`. With the documented C6 native
binding at `C000h`, the trace records every BIOS `READ` and `WRITE` entry plus
drive, track, translated sector, DMA address, and cycle count. Unlike the host
protocol log, this includes resident-cache hits and therefore exposes the
actual record-consumption sequence without changing target code or timing.
The fixed instrumentation addresses are `C027h`/`C02Ah` with state at
`C93Ah`; do not use it for another adapter layout.

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
path. `sync/inta_bus_check.sh` runs a focused synthetic PIC/EI loop through both
CPUs and requires the typed `IA` sequence `CD D4 FE` end-to-end.

`sync/i8080_vm80a_diff_check.sh` is the complementary instruction-boundary
guard. It generates 8,192 isolated cases: all 256 opcode bytes crossed with all
32 combinations of the architectural S/Z/AC/P/C flags, while register, memory,
immediate, and I/O operands rotate through `00`, `01`, `0F`, `10`, `7F`, `80`,
`FE`, and `FF`. Each case seeds the C core and vm80a at the same clean M1
boundary, executes exactly one instruction, and compares A/BC/DE/HL/SP/PC,
flags, interrupt enable, halt, final memory effects, and port output. Memory
writes are compared by final address/value rather than physical order: for
example, XTHL may write the same two final stack bytes in a different bus order,
which is not an architectural-state difference. This guard is exhaustive over
opcode and initial flag combinations, not over the full 8080 state space.

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

## Real-time pacing (`JUKU_REALTIME_HZ`)

By default `cosim` runs as fast as the host allows — roughly 270x a real Juku
on an M4 Pro — which is what the test suite wants. Set `JUKU_REALTIME_HZ` to a
cycle rate (or the shorthand `1`, meaning the nominal 2 MHz clock from
`ref/juku-machine-facts.json`) and the run is paced so that **wall-clock time
equals machine time**. The pacer sleeps only when simulated time has run ahead
of real time, on a ~1 ms slice; it never speeds a slow host up, so it cannot
hide a model that is lagging. `tests/cosim_realtime_test.py` guards the
default, both spellings of the rate, proportionality at 10x, and rejection of
a malformed value.

Two distinct uses:

- **Measuring machine time without waiting for it.** Run unpaced and divide
  the reported `cyc=` at the stop point by the clock. A native Janet netboot
  of `EKDOS230.BIN` stops at `CA00h` after 187,686,174 cycles, i.e. **93.8 s of
  machine time**, produced in 5.5 s of wall clock.
- **Reproducing host/machine interaction faithfully.** Unpaced, every
  real-world latency on the host side (Python scheduling, `select` granularity,
  USB-UART turnaround) is charged against a machine running ~270x too fast, so
  a 10 ms host hiccup costs seconds of simulated time and trips protocol
  timeouts that hardware never sees. Pacing removes that distortion. The same
  netboot paced: 92.0 s wall against 92.4 s modeled, with rejects falling from
  45 to 28 and transmitted frames from 420 to 386 — closer to the physical
  CS00014 baseline of 334 frames and zero rejects.

Pacing is therefore the honest way to compare a simulated session against a
stopwatch on the bench, and the right mode for any experiment whose result
depends on host and machine agreeing about time.

## Recent execution history (`JUKU_PC_HISTORY`)

Set `JUKU_PC_HISTORY=1` to retain a bounded ring of the last 256 instruction
addresses. On every normal, checkpoint, or stop-PC exit, cosim prints the ring
in execution order as one `[EXEC] recent PCs:` line. It is intentionally off
by default and records only addresses, so long runs neither grow a trace file
without bound nor pay for full instruction logging. This is useful when a
protocol-level timeout leaves the CPU alive but does not identify the loop or
error path that consumed the target. `tests/cosim_realtime_test.py` guards the
opt-in, single-line, and 256-entry bounds.

## Address watchpoint (`JUKU_WATCH_ADDRESS`)

Set `JUKU_WATCH_ADDRESS` to one numeric address or an inclusive `start-end`
range, for example `0xC600-0xC63F`. Cosim logs each memory read and write in
that range with value, PC, and cycle count. It is observation-only and disabled
by default. This is intentionally much narrower than a complete bus trace: it
was added to prove that a CP/M native disk workspace was overwriting service
code and, after its first relocation, the resident NetDisk cache.

## Interactive console (`JUKU_CONSOLE_PTY`)

`JUKU_CONSOLE_PTY=auto` creates a PTY and prints its slave path; a device path
attaches an existing one. Characters the firmware passes to the ROM's console
routine are mirrored to it, and bytes typed into it are queued for the emulated
key matrix, so `screen /dev/ttysNNN` drives the machine from a terminal.

Characters are passed through verbatim in both directions. The firmware
emits its own `CR`/`LF` pairs, so the console must not synthesise newlines --
doing so doubles every line break on the attached terminal.

This is a **simulator affordance, not a machine feature**: a real Juku's console
is its bitmap screen and key matrix, and nothing here changes the ROM or the
firmware. The hook is the console character-output routine (`D9E3h` in the
EktaSoft family, which the monitor's `WRCHR` vector at `FFD9h` jumps to);
`JUKU_CONSOLE_OUT_PC` overrides it for other firmware. Both the banked address
and its mode-0 ROM alias are matched, because the same routine runs at either
depending on the memory mode.

The hook reads the character from register A by default. A BIOS jump-table
entry is often easier to identify before its `MOV A,C`; set
`JUKU_CONSOLE_OUT_REGISTER=C` for that case. This remains observation only and
does not bypass the emulated renderer or keyboard.

Pair it with `JUKU_REALTIME_HZ` for hands-on use — at full simulation speed
a session runs faster than a human can type into it. `JUKU_KEYS` and the
console share one key queue: the scripted string plays first and anything
typed afterwards queues behind it, so `--max-speed --keys TDD` reaches a
CP/M `A>` in seconds and still accepts commands.

`tools/juku_run.py` wraps this into one command: it builds cosim, starts it
paced with a console PTY, optionally attaches a floppy image
(`--disk-image`, or an inherited `JUKU_DISK`) or brings up the Janet netboot
or disk server on a second PTY, and prints the device to attach to (or
bridges the current terminal with `--attach`). Every path it hands to cosim
is resolved first, because cosim runs in its own working directory.

For a CP/Mish dual-network-drive session, `--drive-b` accepts a physical
800 KiB `.JUK` image. A: remains the 386 KiB host volume and may be made
writable; B: preserves the original two-sided 160-track, 4 KiB-block Juku
geometry and is read-only:

```sh
tools/juku_run.py --disk ../cpmish/juku-net-mode2-system.bin \
    ../cpmish/juku-net-mode2.img --drive-b J3KGAME2.JUK --writable --attach
```

It also turns cosim's bank-switch logging off and deletes its run directory
on exit. The Juku switches memory banks constantly -- hundreds of thousands
of times a minute -- so an interactive session left running writes gigabytes
of stderr; one session here reached 52 GB and filled the disk. `--keep-logs`
retains both the logging and the directory when that detail is wanted.

Type boot keys **one at a time with a beat between them**: the emulated
matrix consumes a keystroke every few frames, and anything typed before its
prompt exists is discarded, which looks exactly like the machine ignoring
you. `JUKU_DISK=... tools/juku_run.py` then `T`, `D`, `D` reaches a CP/M
`A>` from the vendored floppy; a bare `--netboot` of a *disk* system such as
`EKDOS230.BIN` will instead hit `Disk Read error` after handoff, because
that system expects a drive. Guarded by `tests/cosim_console_test.py`,
which reads the boot banner out of the terminal and types a command back in.
