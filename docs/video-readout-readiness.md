# Video readout readiness

Status: **RUNNABLE ABSTRACT VIDEO READOUT GUARDED**

This guard checks byte preservation in the runnable abstract video path.
It runs archive-37 RomBios 3.43m with a requested stop target of 6000
framebuffer writes (VIDEO_WRITES defaults to 6000), then serializes the capture.
The testbench also has a 400 ms simulated time cap. This script suppresses
the boot log and does not assert that the write target was reached.
It does not require a full boot prompt or compare that screen to cosim:

- hdl/sim/video_readout_tb.v serializes a booted framebuffer through the
  abstracted ir16_sr pixel serializer and reconstructs the bytes.
- hdl/sim/video_out_tb.v drives juku_top's own video_raster -> ir16_sr ->
  lp5_xor1 path and reconstructs the emitted abstract vid_out bitstream.
- Both reconstructed byte streams must compare exactly against the booted
  juku_top framebuffer.

The sim-only vid_out port is not composite voltage and is not a simulated D34
or VIDEO_OUT node. It contains no sync summing, VT2 output stage, termination, or edge
model. Its name is retained only for HDL interface compatibility.

The remaining physical boundary is the shared-DRAM slot timing: arbitration
through the КП14 muxes and the РЕ3/АГ3 timing network. This check does not claim
that timing is closed; it locks only the byte-to-pixel serializer and runnable
juku_top abstract oracle. The companion raster-geometry guard is
`sync/video_timing_check.sh` / `docs/video-timing-reference.md`.

## Command

```sh
VIDEO_WRITES=6000 sync/video_readout_check.sh
```

## Evidence

| Artifact | Bytes | Check |
| --- | ---: | --- |
| hdl/sim/vram_top.bin | 9640 | source framebuffer from juku_top_tb |
| hdl/sim/vram_readout.bin | 9640 | byte-identical standalone serializer reconstruction |
| hdl/sim/vram_vidout.bin | 9640 | byte-identical juku_top abstract-oracle reconstruction |

## Remaining Boundary

- Establish the CPU/video shared-DRAM slot schedule with source closure and
  measured timing. The validated D8/D94 РЕ3 contents are already available;
  they do not establish this arbitration schedule. See
  [the slot timing audit](video-slot-timing-audit.md).
- Replace the sim-only second framebuffer read port with the real shared-memory
  video read slot when the timing source is available.
