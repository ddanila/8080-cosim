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
[`CS00024-PHYSICAL.md`](CS00024-PHYSICAL.md). The current T36 diagnosis
and remaining D57 channel-2 discriminator are in
[`../../docs/cs00024-t36-diagnosis.md`](../../docs/cs00024-t36-diagnosis.md).
The prepared, not yet executed video-slot refresh experiment — arming the
exact EktaSoft D54/D55 raster from the T36 loader and holding RAM
unrefreshed — is specified in
[`RASTER-REFRESH-EXPERIMENT.md`](RASTER-REFRESH-EXPERIMENT.md) with its
runner [`raster_retention.py`](raster_retention.py). The implemented
EktaSoft-based remix ROM that embeds the Jukuravi loader as a monitor
command is specified in
[`EKTA37-REMIX-PLAN.md`](EKTA37-REMIX-PLAN.md).

The separately built, from-scratch network-only successor is in
[`network-rom/`](network-rom/README.md). Its current C12 / ABI 1.5 implementation and release-specific physical scope
are documented there. CS00015's fitted C8 / ABI 1.3 pair is identified in
[the machine profile](../../docs/machines/CS00015.json); its physical
qualification is indexed by [the service record](../../docs/cs00015-service-record.md).

The independent music runtime, tools and physical evidence live in
[JukuPoly](../jukupoly/README.md).

The 2026-08-09 desk audit invalidated the T15/T16/T31/T32 D55 predicate: those
ROMs did not establish the physical D55 clocks before latching their Mode-0
counts. T34 is the first clock-safe D55 functional-path image. Neither
CS00015 nor CS00024 currently has valid evidence that its D55 package is bad;
see
[`../../docs/jukuravi-d55-diagnostic-audit.md`](../../docs/jukuravi-d55-diagnostic-audit.md).

## Current machine configuration

The CS00015 profile, updated 2026-08-21, records fitted JukuNet C8 / ABI 1.3.
The donor D6 `.038` remains fitted, the original D8 `.039` is restored, and
D1 is repaired. [The service record](../../docs/cs00015-service-record.md)
owns the physical changes and firmware qualifications. The preceding Ekta4402
API-v2 `J` attaches are retained in
[their evidence record](sessions/cs00015-ekta4402-j-physical/README.md).
The T31/T32 diagnostic configurations below are historical setups.

