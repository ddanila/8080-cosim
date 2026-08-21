# Portable C host macOS physical check

Status: **FOCUSED C8 COLD PATH PASSED; FULL M5 MATRIX NOT CLAIMED**

On 2026-08-21 the native arm64 build of `jukuhost 0.3.0-m5` ran on macOS
against physical CS00015 fitted with JukuNet C8 / ROM ABI 1.3. The executable
SHA-256 was `2234c3c3a41d7fd83005c62fb5d83fa820c2af79897ab1661d65944318a8cbaf`.
The run bound C8 manifest
`c6b733ec1574594427e1f8485c19aa2aeb0a3c377586e3490cfce9c46e0273b8`,
system `ec9b7fd00db2d8e70258aae74500fa261f987b6b04bddfdb5ab44e56ca2ba3f1`,
and Fastboot V16 stage
`44735bf468a2014bbcf327d5d0770d9fcf21a3c33704499282180ad6c95898ea`.

The first physical attempt exposed a Darwin USB-serial queue difference.
macOS accepted the complete Fastboot stream before it had left the adapter;
the host could therefore change from 8N1 to 8O1 while bytes were still queued.
The portable host now drains the serial transmitter before awaiting the final
Fastboot reply or changing framing. The focused C8 simulator check passed
before the corrected physical run.

The final cold run latched S21 `07h` (English, 80x24, automatic network boot),
completed all 7,670 compressed Fastboot bytes, and ran `STATUS`, `DIAG ALL`,
`N4BULK`, and `SOAK` without operator input. It recorded 2,372 protocol
requests, 33 disk reads carrying 264 records, four writes to a private A:
snapshot, zero target resets, zero reconnects, and zero UART errors. Every
target diagnostic passed and the host stopped cleanly.

Darwin and Python expose monotonic clocks with different epochs on this
machine. The adjacent `cpm-plus-juku` runner now aligns capture records to its
recorded host-start boundary before attributing request metrics. Its synthetic
cross-epoch regression, complete physical-acceptance test, retained cold-run
audit, and the physical four-command run all pass.

This check qualifies the focused physical C8 cold path on Apple Silicon. It
does not replace the broader M5 simulator/platform matrix, visually qualify
the selected 80x24 raster, or exercise deliberately induced C1--C5 POST
failures.
