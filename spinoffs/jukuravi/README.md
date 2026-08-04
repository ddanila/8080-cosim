# Jukuravi diagnostic ROM and host

Jukuravi is a diagnostic and recovery environment for the original Juku
`.009` processor board. The T31 ROM tests the board, exposes loader API v2 over
the onboard 8251, and remains resident while the host uploads and calls 8080
snippets in RAM.

The physical reference system is Arvutimuuseum board `CS00015`. Its validated
T31 run, known D55 fault, transport benchmark, upper-D15 data/fetch diagnostic,
and uploaded speaker demo are recorded in
[`T31-PHYSICAL.md`](T31-PHYSICAL.md).

## Current bench setup

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

T31 and every committed diagnostic image are generated artifacts with pinned
checksums. Build and ROM-version details live in
[`firmware/README.md`](firmware/README.md).

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

T28 introduced loader API v2; T29, T30, and T31 retain it. Revision names are
kept only where an exact ROM image or its regression is being identified.

## Verification

Run the exact-image checks from the repository root:

```sh
bash sync/jukuravi_t28_check.sh
bash sync/jukuravi_t31_check.sh
```

The T28 suite pins the reference implementation of loader API v2. The T31
suite pins the currently burned image and executes the uploaded speaker demo
through the real host/cosim PTY path. The same host code is used for cosim and
the physical serial port.

The diagnostic ladder, fault injection coverage, image hashes, and older ROM
revisions are documented in [`firmware/README.md`](firmware/README.md). That
history is retained because it identifies reproducible binaries and isolates
which hardware test first introduced each behavior; it is not part of the
normal bench workflow.
