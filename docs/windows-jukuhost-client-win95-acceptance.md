# Original Windows 95 VM acceptance

Local test, 2026-09-05. This is an actual Windows 95 guest result, not Wine
and not physical Windows serial qualification.

## Environment

- User-supplied Windows 95 OEM CD, ISO SHA-256
  `8cba431f1178066d306f17d088ebb5ea0be923b7b21ac61b4b45365dab58dfa4`.
- QEMU 10.2.1, Pentium TCG, 32 MiB RAM, Cirrus VGA, 504 MiB FAT16 IDE disk,
  `-icount shift=5,align=off,sleep=on`. No network adapter. VNC is localhost-only.
- Installation used the sibling `msdos` repository's generated DOS-compatible
  floppy. That repository's `tests/WINDOWS95-SETUP.md` owns setup details.
- COM1 is QEMU's local PTY, attached directly to the C12 co-simulator; no
  physical serial adapter or CS00000 was used. Simulator pacing is 1.7 MHz,
  using the same UART settings as the Wine end-to-end harness.
- JUKUWIN SHA-256:
  `00a89db0b15c2c234ea7af792d6c78792d783771d1b9eb9efac6b206cd895ea1`.
  Built from the checked embedded payload catalog without an external payload
  source; catalog identities were unchanged.

## Required Windows 95 compatibility

1. `InterlockedExchangeAdd` is absent from the original kernel, preventing
   process startup. The accepted build reads aligned volatile stop-only flags directly on
   Win32/x86 and uses `InterlockedExchange` for writes. The import regression
   excludes the unavailable API.
2. `MoveFileExA` exists as a stub returning `ERROR_CALL_NOT_IMPLEMENTED`.
   Configuration replacement uses the backup/rename fallback for this
   result as well as an absent export. Tests also ensure a real
   access-denied error does not trigger fallback.
3. With the configured 4096-byte serial TX queue, native probe writes of
   1, 128, 512, and 4096 bytes succeeded. Writes of 8192 and 16384 returned
   FALSE, a count of 4096, and last-error zero. The accepted serial implementation caps each synchronous write at
   4096 bytes and preserves the partial-write loop. A 9000-byte shim
   regression requires three bounded writes with exact byte preservation.

## Results and scope

- Installed Windows boots to its desktop.
- The corrected executable passes `--selftest` inside Windows 95.
- GUI loads at 640x480, saves configuration, creates the A: snapshot, and
  verifies COM1 at 19200/8O1 with no flow control.
- C12 booted to `CP/M Plus 3.1 Juku`, `N3 19200`, and `A>`. A simulator
  restart was detected as a target reset and booted CP/M again without
  restarting the Windows host.
- Sending `DIR` through the GUI returns a directory listing and a fresh `A>`
  prompt, demonstrating bidirectional interactive console traffic.
- Final clean stop: 3279 requests, 50 read operations / 150 records, zero
  writes, retries, reconnects, or UART errors; one deliberately induced target
  reset and boot restart. This is a functional test, not an endurance claim.
- V16 ready/final marker warnings occur; recovery through the resident stream
  scanner and subsequent NetDisk traffic succeeds. This is not a claim that
  every boot marker was observed.
- Recorded Win32 desk gate passed: shim tests, reproducible PE builds, import
  audit, Wine self-test, and package validation. These complement rather than
  replace the actual Windows 95 result.

Local VM, diagnostic probe, captures, and screenshots live in ignored
`build/win95/`. The CD, Windows installation, and product identification are
not repository fixtures. Stock ROM/C11 guest tests, physical Windows serial
hardware, long endurance, and full GUI qualification remain outside this run.
