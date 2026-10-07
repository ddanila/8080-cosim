# Windows Juku host client Wine acceptance

Date: 2026-09-04

Qualified source state: M8 reset-safe stock recovery milestone

Result: **PASS at the local Wine protocol boundary**

This extends the 2026-09-03 non-Windows desk acceptance by executing the
actual 32-bit Open Watcom PE. It does not claim GUI automation, native Windows
driver behavior, physical parity or timing, the USB adapter, CS00000, or
Windows 95 qualification.

## Environment and artifact

- Host: Linux 7.0.0-30-generic, x86-64.
- Runtime: Wine 10.0 in a newly created `WINEARCH=win32` prefix.
- Serial bridge: two raw PTYs connected by `socat`; Wine `COM1` is registered
  and linked to the host side.
- EXE: 207,360 bytes, SHA-256
  `ea556fde96e5d7faa34fd04f2065eba647f39c49aee3e30c68f56dff74f42316`.
- Compiler bootstrap SHA-256:
  `f83c158176f740ec656394a1ec531e2e6d8b78ebdfa4496460f9a0e457475e85`;
  pinned Open Watcom source
  `cf43271464fdd57065d3d72de8ca917c55c6a887`.

The exact accepted commands were:

```sh
sync/jukuhost_win32_check.sh
python3 tests/jukuhost_stock_recovery_cosim_test.py
sync/jukuhost_win32_wine_e2e.sh build/win32-wine-e2e/JUKUWIN.EXE
```

The first command passed portable payload/configuration/device-selection
tests, the Win32 API shim, two byte-identical builds, PE/import/resource audit,
the real PE self-test under Wine, and exact package validation. The second
command kept one native host process alive across a simulated stock target
restart and reached `A>` before and after it. The third executed the PE in
stock, retained C11 and C12 protocol sessions. The complete Wine protocol
run is local-only.

## Rerunning the current source

From the repository root, run:

```sh
sync/jukuhost_win32_wine_e2e.sh
```

Without an argument, the wrapper builds
`build/win32-wine-e2e/JUKUWIN.EXE` before running the protocol harness.
An optional EXE path tests that existing artifact without rebuilding it.
The recorded command above assumes that artifact already exists.

The wrapper requires `wine`, `wineboot`, `xvfb-run`, and `socat` on `PATH`.
The protocol harness also requires a C compiler and generated artifacts in
the sibling `../cpm-plus-juku/out/` directory (override the checkout with
`CPM_PLUS_JUKU_ROOT`). It does not build those artifacts:

- Stock: `cpm-plus-juku.img`, `cpm-plus-juku-stock-recovery-system.bin`,
  and `cpm-plus-juku-stock-recovery-fastboot-v17.bin`.
- C11 and C12: `cpm-plus-juku-{c11,c12}-full.img`,
  `cpm-plus-juku-network-rom-{c11,c12}-system.bin`, and
  `cpm-plus-juku-network-rom-{c11,c12}-fastboot-v16.bin`.
- Shared B: image: `cpm-plus-juku-apps.juk`.

Use that checkout's build instructions to generate the files before running
the harness. The ROM images come from this repository.

The wrapper prints `SKIP` and exits zero if any of its four runtime tools is
missing, before building or checking
the EXE path. Exit zero alone therefore does not prove a protocol run.
The ordinary desk gate requires only the first three for its Wine self-test;
its build, API-shim, PE and package checks still run without Wine.

## Accepted protocol evidence

The recorded run covered stock passive Janet/JF17/NetDisk at 9,600 baud,
and C11/C12 passive beacon/V16/NetDisk at 19,200 baud, with zero retries and
UART errors in all three cases. The current harness checks clean exit,
boot/service evidence, a host-reported disk-read request, A: working-image
size and unchanged A: base contents. It does not assert exact timing,
request counts or working-copy hashes.

Each case starts one headless host and one simulator. Disk service ends through
`--disk-timeout` (20 seconds for stock, 8 for C11/C12). The harness does not
restart either process or interrupt the serial bridge, so its clean-stop
assertion does not cover GUI Stop/close, target-reset recovery or reconnect.

All three cases mounted a 409,600-byte A: base as a new snapshot working image,
served disk reads, stopped cleanly with host exit zero, retained a raw capture,
and passed capture framing/CRC validation and host-event conversion. The C11 and C12 cases also mounted
the 819,200-byte B: image. Base and working-copy identities matched after each
read-only workload:

- stock A: `b4402dc9be86fef9532e61fff491dc3b93dc0db40e68d575c89aab083160bec1`;
- C11 A: `59174921a4504283dd0311ef07324a7e3db4f4c0bd7ebac4cd7304097e8ab2fa`;
- C12 A: `56e0db2f203bd813e609298b5ef1ff01177c97dbb386d894b38251580a1c1fc9`.

The Wine stock run attached from a checked directed Janet poll, transferred
the complete JF17 body, and then served NetDisk requests. All three runs
missed an optional final reply and used
valid NetDisk requests as the end-to-end confirmation; no compressed body was
resent. Capture conversion derives JF17 versus V16 from host events, hashes the
payload files selected by the harness, and records its specified disk rate. It does not
independently authenticate payloads from RX/TX bytes; see
[capture conversion](portable-c-host-implementation.md#capture-conversion).

## Wine-specific boundary

Wine 10 accepted `SetCommState` for `8O1` on the PTY but returned `8N1` from
`GetCommState`. The host dynamically detects Wine, permits only that exact
odd-to-none parity readback mismatch, and prints a byte-emulation warning.
The API-shim regression proves that the same mismatch is rejected when Wine
is not detected. Baud, byte size, stop bits, flow control, and error policy
remain verified.

Wine 10 also required the `HKLM\Software\Wine\Ports` mapping for `COM1` in
addition to the traditional prefix symlink. The harness installs both mappings
inside its disposable prefix and refreshes Wine before each case.

## Remaining gates

W4 still requires the exact PE on current Windows with the real adapter and
CS00000, including UI operation, stable device identity, cold/warm boots,
A:/B:, controlled writes, N4, reconnect, shutdown, and endurance evidence.
Windows 95 guest execution has since been recorded in
[the guest acceptance report](windows-jukuhost-client-win95-acceptance.md).
That serial path uses a simulator, so physical Windows 95 serial qualification
remains separate. This Wine record qualifies its named PE and payloads; use
[the operator guide](windows-jukuhost-client.md) for the current build.
