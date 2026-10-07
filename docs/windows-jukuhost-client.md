# Windows Juku host client

`JUKUWIN.EXE` is the self-contained Windows host for a Juku using the stock,
C11, or C12 JukuNet ROM. It includes the approved CP/M boot systems, JF17
stock helper, and JF16 C11/C12 helpers. Disk images remain ordinary external
files.

## Download the Windows bundle

Open [Releases](https://github.com/ddanila/8080-cosim/releases), select a
**Windows host** build, and download **jukuwin-windows-full-cpm.zip**.
For an existing installation, download just **JUKUWIN.EXE**, close the host,
and replace the old EXE. Keep the existing INI, disk images and working snapshots;
no extra DLLs or boot files are required.

The release page and ZIP are public without signing into GitHub and have no
automatic expiry. Each development prerelease identifies its source commit
and includes installation instructions and a ZIP checksum.

The [Windows host bundle workflow](https://github.com/ddanila/8080-cosim/actions/workflows/windows-host.yml)
publishes a release after all checks pass for relevant pushes to master or
manual runs on master. Pull requests only produce Actions artifacts.
Those artifacts require GitHub login and are retained for 90 days.

The ZIP contains a **files/** folder ready to copy to a formatted 1.44 MB
floppy and **JUKUWIN.IMG**, a complete FAT12 image for disk-writing tools.
This is a transfer disk. Copy its files into a writable Windows hard-disk
folder before starting the host, so snapshots and captures have room to grow.

The bundle includes `CPM3.IMG`: the full CP/M development A: image, with 33
files and 190 KiB free inside CP/M. It includes the full utilities plus ED,
SID, PATCH, HEXCOM, command history, diagnostics, HELP and example source/HEX.
This is the approved full development collection, not the minimal recovery
disk. The included `README.TXT` lists every file. The optional B: image is
left empty so music or application media can be supplied separately.

The bundled INI preselects **Stock ROM**, automatic serial selection, and a
writable snapshot of `CPM3.IMG`; it does not start listening automatically.
Select C11 or C12 instead if that is the ROM fitted in your machine.
`MANIFEST.JSN`, `SHA256.TXT` and `LICENSE.TXT` travel with the files.

CI checks the native components, two byte-identical PE builds, the Win95
import boundary, payload identities, the full-media hash, floppy capacity,
and byte-for-byte FAT12 readback. It then runs the actual EXE selftest on
Windows Server 2022, including repeated GUI Listen, worker teardown, early
failure logging and session logging, before publishing the final artifact.
This does not replace physical serial or Windows 95 testing.

The [original Windows 95 VM acceptance report](windows-jukuhost-client-win95-acceptance.md)
records a successful self-test, configuration save, and interactive C12 CP/M
session. Physical
Windows serial hardware qualification remains outstanding.

## First start

Place `JUKUWIN.EXE` and `JUKUWIN.INI` in a writable folder. Double-click the
EXE, then:

1. choose **C12**, **C11**, or **Stock ROM**;
2. select the serial adapter;
3. browse to a 400 KiB A: image;
4. optionally browse to a native 800 KiB B: image;
5. leave A: in **Snapshot** mode for normal writable use; and
6. press **Listen**, then power or reset the Juku if necessary.

Select **C12** for a machine fitted with the C12 ROM and matching CP/M system.
**C11** selects the embedded C11 system and helper; its
[physical acceptance remains pending](c11-session-recovery.md#qualification).
Both wait without
transmitting until they see their checked ROM beacon or a complete NetDisk
request. This means either can safely attach while CP/M is already running or
silently playing music. Select the mode that exactly matches the installed
ROM; the embedded system and Fastboot pair changes with it.

**Stock ROM** stays at 9,600/8O1 for Janet, the compressed JF17 transfer, and
NetDisk. Like C11/C12, it first listens without transmitting, attaches to a
checked live NetDisk session, and recognizes a new checked Janet request as a
target reset. After a stock-ROM cold start or hardware reset, select **T → N**
on the Juku to enter Janet network boot. The host reloads CP/M when that
checked request arrives; it does not send the monitor keys. See
[the stock boot guide](janet-fastboot.md) for station-prompt settings.

Press **Stop** before changing the mode, adapter, or disk images. Closing the
window while active requests the same clean stop and waits for the current
serial or media operation to finish. Serial read and write calls have timeouts,
and transmitter draining has a ten-second limit. A write spanning several
calls can take longer than one call's timeout. File reads, writes and flushes
have no application timeout, so a stalled filesystem can delay stopping or
closing.

Press **Stop** and wait for the session to finish before shutting down Windows.
If Windows requests shutdown while a session is active, the host requests Stop
and refuses that shutdown request. Retry shutdown after the host is idle.

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
A resumed working copy must have the correct size; its modified contents are
not required to match the base hash.

Every write uses the CRC-protected `.jhj` transaction journal. At the next
writable session, an incomplete transaction restores its saved previous
record; a completed transaction restores its saved new record. Invalid or
unreadable journals stop the session. This recovers the recorded transaction,
not arbitrary filesystem damage or external edits to the image.

Read-only mode serves A: without writes. B: accepts only an 819,200-byte native
cylinder/head image and is always read-only.

Do not copy, replace, or edit a mounted image while the host is listening.
The program opens writable media exclusively and reports a conflict instead
of sharing it with another writer.

## Console and evidence

The left transcript is the N4 CP/M console. Type a command in the input field
and press **Send**; a carriage return is added automatically. The right pane
shows host diagnostics and recovery transitions.

The program creates `JUKUWIN.LOG` beside the EXE as soon as it
starts, before loading the INI or creating a worker. If that folder is not
writable, it uses `JUKUWIN.LOG` in the Windows temporary folder instead. The
initial diagnostic pane shows the chosen path. The file appends timestamped
startup, configuration, Listen/Stop, worker failure and session diagnostics,
flushing every entry. It persists across restarts; you can delete it while the
host is closed. Send this file when reporting a startup or Listen failure.
If neither location can be written, the application displays an error.

Listen failures include the Windows error number, description and C runtime
error number.

Each run creates a distinct timestamped folder beneath the configured
`logs` directory containing `JUKUHOST.LOG` and, by default, `JUKUHOST.CAP`.
The capture is the same CRC-protected byte/event format used by the Linux and
DOS host. Evidence failure stops a run rather than silently discarding the
record.

After a clean GUI stop, cleanup uses `keep_sessions` (default 20) to retain
the newest recognized session folders by timestamped name. Cleanup scans at
most 10,000 recognized folders; if more exist, it sorts only that subset and
leaves folders outside the scan untouched. It attempts to delete
`JUKUHOST.LOG` and `JUKUHOST.CAP` in older folders, including earlier failed
sessions, then removes empty folders. Extra files do not protect those logs
or captures. Copy important sessions elsewhere or set `keep_sessions=0` to
disable cleanup. Headless runs do not perform this cleanup; the separate
startup log `JUKUWIN.LOG` is unaffected.

## Configuration

`JUKUWIN.INI` is strict ASCII text. Relative image and evidence paths are
resolved beside the INI file. The UI saves settings when **Listen** is pressed
and uses no registry settings. See the
[implementation guide](windows-jukuhost-client-implementation.md) for file
replacement and recovery details.

The example below selects C12, enables automatic listening, and mounts an
optional B: image. Adjust it for the fitted ROM and available media; the
bundled INI uses the Stock ROM/manual-start settings described above.

```ini
[juku]
mode=c12
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
ejects B:. `keep_sessions` accepts 0 through 10000.

For automated diagnosis, `JUKUWIN.EXE --selftest` verifies the portable core,
configuration round trip, and every embedded payload on two successive worker
threads without opening a port. It also writes its results to `JUKUWIN.LOG`.
`JUKUWIN.EXE --headless --config PATH` serves the same configuration without
creating a window; it is intended for controlled tests and support work.
`--disk-timeout SECONDS` gives that headless mode a bounded NetDisk test run;
zero, which is the default, serves without a time limit.

## Local Wine end-to-end check

Developers can run the actual PE against the stock, C11, and C12 simulators:

```sh
sync/jukuhost_win32_wine_e2e.sh
```

The default invocation rebuilds `JUKUWIN.EXE` first. To test an existing binary
without rebuilding it, pass its path:

```sh
sync/jukuhost_win32_wine_e2e.sh /path/to/JUKUWIN.EXE
```

It needs 32-bit Wine,
`wineboot`, Xvfb, `socat`, Python 3, a C compiler, and the sibling
`cpm-plus-juku` stock recovery and C11/C12 outputs, including their disk images
and the application B: image (or set `CPM_PLUS_JUKU_ROOT`). It creates an
isolated 32-bit Wine prefix and retained evidence under `build/`. This longer
test is developer-invoked and is deliberately not part of the ordinary CI
gate.

Wine's PTY backend accepts the requested odd-parity DCB but reports no parity
on readback. The executable detects Wine and emits a warning before continuing
with byte-level emulation. Real Windows keeps strict `8O1` readback validation;
the Wine pass therefore does not qualify a physical serial adapter or parity.

## Qualification boundary

The package manifest records the EXE size and hash, the pinned compiler label,
the embedded payload catalog, and the checkout revision at packaging time.
The release workflow builds and packages the same checkout. For local packages,
`tools/package-jukuhost-windows.py` copies an existing EXE without rebuilding
it or verifying its source revision; build it from the intended checkout first.
The portable folder's README links to documentation at that packaging revision.
A Wine or simulator pass proves the desk behavior only. Consult
[windows-jukuhost-client-implementation.md](windows-jukuhost-client-implementation.md)
for current physical Windows and Windows 95 qualification status.
