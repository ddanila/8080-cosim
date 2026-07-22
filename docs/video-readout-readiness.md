# Video readout readiness

Status: **RUNNABLE ABSTRACT VIDEO READOUT GUARDED**

This guard proves the current runnable video-readout path:

- hdl/sim/video_readout_tb.v serializes a booted framebuffer through the
  abstracted ir16_sr pixel serializer and reconstructs the bytes.
- hdl/sim/video_out_tb.v drives juku_top's own video_raster -> ir16_sr ->
  lp5_xor1 path and reconstructs the emitted abstract vid_out bitstream.
- Both reconstructed byte streams must compare exactly against the booted
  juku_top framebuffer.

The sim-only vid_out port is not composite voltage and is not a simulated D34
or X7 node. It contains no sync summing, VT2 output stage, termination, or edge
model. Its name is retained only for HDL interface compatibility.

The remaining physical boundary is the shared-DRAM slot timing: arbitration
through the КП14 muxes and the РЕ3/АГ3 timing network. This check does not claim
that timing is closed; it locks only the byte-to-pixel serializer and runnable
juku_top abstract oracle. The companion raster-geometry guard is
`sync/video_timing_check.sh` / `docs/video-timing-reference.md`.

## Command

```sh
sync/video_readout_check.sh
```

## Evidence

| Artifact | Bytes | Check |
| --- | ---: | --- |
| hdl/sim/vram_top.bin | 9640 | source framebuffer from juku_top_tb |
| hdl/sim/vram_readout.bin | 9640 | byte-identical standalone serializer reconstruction |
| hdl/sim/vram_vidout.bin | 9640 | byte-identical juku_top abstract-oracle reconstruction |

## Remaining Boundary

- Dump or otherwise prove the РЕ3/АГ3 timing that arbitrates CPU/video DRAM
  slots.
- Replace the sim-only second framebuffer read port with the real shared-memory
  video read slot when the timing source is available.
