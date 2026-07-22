# ROM-programmed Juku video timing

Status: **AUTONOMOUS PIT RASTER TIMING GUARDED / DRAM SLOT + D34_SIG OPEN**.

This generated report executes the exact `ekta37` D54/D55 programming
bytes through the PIT bus pins of `juku_top`, with its 16 MHz input running
the source-proved D40 1 MHz divider. It measures the autonomous D54 -> D55
-> D56 -> D34_SYNC chain; no synthetic frame tick or forced sync net is used.

## Command

```sh
python3 scripts/report_video_pit_timing.py
```

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Exact ekta37 PIT write sequence remains present | PASS | ROM offsets 0x01D4..0x0222, filtered to ports 0x10..0x17 |
| 8253 model implements the video-used BCD and modes 1/2 | PASS | BCD reload conversion, hardware one-shot, rate generator, latch-command preservation |
| Autonomous top-level PIT/one-shot timing passes | PASS | VIDEO-PIT-TIMING: PASS h=15625Hz line=64000ns frame=313lines/20032000ns v=49.920128Hz active=320x241 D56=5040/223000ns |
| Physical PIT/D56 cascade endpoints remain exact | PASS | board JSON D54/D55/D56 plus HOR_RTR/VER_RTR endpoint sets |
| Independent MAME raster geometry agrees with the ROM divisors | PASS | 512x313 total, 320x241 active, H porches 64/128 px, V porches 25/47 lines |
| Unresolved slot and D34 signal boundaries remain explicit | PASS | no framebuffer-slot or D34_SIG promotion |

## Recovered programmed contract

| Stage | Control/count | Meaning |
| --- | --- | --- |
| D54 counter 0 | mode 2, BCD `0x64` | 64 one-microsecond byte clocks per line |
| D54 counter 1 | mode 1, BCD `0x24` | 24 us horizontal blank interval |
| D54 counter 2 | mode 1, BCD `0x08` | 8 us horizontal front porch |
| D55 counter 0 | mode 2, binary `0x0139` | 313 lines per frame |
| D55 counter 1 | mode 1, BCD `0x0072` | 72-line vertical blank interval |
| D55 counter 2 | mode 1, BCD `0x25` | 25-line vertical front porch |

The remaining intervals follow without guessed constants: 40 active byte
clocks = 320 pixels, 16 us horizontal back porch, 241 active lines, and a
47-line vertical back porch. With the traced clocks this gives 15.625 kHz
horizontal and `1 MHz / (64 * 313) = 49.920128 Hz` frame rate.

## Executed result

```text
VIDEO-PIT-TIMING: PASS h=15625Hz line=64000ns frame=313lines/20032000ns v=49.920128Hz active=320x241 D56=5040/223000ns
```

The test also verifies the typical modeled D56 pulse widths (5.04 us and
223 us) and the traced `D34_SYNC = D56.Q2 XOR D56.Q_N` truth.

## Deliberate boundary

This closes autonomous digital raster timing, not video memory arbitration.
D41/D50/D51/D52/D53 slot control, D34_SIG, fetched framebuffer bytes, the
VT2 stage, and loaded X7 voltage remain separate open boundaries. The
abstract `vid_out` is still only a framebuffer oracle and is not composite.
