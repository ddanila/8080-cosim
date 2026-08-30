# Jukuravi diagnostic ROM and host

Jukuravi is a diagnostic and recovery environment for the original Juku
`.009` processor board. T31 is the stable CS00015 service image; T36 is the
physically booted physical-row refresh image for CS00024. Both expose loader API v2
over the onboard 8251 and remain resident while the host uploads and calls
8080 snippets.

The physical reference system is Arvutimuuseum board `CS00015`. Its validated
T31 transport run, historical D55 bitmap, transport benchmark, upper-D15
diagnostic, and uploaded speaker demo are recorded in
[`T31-PHYSICAL.md`](T31-PHYSICAL.md).
The separate CS00024 T31 session and its corrected D55 interpretation are in
[`CS00024-PHYSICAL.md`](CS00024-PHYSICAL.md). The completed T36 desk diagnosis
and D57 channel-2 localization are in
[`../../docs/cs00024-t36-diagnosis.md`](../../docs/cs00024-t36-diagnosis.md).
The prepared, not yet executed video-slot refresh experiment — arming the
exact EktaSoft D54/D55 raster from the T36 loader and holding RAM
unrefreshed — is specified in
[`RASTER-REFRESH-EXPERIMENT.md`](RASTER-REFRESH-EXPERIMENT.md) with its
runner [`raster_retention.py`](raster_retention.py). The planned
EktaSoft-based remix ROM that embeds the Jukuravi loader as a monitor
command is specified in
[`EKTA37-REMIX-PLAN.md`](EKTA37-REMIX-PLAN.md).