The verified T31 service EEPROM is prepared media, not currently fitted in
CS00015. Its identity and programming evidence are in
[T31 physical acceptance](T31-PHYSICAL.md#service-media-refresh-2026-08-09).

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

The recorded macOS setup used the built-in Apple CP210x driver and stdlib
`termios`, without pyserial or a vendor driver install. Confirm the actual
adapter and device node on another setup; the result is qualified in
[MACOS-BENCH.md](MACOS-BENCH.md).

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

The historical CS00015 investigation isolated a D1 16-bit increment fault;
D1 replacement subsequently produced clean results. To repeat that focused
discriminator after a T32 boot, without another ROM burn:

```sh
python3 spinoffs/jukuravi/probe_a12_increment.py --port /dev/ttyUSB0
```

`CLEAN` means the five register results match the expected increment behavior.
`D1 FAULT CONFIRMED` means they match the repaired CPU's historical signature.
Both recognized results exit 0; `OTHER` exits 2. Read the result label rather
than treating exit 0 as a CPU pass.

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
# Confirm that the resident loader responds without uploading a payload.
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

The [recorded T34 CS00024 tests](CS00024-PHYSICAL.md#t34-cold-boots-and-loader-discriminator-2026-08-09)
passed the short seven-vote CONFIG command, while the longer seven-vote
bootstrap PROBE repeatedly failed strong CRC in the `C000h` parser state. The explicit
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
  short CONFIG recovery after each attempted point, stopping the sweep if
  recovery fails; and
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

A completed batch exits 0 only when no executed core test reports failure and
the boot status passes PIC, PPI, D54, D55, D57 and both compact RAM windows.
Otherwise it reports `COMPLETE WITH FINDINGS` and exits 1. Parser-aging results
and CONFIG recovery are recorded separately in JSON `batch.retention_sweep`;
they do not contribute to that overall verdict, so inspect them even after
`PASS`. Transport or execution errors also exit 1 and preserve completed
results in the session log.

On physical CS00024 the batch measured 1.714065 MHz, then proved that long
uploads can lose their early RAM bytes before RUN. Use [`retention.py`](retention.py)
for the narrower destructive-retention test. It uploads and verifies one
32-byte marker, then repeatedly reads it in the same loader process:

```sh
python3 spinoffs/jukuravi/retention.py --cold --port /dev/ttyUSB0 \
  --address 4D00 --ages 0,20 --loader-guard-ms 0 \
  --log-dir spinoffs/jukuravi/sessions/cs00024-t34-retention
```

Start it before RESET. `--cold` pins T34 `1C/A637`; without `--cold` it attaches
to an already-running API-v2 loader. `--ages` gives ascending target seconds
from completion of the initial verified upload, rather than delays between
reads. An overdue target is read immediately. JSON `retention.samples` records
both the target age and the observed age after each READ completes, including
its transport time.

Loader commands themselves touch RAM and can refresh the tested rows; earlier
reads therefore affect later samples. The physical evidence is not a generic
DRAM benchmark. CS00024 passes when touched about every five seconds but loses mutable
loader state after an untouched interval between roughly 5 and 17 seconds.
See [`CS00024-PHYSICAL.md`](CS00024-PHYSICAL.md) for exact captures and limits.

### T36 refresh and D57 qualification boundary

T35 (`1D/45C4`) increments the high address byte and refreshes physical row
zero repeatedly; it is retained as a negative control, not an all-row solution.
T36 (`1E/C617`) reads `4000h..407Fh` through public `CALL 07A9h`, covering
all 128 physical rows. The exact image identities and refresh ABI are in
[the firmware guide](firmware/README.md) and
[loader API v2](LOADER-API-V2.md).

The completed CS00024 local sweep passed all eight stage/pattern combinations
over `4000h..BFFFh` with no mismatches. It proves the recorded refresh-on
workload, not unrefreshed retention. The earlier interrupted wire sweep has a
narrower captured scope; both records remain in
[CS00024 physical evidence](CS00024-PHYSICAL.md).

The legacy `D57R` channel-2 result is inconclusive: D57 CLK2 is D55's roughly
49.92 Hz `/VER RTR`, and that probe did not wait for a guaranteed clock edge.
The corrected `D57S` probe arms the Ekta raster and waits 64 refresh sweeps
per write. It passed on CS00015. CS00024 still needs this corrected rerun
before diagnosing its channel-2 path, socket or package. `--only-d57` still
runs verified CALL/RET and CPU timing first, then D57; it skips the other
CPU/RAM probes and parser-aging sweep:

```sh
python3 spinoffs/jukuravi/batch.py --port /dev/ttyUSB0 --rom t36 \
  --only-d57 --log-dir spinoffs/jukuravi/sessions/cs00024-t36-d57-followup
```

This focused follow-up does not require rerunning the RAM sweep. See
[the consolidated diagnosis](../../docs/cs00024-t36-diagnosis.md) for its
expected signatures and interpretation.

### Session logs

`host.py` writes `<timestamp>.json` plus matching `.rx.bin` and `.tx.bin`
in the directory selected by `--log-dir`. Multiple runs can share that
directory. Its default is [`sessions/default`](sessions), resolved relative
to `host.py`; an explicit relative path is resolved from the working directory.
The batch and retention runners use the same file format with their own default
directories; check the selected runner's `--help`.
An interrupted process may leave only the raw files. Use a descriptive directory
for an experiment:

```sh
python3 spinoffs/jukuravi/host.py --port /dev/ttyUSB0 \
  --attach-loader --probe-loader \
  --log-dir spinoffs/jukuravi/sessions/t32-probe
```

Preserve committed captures cited by physical records, including
[`T31-PHYSICAL.md`](T31-PHYSICAL.md), [`T32-PHYSICAL.md`](T32-PHYSICAL.md)
and [`CS00024-PHYSICAL.md`](CS00024-PHYSICAL.md).

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
- RUN replay protection for the same execution ID while the ROM's invocation
  cache survives; a new host invocation uses a new ID;
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

The gates bind their named firmware revisions and test the host/cosim path;
they do not establish physical acceptance. T35 remains the one-row refresh
negative control. Use T36 for the corrected 128-row software-refresh contract.
The legacy D57 cosim result does not establish a physical channel-2 fault.

See [the firmware guide](firmware/README.md) for gate scopes, exact-image
hashes, probe selection and hardware boundaries. Historical revision names
identify archived binaries and regressions, rather than additional steps in
the normal bench workflow.
