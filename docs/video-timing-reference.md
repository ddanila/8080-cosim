# Video timing reference

Status: **VIDEO RASTER GEOMETRY GUARDED**

This check requires the vendored MAME active geometry to be 320 × 241
pixels and tests the local `video_raster` active-area scan. Porches and
periods below are parsed reference values, not simulated blanking intervals.

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

The test instantiates the raster block rather than the complete board. It
does not measure physical frame timing or validate the CPU/video DRAM slot
schedule. The sim-only video read port still needs replacement with measured
shared-DRAM timing. The separate autonomous PIT timing test is documented in
[ROM-programmed timing](video-pit-timing.md).
