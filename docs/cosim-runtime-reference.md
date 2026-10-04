# Cosim runtime and CPU-bus reference

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

## Command stack measurements and checkpoints

Set `JUKU_CHECKPOINT_PREFIX` to the output path prefix, then use:

- `SIGUSR2` immediately before submitting a CP/M command: arm measurement
  for its next `0100h` entry.
- `SIGUSR1` after the prompt: write `.ram` and `.state` without stopping.
- `SIGTERM` or `SIGINT`: stop and write the final checkpoint.

The stack measurement excludes resident BDOS work reached through `CALL 0005h`
or `JMP 0005h`. It tracks call depth and the exact stacked return address,
including page-zero and resident-CCP returns, and freezes at the command's
exit. BDOS function 0 terminates the measurement without waiting for a return.
The state records entry SP, segment anchors, low SP, observed bytes, explicit
SP writes, generation and armed/frozen status. These command-scoped fields
avoid attributing subsequent CCP/BDOS stack use to the transient.

Each checkpoint overwrites the same prefix's files: RAM first, then state,
without an atomic pair replacement. A live reader can see an incomplete or
mixed pair; coordinate reads between requests and retain copies needed for
comparison. `checkpoint_generation` in `.state` counts dumps, including the
final dump; it is not an archive index or a generation tag in the RAM file.
Repeated command measurements have their own generation counter. Standard
signals can coalesce, so send and observe requests one at a time.

## CP/M Plus disk trace

For CP/M Plus NetDisk analysis, set
`JUKU_CPM_DISK_TRACE=/path/to/disk-trace.txt`. With the documented C6 native
binding at `C000h`, the trace records every BIOS `READ` and `WRITE` entry plus
drive, track, translated sector, DMA address, and cycle count. Unlike the host
protocol log, this includes resident-cache hits and therefore exposes the
actual record-consumption sequence without changing target code or timing.
The fixed instrumentation addresses are `C027h`/`C02Ah` with state at
`C93Ah`; do not use it for another adapter layout.

## How it works

1. `cosim` boots the adopted archive-0037 RomBios 3.43m image
   (`roms/ekta37.bin`) and dumps `TYPE addr data` lines through
   `JUKU_BUS_TRACE`, bounded by `JUKU_BUS_TRACE_LIMIT`. Paired reads retain real 8080 low-byte-first
   order, while stack pushes retain the CPU's high-byte-first write order.
2. `hdl/sim/cosim_ctrace_tb.v` runs `juku_top`, classifies DBIN and WR edges from the decoded bus
   strobes, consumes the next expected event, and compares its type, address, and CPU-visible data.
   Interrupt acknowledges compare the supplied opcode while ignoring the electrically undefined
   address. The first mismatch is reported with full context.

```sh
sync/cosim_check.sh
```

Run with Bash, Python 3, a C compiler (`CC`, default `cc`), and Icarus
Verilog (`iverilog` and `vvp`). The guard regenerates `hdl/sim/ekta37.hex`
and runs the C trace from `cosim`, where its framebuffer dump can replace
`vram.bin`; copy an existing capture elsewhere if it must be retained. Build
and bus-trace files are temporary and removed when the script exits.

`WINDOW` (ns) and `TRACE_LIMIT` (events) bound the run. Their defaults are
30,000,000 ns and 130,000 events; the event verdict may stop the simulation
earlier. Wall runtime depends on the simulator and host, not a full-banner run. The default boot
necessarily covers `MR`, `MW`, `IR`, and `IW`; separate interrupt guards exercise the interrupt
path. `sync/inta_bus_check.sh` runs a focused synthetic PIC/EI loop through both
CPUs and requires the typed `IA` sequence `CD D4 FE` end-to-end.

`sync/i8080_check.sh` tests the C core against independent expected results:
immediate arithmetic/logic across all byte operands, INR/DCR and rotates,
valid packed-BCD addition followed by DAA, and selected stack, I/O, EI-delay and
undocumented-opcode cases. Its DAA sweep covers decimal operands 0–99 and both
input carries, not every arbitrary A/flag state. It requires a C compiler.

