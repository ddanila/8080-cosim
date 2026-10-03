# Deep cosim CPU-bus guard — reference

`sync/cosim_check.sh` compares the runnable `juku_top` model
with the C emulator (`cosim`) through ordered CPU-bus events.
The shared event vocabulary is memory read/write (`MR`/`MW`), I/O read/write (`IR`/`IW`), and
interrupt acknowledge (`IA`); address and data are checked for every event, with the acknowledge
address treated as don't-care. The C oracle combines an independent 8080 core
with Juku memory banking and peripheral models. This checks agreement between
two implementations; it does not establish physical timing or complete board
fidelity. LVS checks connectivity, while `boot_check` checks sampled memory.

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

`WINDOW` (ns) and `TRACE_LIMIT` (events) bound the run. Their defaults are
30,000,000 ns and 130,000 events; the event verdict may stop the simulation
earlier. Wall runtime depends on the simulator and host, not a full-banner run. The default boot
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
`0x03E0`; `cosim/trace.c` logs its computed/stored comparison. The archived
`ekta24/31/32/35/37.bin` images satisfy it, storing
`7B`/`D3`/`8F`/`EE`/`1A`, respectively. These filename numbers are serials,
not RomBios versions; see [the lineage notes](ektasoft-rombios-lineage.md).
`ekta43.bin` (serial #0043, RomBios 2.43m) is the counterexample: it stores
`F2` while its covered bytes sum to `57`. The boot harness patches its in-memory
checksum byte and logs the change; the source file remains unchanged. The
patch condition tests the stored byte and computed sum, not the filename or
whole-image hash.

Jukuravi rung 5a deliberately uses these exact offsets rather than inventing a
second short-ROM convention. Its D15-only diagnostic reserves `0x000A`, starts
framed protocol tables at `0x0800`, and recomputes all 2,037 covered bytes at
runtime before touching the USART or RAM.

## Bus and DRAM model boundary

The default 130,000-event run requires `BTRACE-END` with matching event types,
addresses and data, including the BIOS RAM test at `D300h`. A malformed or
short reference trace, absent default event class, mismatch or missing verdict
fails the gate. Stack pushes write high byte first, matching the 8080 bus order.

The functional DRAM model holds RAS through the CAS column phase. It latches
row/column addresses at their strobes and strobes DIN on the later falling
edge of CAS or WE, covering early and delayed writes. A sub-nanosecond settling
delta handles the zero-delay address mux; it does not model real DRAM access
latency. `hdl/sim/dram_unit_tb.v` checks control-edge ordering, read-after-write,
physical row permutation and non-aliasing addresses through `sync/boot_check.sh`.
The timing reference is the vendored
[Mostek MK4564 datasheet](../ref/datasheets/mk4564-64kx1-dram.pdf), interpreted
for the К565РУ5Г bank in `ref/datasheets/k565ru5-pinout.txt`.

This model does not prove the complete historical video-slot timing, D36/R57
propagation delay or precise DOUT turn-off. The runnable video path retains
its simulation-only second port. See
[memory timing](memory-timing-boundary.md) and
[video-slot timing](video-slot-timing-audit.md) for the remaining evidence.
Resolved simulator-ordering defects and the retired Verilog oracle are
recorded in Git history.

## Real-time pacing (`JUKU_REALTIME_HZ`)

By default `cosim` runs as fast as the host allows. Set `JUKU_REALTIME_HZ` to a
cycle rate (or the shorthand `1`, meaning the nominal 2 MHz clock from
`ref/juku-machine-facts.json`) and the run is paced so that **wall-clock time
equals machine time**. The pacer sleeps only when simulated time has run ahead
of real time, on a ~1 ms slice; it never speeds a slow host up, so it cannot
hide a model that is lagging. `tests/cosim_realtime_test.py` guards the
default, both spellings of the rate, proportionality at 10x, and rejection of
a malformed value.

For machine-time measurement, run unpaced and divide the reported `cyc=` by
the selected clock rate. For experiments involving host scheduling, serial
turnaround or a bench stopwatch, enable pacing: otherwise host latency is
charged against a guest executing faster than the physical machine. A slow
host can still lag the requested rate; inspect modeled and wall times before
comparing results.

An interactive tool may instead need maximum CPU speed while retaining a
native helper process on the emulated USART. Set `JUKU_USART_HOST_SYNC_MS` to
the maximum wall-clock wait for the first reply byte after target
transmission (an integer from 1 to 60,000 ms). This opt-in coordination prevents the unpaced guest from
consuming a firmware timeout before the helper is scheduled; it does not
alter the 8251/PIT byte timing or pace CPU-only execution. Leave it unset for
timing experiments and use `JUKU_REALTIME_HZ` whenever wall time itself is
part of the experiment.

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
by default. Use it to observe a specific memory boundary without a complete bus trace.

Every checkpoint also records a cumulative `watch_write_count` and the
address, value, PC, and emulated cycle of the previous and last watched writes.
These bounded fields make short intervals that occur entirely between two
host checkpoints observable without relying on stdio flush timing. They are
zero when no watched write has occurred and do not alter the existing textual
watch log.

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

Set `JUKU_CONSOLE_OUT_DISABLE=1` to retain PTY-to-key-matrix input while
disabling all simulator console-output interception. This is the appropriate
mode when output must be observed exclusively through a production serial
console such as C9 N4.

Pair it with `JUKU_REALTIME_HZ` for hands-on use — at full simulation speed
a session runs faster than a human can type into it. `JUKU_KEYS` and the
console share one key queue: the scripted string plays first and anything
typed afterwards queues behind it, so `--max-speed --keys TDD` reaches a
CP/M `A>` in seconds and still accepts commands.

Timing-sensitive raw-key tests can inject one ordinary matrix contact at an
exact instruction boundary with `JUKU_KEY_AT_PC=PC:BYTE`. Both fields are
hexadecimal; for example, `JUKU_KEY_AT_PC=34A2:1B` begins a physical Escape
contact immediately before the instruction at `34A2h`. The contact then uses
the normal `JUKU_KEY_HOLD_FRAMES` and `JUKU_KEY_GAP_FRAMES` timing and the same
factory matrix mapping as PTY/scripted input. Set
`JUKU_KEY_AT_PC_HOLD_FRAMES` to override only the triggered contact's hold
time when it must span a slow guest operation; ordinary PTY/scripted contacts
retain `JUKU_KEY_HOLD_FRAMES`. If a relocatable or overlaid program can reach
the same numeric PC during startup, `JUKU_KEY_AT_PC_GATE=ADDRESS:BYTE` delays
the trigger until the byte visible at that hexadecimal guest address equals
the hexadecimal value. The trigger fires once and does not bypass the guest
keyboard scanner; it exists to make a poll-overlap regression deterministic
at full simulator speed.

`tools/juku_run.py` wraps this into one command: it builds cosim, starts it
paced with a console PTY, optionally attaches a floppy image
(`--disk-image`, or an inherited `JUKU_DISK`) or brings up the native C
`jukuhost` on a second PTY, and prints the device to attach to (or bridges the
current terminal with `--attach`). It builds `build/jukuhost` on demand,
retains a text log plus raw capture when `--keep-logs` is selected, and has no
Python-host fallback. Every path it hands to cosim is resolved first, because
cosim runs in its own working directory.

For a CP/Mish dual-network-drive session, `--drive-b` accepts a physical
800 KiB `.JUK` image. A: remains the 386 KiB host volume and may be made
writable; B: preserves the original two-sided 160-track, 4 KiB-block Juku
geometry and is read-only:

```sh
tools/juku_run.py --disk ../cpmish/juku-net-mode2-system.bin \
    ../cpmish/juku-net-mode2.img --drive-b J3KGAME2.JUK \
    --disk-baud 19200 --disk-protocol 2 --writable --attach
```

It also turns cosim's bank-switch logging off and deletes its run directory
on exit. The Juku switches memory banks constantly -- hundreds of thousands
of times a minute -- so long sessions can produce large stderr logs. `--keep-logs`
retains the directory and leaves the inherited `JUKU_TRACE_BANK` setting intact.
If it is already `0`, bank logging stays disabled. Likewise, `--max-speed`
skips the launcher’s pacing override but preserves an inherited
`JUKU_REALTIME_HZ`; unset that variable for an unpaced run.

Type boot keys **one at a time with a beat between them**: the emulated
matrix consumes a keystroke every few frames, and anything typed before its
prompt exists is discarded, which looks exactly like the machine ignoring
you. `JUKU_DISK=... tools/juku_run.py` then `T`, `D`, `D` reaches a CP/M
`A>` from the vendored floppy; a bare `--netboot` of a *disk* system such as
`EKDOS230.BIN` will instead hit `Disk Read error` after handoff, because
that system expects a drive. Guarded by `tests/cosim_console_test.py`,
which reads the boot banner out of the terminal and types a command back in.
