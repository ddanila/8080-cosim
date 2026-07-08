# EKDOS JBASIC command probe

Status: **EKDOS JBASIC COMMAND BOUNDARY PINNED**

This generated report drives the factory ROMBIOS boot sequence to EKDOS,
waits for the `A>` prompt bitmap, then types the disk command
`JBASIC` on the vendored programming disk. The keyboard wait marker is
implemented as `|` in `JUKU_KEYS`; it is not a typed key.

The result is a bounded command-launch diagnostic, not a BASIC prompt
claim. It proves the post-prompt keyboard path is deterministic and that
the command triggers further FDC traffic from a real directory-backed
`JBASIC.COM` candidate.

## Command

```sh
JUKU_DISK=media/disks/JUKPROG2.CPM JUKU_KEYS=$'TDD|JBASIC\r' JUKU_KEY_HOLD_FRAMES=6 JUKU_KEY_GAP_FRAMES=8 cosim/trace roms/ekta37.bin 900000000 0 200000
```

## Summary

- Trace exit code: 0
- Disk image: `media/disks/JUKPROG2.CPM`
- Keyboard script: `TDD|JBASIC\r` (11 positions including the wait marker)
- Prompt wait marker: consumed at 73446 VRAM writes, 14200002 cycles, position 3
- Final keyboard position/phase: `11` / `0`
- Stop PC: `FED4`
- Cycles: 900000005
- Mode switches: 3415700
- WD1793 data reads (`0x1F`): 19968
- Live JBASIC candidate: `ref/extracted-software/JUKPROG2_JBASIC_live_candidate.COM`
- Live JBASIC candidate SHA256: `b1ae68b464c245a888c8e6bbf07037960f5a92d4e968c956c6205a1de6cfc545`
- Live JBASIC entry prefix at RAM `0x0100`: 6 bytes
- Live JBASIC byte matches at RAM `0x0100`: 570 / 8320
- Final RAM `ERROR` string: `0x0469`
- Final RAM `READY` string: `0x0476`
- Final RAM `BASIC` string: `0x04AD`
- Final VRAM SHA256: `60dcda06cf3402a1710e07eb38189518d6a3827c8279888bd8f0d927967ba90b`
- Final lit pixels: 1175
- Final fixed-framebuffer nonzero lines: 68 (`1`..`139`)
- Final fixed-framebuffer first bytes: `00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00`
- Probe failures: 0

## FDC I/O Ports

| Direction | Port | Count | Last write |
| --- | ---: | ---: | --- |
| OUT | 0x1C | 48 | 0x80 |
| OUT | 0x1D | 0 | - |
| OUT | 0x1E | 40 | 0x09 |
| OUT | 0x1F | 40 | 0x14 |
| IN | 0x1C | 143 | - |
| IN | 0x1D | 40 | - |
| IN | 0x1E | 0 | - |
| IN | 0x1F | 19968 | - |

## Video/Mode State

- Final memory mode: `0`
- Final PPI Port C latch: `0x04`
- Final VRAM writes: 77306

| Port | Function | Last | OUT count | IN count |
| ---: | --- | ---: | ---: | ---: |
| 0x10 | screen width / PIT0 counter 0 | 0x64 | 1 | 0 |
| 0x11 | horizontal blank / PIT0 counter 1 | 0x24 | 1 | 0 |
| 0x12 | horizontal front porch / PIT0 counter 2 | 0x08 | 1 | 0 |
| 0x13 | PIT0 control | 0x93 | 3 | 0 |
| 0x14 | screen height / PIT1 counter 0 | 0x01 | 2 | 0 |
| 0x15 | vertical blank / PIT1 counter 1 | 0x00 | 2 | 0 |
| 0x16 | vertical front porch / PIT1 counter 2 | 0x25 | 1 | 0 |
| 0x17 | PIT1 control | 0x34 | 3 | 0 |
| 0x18 | PIT2 counter 0 | 0x32 | 1 | 0 |
| 0x19 | PIT2 counter 1 | 0x03 | 20 | 0 |
| 0x1A | PIT2 counter 2 | 0xFF | 8962 | 8960 |
| 0x1B | PIT2 control | 0x80 | 8954 | 0 |

## Disposition

- `JUKPROG2.CPM` is used because `docs/basic-disk-extraction.md` now preserves the raw live-load `JBASIC.COM` candidate from that disk.
- The `JUKU1.CPM` `JBASIC.COM` directory entry still matters as catalog evidence, but the current extractor maps it to erased bytes; it is not used for this launch probe.
- The final RAM contains the live candidate entry signature plus relocated `ERROR`, `READY`, and `BASIC` strings, proving the command reaches loaded BASIC code/data.
- The final video/mode table records the MAME-mapped timing ports from the checkpoint, making framebuffer changes auditable without claiming a rendered text prompt.
- The deeper fixed-`0xD800` framebuffer boundary remains a sparse non-text bitmap, not a user-visible BASIC `READY` oracle.
- Next work is a BASIC prompt oracle: decode the post-command screen/text state or identify the exact EKDOS loader/TPA handoff needed by this `JBASIC.COM`.
