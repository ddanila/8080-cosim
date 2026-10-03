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

The accepted host drains the serial transmitter before awaiting the final
Fastboot reply or changing from 8N1 to 8O1. On Darwin, accepting a write does
not mean that the complete stream has left the USB-serial adapter.

The final cold run latched S21 `07h` (English, 80x24, automatic network boot),
completed all 7,670 compressed Fastboot bytes, and ran `STATUS`, `DIAG ALL`,
`N4BULK`, and `SOAK` without operator input. It recorded 2,372 protocol
requests, 33 disk reads carrying 264 records, four writes to a private A:
snapshot, zero target resets, zero reconnects, and zero UART errors. Every
target diagnostic passed and the host stopped cleanly.

The recorded request metrics use the adjacent `cpm-plus-juku` runner's
host-start boundary to align capture timestamps: Darwin and Python monotonic
clock epochs differ on this machine. Preserve that alignment when reanalyzing
the capture.

This check qualifies the focused physical C8 cold path on Apple Silicon. It
does not replace the broader M5 simulator/platform matrix, visually qualify
the selected 80x24 raster, or exercise deliberately induced C1--C5 POST
failures.
