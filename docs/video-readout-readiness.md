# Video readout readiness

Status: **READY FOR V2 VIDEO READOUT**

This guard proves the current runnable video-readout path for WS-B2:

- hdl/sim/video_readout_tb.v serializes a booted framebuffer through the
  abstracted ir16_sr pixel serializer and reconstructs the bytes.
- hdl/sim/video_out_tb.v drives juku_top's own video_raster -> ir16_sr ->
  lp5_xor1 path and reconstructs the emitted vid_out stream.
- Both reconstructed byte streams must compare exactly against the booted
  juku_top framebuffer.

The V3 boundary remains the faithful physical slot timing: shared DRAM
arbitration through the КП14 muxes and dumped РЕ3/АГ3 timing. This check does not
claim that timing is closed; it locks the byte-to-pixel serializer and runnable
juku_top output stage.

## Command

```sh
sync/video_readout_check.sh
```

## Evidence

| Artifact | Bytes | Check |
| --- | ---: | --- |
| hdl/sim/vram_top.bin | 9640 | source framebuffer from juku_top_tb |
| hdl/sim/vram_readout.bin | 9640 | byte-identical standalone serializer reconstruction |
| hdl/sim/vram_vidout.bin | 9640 | byte-identical juku_top video-output reconstruction |

## Remaining Boundary

- Dump or otherwise prove the РЕ3/АГ3 timing that arbitrates CPU/video DRAM
  slots.
- Replace the sim-only second framebuffer read port with the real shared-memory
  video read slot when the timing source is available.