`sync/i8080_vm80a_diff_check.sh` is the complementary instruction-boundary
guard. It generates 8,192 isolated cases: all 256 opcode bytes crossed with all
32 combinations of the architectural S/Z/AC/P/C flags. Selected registers and
byte operands use eight boundary patterns; addresses and remaining memory use
deterministic patterns, direct jump/call operands and preloaded stack words use
`3456h`, and input ports return `port XOR A5h`. These choices are correlated, not an independent operand
cross-product. Each case seeds the C core and vm80a at the same clean M1
boundary, executes exactly one instruction, and compares A/BC/DE/HL/SP/PC,
flags, interrupt enable, halt, final memory effects, and port output. Memory
writes are compared by final address/value rather than physical order: for
example, XTHL may write the same two final stack bytes in a different bus order,
which is not an architectural-state difference. This guard is exhaustive over
opcode and initial flag combinations, not over the full 8080 state space. It
does not compare cycle counts, read-bus ordering, WAIT behavior or asynchronous
interrupt acceptance. It requires a C compiler and Icarus Verilog; the bus and
interrupt guards above cover separate boundaries.

## EktaSoft block-1 checksum convention

The boot ROM stores at `0x000A` the eight-bit additive sum of bytes
`0x000B..0x07FF`. This is the convention exercised by the checksum routine at
`0x03E0`; `cosim/trace.c` logs its computed/stored comparison. Per-image
identities and checksum findings belong to
[the lineage notes](ektasoft-rombios-lineage.md). Filename numbers identify
serials, not RomBios versions.
`ekta43.bin` (serial #0043, RomBios 2.43m) is the counterexample: it stores
`F2` while its covered bytes sum to `57`. The boot harness patches its in-memory
checksum byte and logs the change; the source file remains unchanged. The
patch condition tests the stored byte and computed sum, not the filename or
whole-image hash.

Diagnostic-ROM checksum and build identities are documented in
[the Jukuravi firmware guide](../spinoffs/jukuravi/firmware/README.md).

## Bus and DRAM model boundary

The C reference must contain exactly the requested event count (130,000 by
default) and all four default event classes. The HDL gate accepts either
`BTRACE-END` when that trace is exhausted or `BTRACE-OK` when the configured
simulation window ends after matching the compared prefix. A passing window
verdict therefore does not require all reference events, or the BIOS RAM test
at `D300h`, to have been reached. Inspect the verdict and compared-event count
when using the result as coverage evidence. A malformed or short reference
trace, absent default event class, mismatch or missing verdict fails the gate. Stack pushes write high byte first, matching the 8080 bus order.

The HDL `dram_64kx1` model initializes all cells to zero and retains them
without charge decay. Those are simulator assumptions, not physical power-on
contents or retention evidence. A passing boot does not prove that hardware
refresh preserves RAM.

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

## Real-time pacing (`JUKU_REALTIME_HZ`)

By default `cosim` runs as fast as the host allows. Set `JUKU_REALTIME_HZ` to a
cycle rate (or the shorthand `1`, meaning 2 MHz) to pace execution toward that
rate. Every roughly 2,000 simulated cycles, the pacer checks elapsed wall time
and sleeps if execution is more than 0.5 ms ahead. The check interval is about
1 ms at 2 MHz and changes with the selected rate. A slow host can still lag;
inspect modeled and wall times before comparing results.
`tests/cosim_realtime_test.py` guards the
default, both spellings of the rate, proportionality at 10x, and rejection of
a malformed value.

For machine-time measurement, run unpaced and divide the reported `cyc=` by
the selected clock rate. For experiments involving host scheduling, serial
turnaround or a bench stopwatch, enable pacing: otherwise host latency is
charged against a guest executing faster than the physical machine.

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
range, for example `0xC600-0xC63F`. Cosim logs each memory read (including opcode fetches) and attempted write in
that range with value, PC, and cycle count. It is observation-only and disabled
by default. Use it to observe a specific memory boundary without a complete bus trace.

Every checkpoint also records a cumulative `watch_write_count` and the
address, value, PC, and emulated cycle of the previous and last watched writes.
Writes are recorded before ROM protection or injected write faults are applied;
these fields prove attempted bus writes, not that RAM accepted the values.
These bounded fields make short intervals that occur entirely between two
host checkpoints observable without relying on stdio flush timing. They are
zero when no watched write has occurred and do not alter the existing textual
watch log.

## Interactive console (`JUKU_CONSOLE_PTY`)

`JUKU_CONSOLE_PTY=auto` creates a PTY and prints its slave path; a device path
attaches an existing one. At the configured output PC, the selected character
register is mirrored to it. Bytes typed into the PTY are queued for the
emulated key matrix, so `screen /dev/ttysNNN` drives the machine from a terminal.

Output characters are mirrored verbatim. The firmware emits its own `CR`/`LF`
pairs, so the terminal must not add newlines. Input converts `LF` to `CR`
(Return) and `DEL` to Backspace before queueing matrix keystrokes.

This is a **simulator affordance, not a machine feature**: a real Juku's console
is its bitmap screen and key matrix, and nothing here changes the ROM or the
firmware. The default hook is `D9E3h`, the console character-output routine
used by the adopted ekta37 image. Set `JUKU_CONSOLE_OUT_PC` to the verified
output entry for another image or resident BIOS (for example,
`JUKU_CONSOLE_OUT_PC=0xC600`). For any configured PC at or above `C000h`,
the hook also matches that PC minus `C000h`. It tests numeric PCs without
checking the active bank, instruction bytes, or ROM identity. Execution of
unrelated code at either address can therefore produce misleading output;
PTY text alone does not prove that the firmware rendered those characters.

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
typed afterwards queues behind it. The [runner](../tools/juku_run.py) accepts
`--max-speed --keys TDD` to submit the disk-boot command and continue accepting
interactive input. These are runner options, not arguments to the `trace` binary.

Direct `trace` runs delay queued matrix input until
`JUKU_KEY_START_VRAM` framebuffer writes (default `42000`, chosen for the
EktaSoft banner). Set it to a suitable threshold, or `0`, for firmware that
does not draw that banner. `JUKU_KEY_HOLD_FRAMES` and `JUKU_KEY_GAP_FRAMES`
both default to `3`; they count configured frame intervals rather than
wall-clock seconds. Guest firmware must still scan the matrix for a contact
to become a key event.

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
Python-host fallback. An existing `build/jukuhost` is reused without a freshness
check; run `sync/jukuhost_linux_build.sh` after host-source changes. `--host`
selects an existing executable and never rebuilds it. The launcher resolves ROM and disk-image paths before starting cosim in its
run directory. Supply an absolute path for `--trace`: that prebuilt executable
path is passed unchanged. Other inherited path-valued cosim settings also
resolve from the run directory, so use absolute paths for them.

The launcher defaults to NetDisk protocol 2 at 9600 baud; the standalone
`jukuhost` defaults to protocol 3 at 19200. Select the protocol and baud required
by the served system explicitly when using another profile. These disk
settings are passed only with `--disk`; `--netboot` starts a boot-only host
and does not use them.

For a CP/Mish dual-network-drive session, `--drive-b` accepts a physical
800 KiB `.JUK` image. The C host requires A: to be exactly 409,600 bytes
(400 KiB); the guest filesystem determines its usable capacity. `--writable`
enables journaled writes directly to that A: file. B: preserves the original
two-sided 160-track Juku geometry and is read-only:

```sh
tools/juku_run.py --disk ../cpmish/juku-net-mode2-system.bin \
    ../cpmish/juku-net-mode2.img --drive-b J3KGAME2.JUK \
    --disk-baud 19200 --disk-protocol 2 --writable --attach
```

The launcher turns cosim's bank-switch logging off and removes its run directory
during normal shutdown unless `--keep-logs` is set. The Juku switches memory banks constantly -- hundreds of thousands
of times a minute -- so long sessions can produce large stderr logs. `--keep-logs`
retains the directory and leaves the inherited `JUKU_TRACE_BANK` setting intact.
If it is already `0`, bank logging stays disabled. Likewise, `--max-speed`
skips the launcher’s pacing override but preserves an inherited
`JUKU_REALTIME_HZ`; unset that variable for an unpaced run.

An early failure to discover the console or serial PTY returns 1 and leaves
the run directory for diagnosis. After startup, the launcher does not propagate
child-process exit codes: its normal shutdown returns 0, and a host failure
does not stop cosim. Use `--keep-logs` and inspect the host log/capture when
qualifying a network session. In `--attach` mode, Ctrl-] leaves the bridge and
shuts down the session; it does not leave the emulator running in the background.

Wait for each expected boot prompt before typing the next key. The simulator
queues matrix contacts; it does not synchronize them to visible prompts.
Startup scans can consume an early contact before the intended command handler
is ready. `JUKU_DISK=... tools/juku_run.py` then `T`, `D`, `D` reaches a CP/M
`A>` from the vendored floppy; a bare `--netboot` of a *disk* system such as
`EKDOS230.BIN` will instead hit `Disk Read error` after handoff, because
that system expects a drive. `tests/cosim_console_test.py` checks the console
with the committed `ekta4401` remix: it reads the banner and sends `H`, then
requires the help response. It does not exercise this disk-boot sequence.
