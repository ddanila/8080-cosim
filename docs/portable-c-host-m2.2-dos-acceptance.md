# Pocket8086 DOS host M2.2 desk acceptance

Status: **DESK COMPLETE — PHYSICAL M2.3 QUALIFICATION REQUIRED**

This report freezes the automatable acceptance boundary for the 16-bit DOS
build of the production C Juku host. It proves that the same admitted protocol
core builds and runs as an 8086 DOS executable through both supported boot
paths. It does not claim Pocket8086 performance or physical CS00015 behavior;
those are the next M2.3 gate.

## Locally owned toolchain

The repository vendors the unmodified official Open Watcom V2 `Current-build`
C/C++ distribution published on 2026-08-20. The archive is stored with Git
LFS, verified before use, and expanded only into the ignored `.tools/` tree.

| identity | value |
| --- | --- |
| upstream source commit | `cf43271464fdd57065d3d72de8ca917c55c6a887` |
| vendor asset | `open-watcom-v2-c-linux-x64-20260820` |
| vendor bytes | `129055748` |
| vendor SHA-256 | `f83c158176f740ec656394a1ec531e2e6d8b78ebdfa4496460f9a0e457475e85` |
| C compiler | Open Watcom C x86 16-bit 2.0 beta, 2026-08-20 02:17:35 |
| linker | Open Watcom Linker 2.0 beta, 2026-08-20 02:13:42 |

`tools/bootstrap-open-watcom.sh` and `tools/open-watcom-env.sh` are implemented
here. There is no Kolobok checkout, build step, downloaded helper, or runtime
dependency. Both the DOS and future Win32 ports use this one pinned compiler
lineage.

## Accepted executable

The build command is:

```sh
sync/jukuhost_dos_build.sh
```

It selects the 8086 instruction set, large memory model, C99 parsing,
optimization, a 24 KiB stack, warning level 4, and warnings as errors. Two
clean output directories produce byte-identical executables.

| property | result |
| --- | --- |
| file | `build/dos/JUKUHOST.EXE` |
| size | `78676` bytes |
| SHA-256 | `6a8b72e198614fbd56fa1be525a0818b946315ccd69bedc3395270a1d2a4f459` |
| linker memory image | `101744` bytes |
| DGROUP | `0x85a0` = 34,208 bytes |
| stack | `0x6000` = 24,576 bytes |
| reported available allocation at start/stop | 31,066 / 31,066 bytes in the DOSBox-X workload |
| timer | BIOS tick plus latched PIT channel 0, reported 1 ms resolution |

The equal start/stop allocation values are a leak check at the session
boundary, not a measured peak high-water mark. DOSBox-X fixed-cycle time is
also deliberately not reported as Pocket8086 performance.

## Architecture admitted for DOS

The protocol, bootstrap, session, configuration, evidence, media, journal, and
SHA-256 sources remain shared with Linux. DOS adds only platform services:

- direct COM1/COM2 UART register access, with saved/restored divisor, line
  control, modem control, and interrupt-enable state;
- explicit 9,600/8O1 and 19,200/8N1 or 8O1 programming, FIFO detection,
  receive clearing on a framing transition, TX drain, bounded polls, and UART
  line-error counters;
- a wrap-safe BIOS/PIT clock and idle polling;
- local `CON` input/output, with F10 as an idle-only clean exit;
- DOS filesystem synchronization and file-backed media access.

A: and B: are never allocated as complete memory buffers. Identity hashes are
streamed; A: snapshot creation is file-to-file; logical records are read and
written on demand; and native cylinder/head B: offsets are translated lazily.
This removes the 400/800 KiB allocation assumption that cannot hold in a
16-bit process. The shared journal state machine and malformed-input tests
remain covered by the Linux M2/core gates; the DOS C8 run additionally proves
the concrete snapshot, identity, log, capture, and file-backed read paths.

## Self-contained Pocket directory

After building, run:

```sh
tools/package-jukuhost-dos.py
```

The packager verifies every selected input against the adjacent
`cpm-plus-juku` C8 manifest before producing `build/dos-package/`. It contains
only 8.3-safe names: `JUKUHOST.EXE`, `JUKUHOST.INI`, `JUKU.BAT`, `SYSTEM.BIN`,
`FAST16.BIN`, `BASE.IMG`, `APPS.JUK`, `README.TXT`, and `MANIFEST.SHA`.

Copy that directory to the Pocket8086 and run either command with no options:

```bat
JUKUHOST
JUKU.BAT
```

The package defaults to COM1, local `CON`, C8 direct Fastboot at 19,200/8N1,
NetDisk v3 at 19,200/8O1 with three-record read-ahead, writable snapshot A:,
read-only native B:, text logging, and binary capture. F10 exits cleanly while
the session is idle.

## Automated acceptance

The complete repeatable gate is:

```sh
sync/jukuhost_dos_check.sh
```

It performs four materially different checks:

1. two independent warning-as-error builds and a byte comparison;
2. the actual 16-bit `JUKUHOST.EXE --selftest` under headless DOSBox-X with an
   8086 CPU profile;
3. the actual EXE through emulated COM1 and a paced TCP/PTTY bridge to the Juku
   simulator, completing stock Janet bootstrap at 9,600/8O1 and installing the
   CP/M 2.2 payload byte-for-byte at `B400h` before its `CA00h` entry;
4. the same executable and COM1 path against the C8 ROM, completing or safely
   confirming V16 through NetDisk, serving CP/M Plus over 19,200-baud NetDisk
   v3, returning at least 20 read operations / 60 records, handling
   bidirectional N4, creating the A: snapshot, authenticating and opening
   native B:, and stopping with log/capture evidence and zero host UART errors.

The accepted C8 run recorded 23 reads, 69 returned records, 279 total N3/N4
requests, 2,527 RX bytes, 14,440 TX bytes, one protocol-level retry, and zero
UART line errors. The harness paces each 8O1 byte at its physical wire duration
because DOSBox-X otherwise batches TCP data into its emulated 16550 faster than
a real serial line.

DOSBox-X's mounted-directory backend returns `ENOENT` for DOS commit
`INT 21h/AH=68h` after successfully writing a file. The DOS platform accepts
only that exact error and still closes the file; every other commit error
remains fatal. A physical DOS implementation therefore retains the stronger
commit behavior. DOSBox-X may also report several RX overruns before the host
opens COM1 because the simulator emits early readiness bytes while the slow
emulated CPU authenticates artifacts; COM1 open clears that stale FIFO and the
host's final UART error count must remain zero.

## M2.3 physical gate

M2.2 authorizes copying this package to Pocket8086; it does not promote that
machine as a production host. On the Pocket8086 physical COM1 and CS00015, use
the exact package manifest and retain `JUKUHOST.LOG` plus `JUKUHOST.CAP` while
checking:

- repeated C8 cold boots to the CP/M prompt;
- A: directory/read and controlled snapshot write, B: directory/read, N4
  input/output, diagnostics, and warm boot;
- clean F10 shutdown with no journal residue;
- delayed-host startup, host replacement/reconnect, and target reset;
- boot time, disk latency, request/record counts, retries, UART errors, and
  available memory against the native-Linux M2.1 baseline.

Only that evidence can close M2.3 and allow the Win32/Wine M3 work to begin.
