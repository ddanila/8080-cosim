# Windows Juku host client

`JUKUWIN.EXE` is the self-contained Windows host for a Juku using either the
stock ROM or the C11 JukuNet ROM. It includes the approved CP/M boot system,
JF15 stock helper, and JF16 C11 helper. Disk images remain ordinary external
files.

## First start

Place `JUKUWIN.EXE` and `JUKUWIN.INI` in a writable folder. Double-click the
EXE, then:

1. choose **C11** or **Stock ROM**;
2. select the serial adapter;
3. browse to a 400 KiB A: image;
4. optionally browse to a native 800 KiB B: image;
5. leave A: in **Snapshot** mode for normal writable use; and
6. press **Listen**, then power or reset the Juku if necessary.

**C11** is the normal mode for the C11 ROM. It waits without transmitting
until it sees either a checked C11 beacon or a complete NetDisk request. This
means it can safely attach while CP/M is already running or silently playing
music.

**Stock ROM** waits for the 9,600-baud Janet loader, installs the embedded
JF15 helper, and continues at 19,200 baud. It requires a fresh stock-ROM boot
request.

Press **Stop** before changing the mode, adapter, or disk images. Closing the
window while active requests the same clean stop and waits for the current
bounded serial/media operation to finish.

## Serial adapters and changing COM numbers

The port list stores a Windows device-instance identity when the driver
provides one. The same adapter can therefore be found after its COM number
changes. If exactly one adapter is present, **Automatic** can select it.

The tested Prolific `067B:2303` adapter has no unique USB serial number. Its
Windows identity may change when it is moved to another physical USB socket.
If two indistinguishable adapters are present, Juku Host deliberately asks for
a selection instead of guessing. Refresh the list and select the intended
adapter.

## Disk safety

A: accepts a logical 409,600-byte image. Snapshot mode authenticates and keeps
the selected image immutable, creating or resuming a sibling `-WORK` image.
Every write uses the existing CRC-protected `.jhj` transaction journal. An
interrupted transaction is recovered at the next start.

Read-only mode serves A: without writes. B: accepts only an 819,200-byte native
cylinder/head image and is always read-only.

Do not copy, replace, or edit a mounted image while the host is listening.
The program opens writable media exclusively and reports a conflict instead
of sharing it with another writer.

## Console and evidence

The left transcript is the N4 CP/M console. Type a command in the input field
and press **Send**; a carriage return is added automatically. The right pane
shows host diagnostics and recovery transitions.

Each run creates a distinct timestamped folder beneath the configured
`logs` directory containing `JUKUHOST.LOG` and, by default, `JUKUHOST.CAP`.
The capture is the same CRC-protected byte/event format used by the Linux and
DOS host. Evidence failure stops a run rather than silently discarding the
record.

## Configuration

`JUKUWIN.INI` is strict ASCII text. Relative image and evidence paths are
resolved beside the INI file. The UI uses a committed temporary file and
atomic replacement where the OS provides it; the legacy fallback retains a
recovery backup. It saves when **Listen** is pressed and uses no registry
settings.

```ini
[juku]
mode=c11
serial=auto
serial_id=
auto_listen=yes

[drive_a]
image=CPM3.IMG
mode=snapshot
working=CPM3-WORK.IMG

[drive_b]
image=JUKEBOX.JUK

[evidence]
directory=logs
capture=yes
verbose=no
keep_sessions=20
```

`serial` may instead be an explicit `COM1` through `COM256`. An empty B: image
ejects B:. `keep_sessions=0` disables automatic evidence retention cleanup.

For automated diagnosis, `JUKUWIN.EXE --selftest` verifies the portable core,
configuration round trip, and every embedded payload without opening a port.
`JUKUWIN.EXE --headless --config PATH` serves the same configuration without
creating a window; it is intended for controlled tests and support work.
`--disk-timeout SECONDS` gives that headless mode a bounded NetDisk test run;
zero, which is the default, serves without a time limit.

## Qualification boundary

The package manifest states exactly which compiler, source revision, embedded
payloads, and EXE hash produced the release. A Wine or simulator pass proves
the desk behavior only. Consult
[windows-jukuhost-client-implementation.md](windows-jukuhost-client-implementation.md)
for current physical Windows and Windows 95 qualification status.
