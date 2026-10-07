# Windows Juku host implementation and qualification

`JUKUWIN.EXE` is a 32-bit ANSI Win32 GUI built with the pinned Open Watcom V2
compiler. It runs the shared C host core and runner; the operator instructions
are in [windows-jukuhost-client.md](windows-jukuhost-client.md).

## Current implementation

- Stock, C11 and C12 modes use embedded boot payloads with hash validation.
  Configuration defaults and the source INI select C12; the floppy packager
  selects Stock ROM for its bundled development disk.
  The source revision, sizes and hashes are maintained in
  [payload-manifest.json](../host/windows/payload-manifest.json).
- Stock/JF17 stays at 9,600/8O1 through Janet, compressed boot and NetDisk,
  allowing automatic target-reset recovery. C11/C12 use their separate
  19,200-baud V16/NetDisk recovery loops.
- A shared worker runner owns serial I/O, disk service and captures. The GUI
  receives copied callbacks through window messages and requests cooperative
  cancellation for Stop and close. An active session refuses the current
  Windows shutdown request while requesting Stop; shutdown is allowed when
  idle. Closing waits for the worker before destroying the window.
- Serial selection supports explicit COM names and stable device-instance IDs.
  Ambiguous unidentified adapters require selection.
- A: supports snapshot or read-only access; B: is read-only. Writable images
  are opened exclusively; read-only opens permit sharing. Writes use
  the shared transaction journal. Configuration uses flushed temporary files
  and a backup/restore fallback where atomic replacement is unavailable.
- Each run gets its own evidence directory, with `JUKUHOST.LOG` and optional
  `JUKUHOST.CAP`. Startup and session diagnostics are also recorded in
  `JUKUWIN.LOG`, opened beside the executable or in the temporary directory
  if that location is unavailable.
- The runtime import boundary is checked against
  [win95-imports.txt](../host/windows/win95-imports.txt). Builds are normalized
  and compared byte-for-byte. The portable package records build identity in
  `MANIFEST.json`; the released floppy bundle carries it as `files/MANIFEST.JSN`
  with the CP/M image provenance added.

## Verified scope

At startup, a missing INI selects a parseable `.tmp` file, otherwise a
parseable `.bak` file, beside that INI. If no candidate is found or moving
the selected candidate fails, the GUI starts with defaults; a failed move
does not retry the other candidate. An existing invalid INI reports an error;
it does not trigger backup recovery. Saving rewrites the configuration,
so comments and original formatting are not retained.

| Environment | Evidence | Limit |
| --- | --- | --- |
| Native build/API shims | Payload, configuration, device selection, partial I/O, cancellation, timer, file replacement and PE/package checks | Does not execute native Windows drivers |
| Windows Server 2022 CI | Actual PE self-test, repeated GUI Listen, Stop during reconnect, early failure and session logs | Uses failure fixtures and an unavailable COM port; no serial-to-board session |
| Wine | Executable self-test and headless stock/C11/C12 simulator boot, A: reads/snapshot creation, mounted B: in C11/C12, captures and timeout-driven clean stop | No required B: read, target-reset, reconnect or GUI Stop/close test; parity-readback exception provides byte emulation, not physical UART qualification |
| Original Windows 95 guest | Executable self-test, GUI, C12 boot, DIR and target-reset recovery | COM1 connects to the simulator; no physical adapter or board was used |

The Wine and guest results are recorded in
[Wine acceptance](windows-jukuhost-client-wine-acceptance.md) and
[Windows 95 guest acceptance](windows-jukuhost-client-win95-acceptance.md).
Their named binary hashes identify the tested artifacts and are not claims
about the latest release binary.

## Remaining qualification

Real current-Windows and physical Windows 95 serial hardware still need the
full cold-boot, disk/write safety, reconnect/reset, GUI and endurance matrix.
The guest result does not complete either physical platform gate.

```sh
sync/jukuhost_win32_check.sh
sync/jukuhost_win32_wine_e2e.sh
```

The first command is the desk/reproducibility gate. The second executes the
actual PE against the stock, C11 and C12 simulators with the documented Wine
prerequisites. If `wine`, `wineboot`, `xvfb-run` or `socat` is missing, the
wrapper prints `SKIP` and exits 0; that result provides no Wine acceptance
evidence. The [Windows Actions workflow](../.github/workflows/windows-host.yml) also
runs [the native runtime guard](../tools/check-jukuwin-runtime.ps1) before
publishing the checked build.
