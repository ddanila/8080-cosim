# Windows Juku host client Wine acceptance

Date: 2026-09-04

Qualified implementation: `244d38addcee4b862a2556c1146ab2b09e1d05ea`

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
- EXE: 176,640 bytes, SHA-256
  `5834c17d115475b7268e93046c643b0b6624dcf5802e4e8d2b485240e01afee5`.
- Compiler bootstrap SHA-256:
  `f83c158176f740ec656394a1ec531e2e6d8b78ebdfa4496460f9a0e457475e85`;
  pinned Open Watcom source
  `cf43271464fdd57065d3d72de8ca917c55c6a887`.

The exact accepted commands were:

```sh
sync/jukuhost_win32_check.sh
sync/jukuhost_win32_wine_e2e.sh build/win32-repro-a/JUKUWIN.EXE
```

The first command passed portable payload/configuration/device-selection
tests, the Win32 API shim, two byte-identical builds, PE/import/resource audit,
the real PE self-test under Wine, and exact package validation. The second
command passed the stock and C11 protocol sessions. The complete protocol run
is intentionally local-only rather than part of ordinary CI.

## Accepted protocol evidence

| Case | Serial path | First disk request | Final service counters |
| --- | --- | ---: | --- |
| stock | Janet at 9,600, V15/NetDisk at 19,200 | 21.369 s | 18 requests, 54 records, 0 retries, 0 UART errors |
| C11 | passive beacon and V16/NetDisk at 19,200 | 8.645 s | 18 requests, 51 records, 0 retries, 0 UART errors |

Both cases mounted a 409,600-byte A: base as a new snapshot working image,
served disk reads, stopped cleanly with host exit zero, retained a raw capture,
and passed independent capture decoding. The C11 case also mounted the
819,200-byte B: image. Base and working-copy identities matched after each
read-only workload:

- stock A: `b4402dc9be86fef9532e61fff491dc3b93dc0db40e68d575c89aab083160bec1`;
- C11 A: `59174921a4504283dd0311ef07324a7e3db4f4c0bd7ebac4cd7304097e8ab2fa`.

The C11 host missed the optional V16 final reply, performed its designed
resident-stream probe, and then received valid NetDisk requests. No Fastboot
resend was attempted; successful disk service is the end-to-end confirmation.

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
W5 separately requires Windows 95 execution and physical serial qualification.
