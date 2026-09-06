# Windows Juku host client

`JUKUWIN.EXE` is the self-contained Windows host for a Juku using the stock,
C11, or C12 JukuNet ROM. It includes the approved CP/M boot systems, JF17
stock helper, and JF16 C11/C12 helpers. Disk images remain ordinary external
files.

## Download the Windows bundle

Open [Releases](https://github.com/ddanila/8080-cosim/releases), select a
**Windows host + full CP/M** build, and download **jukuwin-windows-full-cpm.zip**.
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
Windows Server 2022 before publishing the final artifact. This does not
replace physical serial or Windows 95 testing.

The [original Windows 95 VM acceptance report](windows-jukuhost-client-win95-acceptance.md)
records a successful self-test, configuration save, and interactive C12 CP/M
session after fixing legacy API and serial-write compatibility. Physical
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

**C12** is the default for the latest ROM and matching CP/M system. **C11**
retains compatibility with the physically accepted C11 ROM. Both wait without
transmitting until they see their checked ROM beacon or a complete NetDisk
request. This means either can safely attach while CP/M is already running or
silently playing music. Select the mode that exactly matches the installed
ROM; the embedded system and Fastboot pair changes with it.

**Stock ROM** stays at 9,600/8O1 for Janet, the compressed JF17 transfer, and
NetDisk. Like C11/C12, it first listens without transmitting, attaches to a
checked live NetDisk session, and recognizes a new checked Janet request as a
target reset. It then reloads CP/M automatically without a baud-rate guess.

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
ejects B:. `keep_sessions=0` disables automatic evidence retention cleanup.

For automated diagnosis, `JUKUWIN.EXE --selftest` verifies the portable core,
configuration round trip, and every embedded payload without opening a port.
`JUKUWIN.EXE --headless --config PATH` serves the same configuration without
creating a window; it is intended for controlled tests and support work.
`--disk-timeout SECONDS` gives that headless mode a bounded NetDisk test run;
zero, which is the default, serves without a time limit.

## Local Wine end-to-end check

Developers can run the actual PE against the stock, C11, and C12 simulators:

```sh
sync/jukuhost_win32_wine_e2e.sh
```

The default invocation rebuilds `JUKUWIN.EXE` first. It needs 32-bit Wine,
`wineboot`, Xvfb, `socat`, Python 3, a C compiler, and the sibling
`cpm-plus-juku` C11/C12 outputs (or `CPM_PLUS_JUKU_ROOT`). It creates an
isolated 32-bit Wine prefix and retained evidence under `build/`. This longer
test is developer-invoked and is deliberately not part of the ordinary CI
gate.

Wine's PTY backend accepts the requested odd-parity DCB but reports no parity
on readback. The executable detects Wine and emits a warning before continuing
with byte-level emulation. Real Windows keeps strict `8O1` readback validation;
the Wine pass therefore does not qualify a physical serial adapter or parity.

## Qualification boundary

The package manifest states exactly which compiler, source revision, embedded
payloads, and EXE hash produced the release. A Wine or simulator pass proves
the desk behavior only. Consult
[windows-jukuhost-client-implementation.md](windows-jukuhost-client-implementation.md)
for current physical Windows and Windows 95 qualification status.
