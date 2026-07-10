# Video timing reference

Status: **VIDEO RASTER GEOMETRY GUARDED**

This check pins the runnable video raster geometry against the vendored MAME
Juku reference and the local `video_raster` HDL block.

## Command

```sh
sync/video_timing_check.sh
```

## MAME Reference

Parsed from `ref/mame_juku.cpp`:

| Parameter | Value |
| --- | ---: |
| visible width | 320 px |
| visible height | 241 lines |
| framebuffer columns | 40 bytes |
| framebuffer bytes | 9640 |
| horizontal front porch | 64 px |
| horizontal back porch | 128 px |
| horizontal period | 512 px |
| vertical front porch | 25 lines |
| vertical back porch | 47 lines |
| vertical period | 313 lines |
| nominal frame rate | 49.920128 Hz |

## HDL Guard

- `hdl/sim/video_raster_geometry_tb.v` instantiates `video_raster`.
- It requires a 40 x 241 byte raster: `9640` framebuffer bytes.
- It requires one load phase followed by seven shift phases for every byte.
- It requires wrap back to `0xD800` after `77120` dot clocks.

Pass line:

```
VIDEO-RASTER-GEOMETRY: PASS cols=40 rows=241 bytes=9640 dots=77120 wrap_addr=0xd800
```

## Boundary

This does not close the faithful shared-DRAM video slot timing. The still-open
work is the РЕ3/АГ3-driven CPU/video arbitration schedule and replacement of
the sim-only video read port with that real slot timing.
