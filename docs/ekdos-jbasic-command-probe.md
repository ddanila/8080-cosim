# EKDOS JBASIC command probe

Status: **EKDOS JBASIC PROMPT ORACLE PINNED**

This generated report drives the factory ROMBIOS boot sequence to EKDOS,
waits for the `A>` prompt bitmap, then types the disk command
`JBASIC` on the vendored programming disk. The keyboard wait marker is
implemented as `|` in `JUKU_KEYS`; it is not a typed key.

The result is a bounded command-launch diagnostic and visible BASIC
prompt oracle. It checks keyboard progress, at least 19,000 FDC data
reads over the whole run, a short raw-candidate entry prefix in RAM,
and the rendered `READY` prompt. It does not resolve the directory/raw
allocation mapping described in [BASIC extraction](basic-disk-extraction.md).

## Command

```sh
JBASIC_COMMAND_MAX_CYCLES=900000000 JBASIC_COMMAND_FRAME_CYCLES=200000 \
  sync/ekdos_jbasic_command_probe.py
```

The wrapper compiles its own trace and sets the keyboard/checkpoint inputs.
Its default disk is `media/disks/JUKPROG2.CPM`; to select another image,
set `JBASIC_COMMAND_DISK` to its absolute path. Keyboard timing overrides
are `JBASIC_KEY_HOLD_FRAMES` (default 6) and `JBASIC_KEY_GAP_FRAMES` (default 8).

## Summary

- Trace exit code: 0
- Disk image: `media/disks/JUKPROG2.CPM`
- Keyboard script: `TDD|JBASIC\r` (11 positions including the wait marker)
- Prompt wait marker: consumed at 73446 VRAM writes, 14400002 cycles, position 3
- Final keyboard position/phase: `11` / `0`
- Stop PC: `FED4`
- Cycles: 900000003
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
- Visible command line: `A>JBASIC` at scanline 71 (yes)
- Visible BASIC prompt: `READY` at scanline 121 (yes)
- Visible block cursor: scanline 130 (yes)
- Probe failures: 0

## FDC I/O Ports

| Direction | Port | Count | Last write |
| --- | ---: | ---: | --- |
| OUT | 0x1C | 48 | 0x80 |
| OUT | 0x1D | 0 | - |
| OUT | 0x1E | 40 | 0x09 |
| OUT | 0x1F | 40 | 0x14 |
| IN | 0x1C | 15301 | - |
| IN | 0x1D | 40 | - |
| IN | 0x1E | 0 | - |
| IN | 0x1F | 19968 | - |

## Video/Mode State

- Final memory mode: `1`
- Final PPI Port C latch: `0x05`
- Final VRAM writes: 77306

## Disposition

- `JUKPROG2.CPM` is used because `docs/basic-disk-extraction.md` preserves the raw live-load `JBASIC.COM` candidate from that disk.
- The `JUKU1.CPM` `JBASIC.COM` directory entry still matters as catalog evidence, but the current extraction begins with a 4 KiB `E5`-filled block followed by other data; it is not used for this launch probe.
- The guard requires at least six candidate entry bytes at RAM `0x0100` and the `ERROR`, `READY`, and `BASIC` strings somewhere in RAM. It does not verify the complete loaded binary or the relocation of those strings.
- The fixed-`0xD800` framebuffer has a positive text oracle: the typed `A>JBASIC` command line and final `READY` prompt are matched by exact 8x7 glyph bitmaps.
- The [recorded HDL run](juku-top-jbasic-verilator-probe.md) reached `READY`. This report checks the C-model launch path; see [simulator compatibility](../sync/README.md#simulator-compatibility) for current HDL rerun limits.