The separately built, from-scratch network-only successor is in
[`network-rom/`](network-rom/README.md). Its C6 / ABI 1.2 bounded POST,
ROM-resident Fastboot V16, services, and real CP/M Plus handoff are
simulator-qualified. On 2026-08-18 the exact C6 D15/D16 pair was programmed,
verified, fitted in CS00015, and passed every monitor-independent physical
item. Display/cursor observation remains pending; see the CP/M Plus
[`C6 qualification record`](https://github.com/ddanila/cpm-plus-juku/blob/master/docs/cs00015-c6-blind-qualification-20260818.md).

[`JUKUPOLY.md`](JUKUPOLY.md) records the 2026-08-29 JukuPoly result: a
163-byte strict-8080 CP/M transient synthesizing a physically confirmed
three-voice A-major chord through the unmodified CS00000 speaker at an average
cycle-model sample rate of 10.97 kHz.  It includes the mode-0 PIT technique,
source and regression paths, loudness revision, and retained physical evidence.
The follow-on [`compiled-pattern player`](JUKUPOLY-TRACKER.md) adds envelopes,
legato, detune, slide, and genuinely concurrent sample percussion; its credited
`CANYON.MID` reduction is cycle-qualified at 7.186 kHz and passed a CS00000
physical listening run on 2026-08-30.
The same engine's one-minute, credited arrangement of Robert Prince's DOOM
E1M5 theme “Suspense” also passed physical listening on CS00000.  A 10,701-byte
full 2:44 reduction subsequently completed a cold-boot physical run and
returned cleanly to CP/M.

The 2026-08-09 desk audit invalidated the T15/T16/T31/T32 D55 predicate: those
ROMs did not establish the physical D55 clocks before latching their Mode-0
counts. T34 is the first clock-safe D55 functional-path image. Neither
CS00015 nor CS00024 currently has valid evidence that its D55 package is bad;
see
[`../../docs/jukuravi-d55-diagnostic-audit.md`](../../docs/jukuravi-d55-diagnostic-audit.md).

## Current machine configuration

CS00015 was restored on 2026-08-08 with **EK37 / EktaSoft 3.7**, received the
project's frozen Ekta4401 D15/D16 service-ROM pair on 2026-08-11, and was
upgraded to Ekta4402 on 2026-08-16. Ekta4402 provided direct `N` fastboot plus
the inherited Jukuravi API-v2 `J` entry and is now a frozen preceding baseline.
Two physical `J` attaches requalified PROBE, 128-row refresh query and READ
with zero transport mismatch; evidence is retained under
`sessions/cs00015-ekta4402-j-physical/`. The
T31/T32 configurations below and the intervening EK37 restoration remain
historical evidence. JukuNet C6 / ABI 1.2 is fitted as of 2026-08-18. The donor D6 `.038` remains
fitted, the original D8 `.039` is restored, and D1 is repaired;
see [`../../docs/cs00015-service-record.md`](../../docs/cs00015-service-record.md).

On 2026-08-09 a separate AT28C64B diagnostic/service EEPROM was refreshed from
T32 to the pinned T31 image and verified by a complete programmer verify plus
one independent full read. It is prepared media, not currently fitted in
CS00015. The identities and physical programming record are in
[`T31-PHYSICAL.md`](T31-PHYSICAL.md#service-media-refresh-2026-08-09).

The validated diagnostic setup was:

- D15: `firmware/diag-d0-low4k.bin` / DOS name `T31HOST.BIN`
- D16: unpopulated
- serial: direct CP2102 -> MAX3232 -> Juku X3
- link: 2400 baud, 8N1
- Juku signals: X3.9 SOUT, X3.4 SIN, X3.5 CTS, X3.7 signal ground
- loader RAM: `4000h..BFFFh`; `C000h..CFFFh` is reserved by the ROM

X3 carries RS-232 levels. Never connect it directly to CP2102, Arduino, or
other TTL UART pins. Use a MAX3232-class level converter, including its charge
pump capacitors and common signal ground. The measured connector facts are in
[`../../docs/serial-handoff.md`](../../docs/serial-handoff.md); the optional
Nano bridge wiring is in [`nano/README.md`](nano/README.md).

### Serial port naming

The examples below use the Linux `/dev/ttyUSB0`. On macOS the same adapter
appears as `/dev/cu.usbserial-*`, or `/dev/cu.SLAB_USBtoUART` if the vendor
Silicon Labs driver is installed instead of the built-in one. Always use the
`cu.*` node: opening `tty.*` blocks until carrier detect, which this link never
asserts. Pass `--port` accordingly; `host.py` requires it explicitly, while
`probe_waitclass.py` and `probe_a12_increment.py` default to the first adapter
found by `host.discover_serial_ports()` and print which one they chose.

macOS needs no driver or dependency install: the CP210x driver ships with the
system, and `host.py` uses stdlib `termios` rather than pyserial. Do not install
the vendor Silicon Labs kext alongside the built-in driver. The verified macOS
first-contact sessions against CS00015, including the two instructive failed
attaches, are recorded in [`MACOS-BENCH.md`](MACOS-BENCH.md).

On a cold boot, run a full session first. `--attach-loader` means "reattach to
an already-resident loader without resetting"; it deliberately never answers the
banner, so using it against a freshly reset board leaves the ROM's handshake
unanswered until it gives up into a failure tone. Boot normally once, then
attach as often as needed without another RESET.

T31 and every committed diagnostic image are generated artifacts with pinned
checksums. Build and ROM-version details live in
[`firmware/README.md`](firmware/README.md).

The current upper-ROM diagnostic is T32 (`firmware/diag-d0-waitclass.bin`, DOS
name `T32HOST.BIN`). It retains the complete T31 low-4K monitor and adds eight
deliberate upper-D15 entry points covering the full `{A11,A10,A9}` wait-class
matrix. Each entry stores a unique marker at `4100h` before returning to the
loader, so the host can distinguish an exact successful fetch from a reset or
an unrelated recovery. Its CS00015 cold boot and upper-ROM physical results are
recorded in [`T32-PHYSICAL.md`](T32-PHYSICAL.md); T31 remains the stable loader
and application reference.

After a successful T32 boot leaves loader API v2 resident, exercise and
identify the complete upper-ROM matrix without another RESET:

```sh
python3 spinoffs/jukuravi/probe_waitclass.py --port /dev/ttyUSB0
```

The completed serial-only T33 investigation is retained in
[`T33-PLAN.md`](T33-PLAN.md). The decisive direct-INX probe and ROM WAIT
confirmations ran against the burned T32 image without a re-burn; replacing D1
then changed the exact faulty register signature to the fully clean result.

If the hardware investigation resumes, the next controlled D55 action is a
T34 `1C/A637` cold boot, not substitution. A clean T34 result cancels the
substitution plan; only a repeated T34 `08` opens the controlled discriminator.
Use [`D55-REPLACEMENT.md`](D55-REPLACEMENT.md) for the exact T34 hash,
before/after matrix, provenance/socket inspection, rollback criteria, and
evidence record. Do not combine that discriminator with other rework or
optional Nano wiring.

On CS00015, the wait-class matrix is superseded by a D1 16-bit increment fault.
After a clean T32 boot, read the affected register-pair results directly
without another ROM burn:

```sh
python3 spinoffs/jukuravi/probe_a12_increment.py --port /dev/ttyUSB0
```

`D15-LOCAL` means all consecutive RAM pairs remained `AA BB`; `SHARED-A12`
means their second bytes came from the lower alias as `AA 22`.

## Host use

The CLI defaults match the direct CS00015 setup: 2400 baud, one physical symbol
per logical bit, and a 6 ms response guard. CRC-protected command retries and
independent RAM verification remain enabled.

Attach to the resident monitor, upload a cooperative snippet, call it, collect
returned A, and optionally read a result block:

```sh
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 --attach-loader \
  --load task.bin --load-address 4000 --run-address 4000 \
  --run-mode call --result-address 4100 --result-length 16
```

The snippet may use the stack and temporary serial settings, but it must finish
with an ordinary `RET`. The ROM restores its execution and serial state, reports
A, and waits for another command. Hardware RESET is only needed if uploaded code
crashes, loops, halts, corrupts the reserved workspace, or cannot return.

Useful control-only operations:

```sh
# Confirm that the resident loader responds without changing RAM.
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 \
  --attach-loader --probe-loader

# Inspect retained RAM from a later host process.
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 \
  --attach-loader --probe-loader --read-address 4100 --read-length 16

# Upload and verify, but do not execute.
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 \
  --attach-loader --load task.bin --load-address 4000 --load-only
```

If a different cable is marginal, increase `--loader-guard-ms` first. An odd
majority can then be selected with `--loader-votes 3`, `5`, or `7`. The host
records timestamp-matched raw RX, raw TX, and decoded JSON for every session.
Run `python3 spinoffs/jukuravi/host.py --help` for the complete parameter set.

CS00024 exposed a different boundary: its short seven-vote CONFIG command
passes, while its longer seven-vote bootstrap PROBE reproducibly crosses a
strong-CRC boundary involving the `C000h` parser state. The explicit
`--loader-config-first` policy sends CONFIG before PROBE and then uses the
requested one-vote width. It is not the default and must not be used to hide a
failed exact-cookie PROBE; the PROBE still runs immediately after CONFIG and
must echo all eight bytes exactly.

### One-session T34/T35/T36 batch

[`batch.py`](batch.py) is the CS00024 full host-driven workflow. `--rom t34`
pins exact T34 `1C/A637` and performs the short CONFIG-first transition to one
vote. `--rom t35` pins historical T35 `1D/45C4`; `--rom t36` pins corrected
T36 `1E/C617`. Both use a native one-vote bootstrap and refresh-aware targets.
All profiles keep the same loader session and serial
descriptor open for:

- verified upload, exact readback, CALL/RET and returned-result control;
- a paired host-timed CPU loop that measures effective CPU MHz without I/O;
- clean-result oracles for write-map, LHLD, POP/SHLD, READY-class, boundary,
  and direct INX/DAD probes;
- independent `4000h`/`5000h` data retention and execution; and
- a one-vote parser-aging sweep at 6/12/24/36 ms per physical symbol, with a
  short CONFIG recovery after every point; and
- as the deliberately final operation, eight raw high/low samples from every
  D57 channel, with serial restoration.

Start the runner before resetting the board:

```sh
python3 spinoffs/jukuravi/batch.py --port /dev/ttyUSB0 \
  --rom t36 --local-full-ram-sweep --local-full-ram-hold-ms 6000 \
  --log-dir spinoffs/jukuravi/sessions/cs00024-t36-local-full-physical
```

Wait for `press RESET once`, then press RESET exactly once. The run overwrites
volatile diagnostic RAM. The local sweep uploads a 792-byte cooperative probe
at `4000h` to test `5000h..BFFFh`, then relocates it to `B000h` to test
`4000h..AFFFh`. Their union is all 32 KiB, including both code homes; each
fill and verify calls T36 refresh every 128 bytes and returns compact mismatch,
XOR-mask, first-address, and D84..D91 candidate evidence. It does not touch
EEPROM or persistent media. Do not run it when unsaved RAM contents matter.
T32-only upper-ROM wait-class entries are deliberately excluded because T34
does not contain them. Use `--no-retention-sweep` only when the parser-aging
characterization is not wanted.

`--full-ram-sweep` retains the original wire-forensic method: every 32-byte
LOAD receives an independent READ verification, followed by a second complete
READ after the hold. At 2400 baud its bit-symbol transport takes on the order
of 16 hours for four 32 KiB patterns on physical hardware. It is preserved for
partial-range or wire-level investigations, not recommended as the routine
full-board test. [`analyze_jukuravi_partial_full_ram.py`](../../scripts/analyze_jukuravi_partial_full_ram.py)
recovers completed write/readback and delayed-prefix evidence when such a run
is deliberately interrupted.

The CPU value is an **effective execution frequency**: RAM instruction fetches
and physical READY waits are included. T34's paired short and long CALLs differ
by 1,200,000 nominal 8080 T-states; T35/T36's refresh-aware pair differs by
1,078,000. Subtracting their host-observed RUN-to-RETURN intervals cancels the
fixed loader and serial overhead. It is not presented as a direct crystal
measurement. D57 sampling is last because a board whose boot bitmap already
reports D57 may lose the loader link when that PIT is reprogrammed; all CPU/RAM
and parser evidence is preserved first. Run the complete batch regression with:

```sh
sync/jukuravi_t34_batch_check.sh
```

On physical CS00024 the batch measured 1.714065 MHz, then proved that long
uploads can lose their early RAM bytes before RUN. Use [`retention.py`](retention.py)
for the narrower destructive-retention test. It writes one 32-byte marker and
re-reads it at requested wall-clock ages in the same loader process:

```sh
python3 spinoffs/jukuravi/retention.py --cold --port /dev/ttyUSB0 \
  --address 4D00 --ages 0,20 --loader-guard-ms 0 \
  --log-dir spinoffs/jukuravi/sessions/cs00024-t34-retention
```

Start it before RESET. `--cold` pins T34 `1C/A637`; without `--cold` it attaches
to an already-running API-v2 loader. The physical evidence is not a generic
DRAM benchmark: loader commands themselves touch RAM and can refresh the tested
rows. CS00024 passes when touched about every five seconds but loses mutable
loader state after an untouched interval between roughly 5 and 17 seconds.
See [`CS00024-PHYSICAL.md`](CS00024-PHYSICAL.md) for exact captures and limits.

### T35 physical finding and T36 successor

T35 (`1D/45C4`) was programmed and produced valuable captures, but it is not
an all-row refresh solution. The drawings establish CPU A0..A7 on the DRAM
address mux during RAS; MK4564-class 128-cycle refresh consumes MA0..MA6 and
ignores MA7. T35 increments H and therefore reads `4000h,4100h,...,BF00h`:
the low seven address bits remain zero, so physical row `00` is refreshed 128
times.

The six-second `4D00h` physical lane capture confirmed that interpretation.
Offset zero survived while other low-address rows decayed in structured
blocks, every D84..D91 bit lane participated, and the loader later stopped.
The earlier long T35 reattach proves survival of frequently touched loader
state, not all-row retention.

T36 is the programmed physical-test image:

- artifact `firmware/diag-d0-row-refresh.bin` / `firmware/dos/T36HOST.BIN`;
- ROM `1E`, CRC16 `C617`;
- SHA256 `32264641836ce914a0fc706c916e2847d542d83b05d6737f1d6272b76d78dedb`;
- public `CALL 07A9h`, now reading `4000h..407Fh` with `INR L`.

T36 retains T34's clock-safe D55 test, T35's one-vote/fail-safe loader policy,
and query/enable/disable/counter command. The approximately 1.7 MHz host result
is effective RAM-loop throughput including READY waits, not a direct clock
measurement. It gives a conservative 1.234 ms estimate per sweep against the
2 ms datasheet interval.

The completed post-burn run used the destructive local 32 KiB RAM sweep with
zero, one, checkerboard, and address-XOR patterns. Two small relocated programs
covered the complete range after a six-second refresh-on hold and returned
compact D84..D91 failure attribution:

```sh
python3 spinoffs/jukuravi/batch.py --port /dev/ttyUSB0 --rom t36 \
  --local-full-ram-sweep --local-full-ram-hold-ms 6000 \
  --log-dir spinoffs/jukuravi/sessions/cs00024-t36-local-full-physical
```

Start the command first and press RESET once when requested. This overwrites
all host-safe RAM at `4000h..BFFFh`; it does not alter EEPROM. Use
`--only-ram-lanes` for the shorter 32-byte scratch discriminator. See
[`CS00024-PHYSICAL.md`](CS00024-PHYSICAL.md) for the captures and
[`LOADER-API-V2.md`](LOADER-API-V2.md) for the ABI.

The first T36 physical session on 2026-08-10 passed the complete boot bitmap,
verified upload/return, the 1.702797 MHz effective CPU measurement, and every
A12/LHLD/READY/boundary/increment probe. Its intentionally interrupted
wire-forensic zero pattern still proves a full 32,768-byte LOAD plus immediate
readback with zero retries. After the six-second hold, the captured contiguous
`4000h..46BFh` prefix contained 1,728 exact zeros and sampled all 128 physical
rows 13--14 times. See the physical log for the exact limits; the remainder of
that delayed read and the other three wire patterns were not completed.

The later local session completed the missing proof in 45 minutes. All eight
stage/pattern combinations over the union `4000h..BFFFh` passed with zero
mismatching bytes, XOR `00`, and no candidate D84--D91 package. The same run
also retained a legacy `D57R` capture: channel 2 read `99/99` in all eight
repetitions while channels 0/1 worked. That raw result remains useful evidence,
but its original fault interpretation is superseded. Exact E3 tracing shows
D57 CLK2 is active-low `/VER RTR` from D55.13 at about 49.92 Hz, not D57
CLK0's 1.23 MHz clock, and the legacy probe waited only microseconds without
arming the raster. Its channel-2 reads therefore preceded a guaranteed CLK2
edge. Use the corrected focused follow-up without rerunning RAM:

```sh
python3 spinoffs/jukuravi/batch.py --port /dev/ttyUSB0 --rom t36 \
  --only-d57 --log-dir spinoffs/jukuravi/sessions/cs00024-t36-d57-followup
```

The corrected `D57S` probe arms the exact Ekta raster and waits 64 refresh
sweeps after each channel-2 write. CS00015 returned `FD/3D`, `FC/3C`, `FE/3E`
in all eight repetitions, physically validating its D57 channel 2 and
`/VER RTR` path. CS00024 still needs this corrected rerun before any D57
path, socket, or package diagnosis. See the consolidated
[`CS00024 T36 diagnosis`](../../docs/cs00024-t36-diagnosis.md).

### Session logs

Every run writes one `<timestamp>.json` plus matching `.rx.bin` and `.tx.bin`
into a per-run directory under [`sessions/`](sessions). `--log-dir` names that
directory; it defaults to `sessions/default`, resolved relative to `host.py`
rather than the working directory, so runs launched from the repository root do
not scatter log directories there. Use a descriptive name per experiment:

```sh
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 \
  --attach-loader --probe-loader \
  --log-dir spinoffs/jukuravi/sessions/t32-probe
```

The runs cited as physical evidence in [`T31-PHYSICAL.md`](T31-PHYSICAL.md) and
[`T32-PHYSICAL.md`](T32-PHYSICAL.md) are committed, so those directories must
not be pruned.

The optional Nano bridge has a 115200-baud USB side, so it requires explicit
`--baud 115200`; its Juku-side `SoftwareSerial` rate must match the installed
ROM. Its DTR/reset and liveness features are separate from the proven direct
adapter path.

## Loader contract

[`LOADER-API-V2.md`](LOADER-API-V2.md) is the stable wire and execution
contract. Its important properties are:

- framed CRC-8 transport plus a command CRC-16 recomputed from the ROM's parser
  RAM;
- verified, idempotent LOAD/READ/CRC operations and bounded host retries;
- replay-safe RUN IDs, so a lost response does not execute a snippet twice;
- host reattachment, partial-upload recovery, and RAM inspection without RESET;
- CALL/RET execution with A and caller-selected RAM as the result interface.

T28 introduced loader API v2; T29 through T34 retain it, T35 adds the
compatible refresh command, and T36 corrects its physical row addressing.
Revision names are
kept only where an exact ROM image or its regression is being identified.

## Verification

Run the exact-image checks from the repository root:

```sh
bash sync/jukuravi_t28_check.sh
bash sync/jukuravi_t31_check.sh
bash sync/jukuravi_t32_check.sh
bash sync/jukuravi_t35_check.sh
bash sync/jukuravi_t36_check.sh
```

The T28 suite pins the reference implementation of loader API v2. The T31
suite pins the currently burned image and executes the uploaded speaker demo
through the real host/cosim PTY path. The same host code is used for cosim and
the physical serial port. The T32 suite additionally executes all eight
upper-ROM entries, reattaches after each one, and verifies its unique RAM
marker. The T35 suite preserves the historical binary and physical captures.
The T36 suite derives CPU A0..A6 from the drawings/datasheet, proves a complete
128-row sweep, performs a 1,025-byte verified upload and idle reattach,
exercises every refresh operation and torn-disable fallback, and requires exact
T35 to decay as the one-row negative control while preserving T34 and T35. It
also pins both physical T36 sessions and reproduces the clean-boot/raw-fail
D57 channel-2 signature in focused cosim.

The diagnostic ladder, fault injection coverage, image hashes, and older ROM
revisions are documented in [`firmware/README.md`](firmware/README.md). That
history is retained because it identifies reproducible binaries and isolates
which hardware test first introduced each behavior; it is not part of the
normal bench workflow.
