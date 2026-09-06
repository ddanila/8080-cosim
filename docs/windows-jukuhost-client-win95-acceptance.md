# Original Windows 95 VM acceptance

Local test, 2026-09-05. This is an actual Windows 95 guest result, not Wine
and not physical Windows serial qualification.

## Environment

- User-supplied Windows 95 OEM CD, ISO SHA-256
  `8cba431f1178066d306f17d088ebb5ea0be923b7b21ac61b4b45365dab58dfa4`.
- QEMU 10.2.1, Pentium TCG, 32 MiB RAM, Cirrus VGA, 504 MiB FAT16 IDE disk,
  `-icount shift=5,align=off,sleep=on`. No network adapter. VNC is localhost-only.
- Installation started from the sibling `msdos` repository's generated DOS
  6.22-compatible floppy. Setup source was copied to `C:\WIN95` from the ISO.
  `FILES=60`, `BUFFERS=30`, no HIMEM, and the CD-documented `SETUP /IS` were
  used. See that repository's `tests/WINDOWS95-SETUP.md` for DOS fixes.
  Follow-up on 2026-09-06 resolved the HIMEM observations: DOS fork commit
  `a438fb9` fixes XMS free-memory status and moves crossing 64 KiB boundaries,
  with standalone regressions. Normal Windows 95 Setup with `DOS=HIGH` then
  completed through desktop and clean shutdown. This does not change the
  original host-test configuration recorded here.
- COM1 is QEMU's local PTY, attached directly to the C12 co-simulator; no
  physical serial adapter or CS00000 was used. Simulator pacing is 1.7 MHz,
  using the same UART settings as the Wine end-to-end harness.
- JUKUWIN SHA-256:
  `00a89db0b15c2c234ea7af792d6c78792d783771d1b9eb9efac6b206cd895ea1`.
  Built with the checked embedded payload catalog. Unrelated rebuilt stock
  payloads in the sibling `out` directory differed from the catalog, so the
  documented no-external-payload-source build path was used. No catalog
  identities were silently updated.

## Bugs exposed by the real guest

1. `InterlockedExchangeAdd` is absent from the original kernel, preventing
   process startup. Read the aligned volatile stop-only flags directly on
   Win32/x86; retain `InterlockedExchange` for writes. Remove the unavailable
   import from the allowlist and shim; the import regression guards this.
2. `MoveFileExA` exists as a stub returning `ERROR_CALL_NOT_IMPLEMENTED`.
   Configuration replacement must take the existing backup/rename fallback
   for this result, not only for an absent export. Tests also ensure a real
   access-denied error does not trigger fallback.
3. With the configured 4096-byte serial TX queue, native probe writes of
   1, 128, 512, and 4096 bytes succeeded. Writes of 8192 and 16384 returned
   FALSE, a count of 4096, and last-error zero. Cap each synchronous write at
   4096 bytes, preserving the existing partial-write loop. A 9000-byte shim
   regression requires three bounded writes with exact byte preservation.

## Results and scope

- Installed Windows boots to its desktop.
- The corrected executable passes `--selftest` inside Windows 95.
- GUI loads at 640x480, saves configuration, creates the A: snapshot, and
  verifies COM1 at 19200/8O1 with no flow control.
- C12 boots to `CP/M Plus 3.1 Juku`, `N3 19200`, and `A>`; the first bounded
  run reached 1294 protocol requests and 23 disk reads with zero retries or
  reconnects. A simulator restart is detected as a target reset and boots
  CP/M again without restarting the Windows host.
- Sending `DIR` through the GUI returns a directory listing and a fresh `A>`
  prompt, demonstrating bidirectional interactive console traffic.
- Final clean stop: 3279 requests, 50 read operations / 150 records, zero
  writes, retries, reconnects, or UART errors; one deliberately induced target
  reset and boot restart. This is a functional test, not an endurance claim.
- V16 ready/final marker warnings occur; recovery through the resident stream
  scanner and subsequent NetDisk traffic succeeds. This is not a claim that
  every boot marker was observed.
- Full Win32 desk gate passes: shim tests, reproducible PE builds, import
  audit, Wine self-test, and package validation. These complement rather than
  replace the actual Windows 95 result.

Local VM, diagnostic probe, captures, and screenshots live in ignored
`build/win95/`. The CD, Windows installation, and product identification are
not repository fixtures. Stock ROM/C11 guest tests, physical Windows serial
hardware, long endurance, and full GUI qualification remain outside this run.
