# Physical video contributor probes

Status: **PHYSICAL CONTRIBUTORS PROBED / CONTROLLED STIMULUS ONLY / SLOT + D34_SIG OPEN**.

This generated report guards explicit simulation observability for the
source-proved D42/D43/D37 and D54/D55/D56/D34_SYNC contributors. The
event export uses controlled PIT trigger stimulus solely to prove the traced
component chain and modeled one-shot durations. It is not a Juku raster,
D34_SIG waveform, transistor waveform, composite voltage, or X7 sample stream.

## Commands

```sh
python3 scripts/report_video_physical_probes.py
python3 scripts/report_video_physical_probes.py --events /tmp/video-events.csv
```

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Probe testbench passes its pulse/truth assertions | PASS | iverilog/vvp controlled-stimulus test |
| Explicit top-level probes expose only bounded contributors | PASS | D34_SIG is intentionally absent while its input function remains open |
| Shared-DRAM slot uncertainty is machine-visible | PASS | every exported row carries slot_schedule_known=0 |
| D56 section-2 pulse is the guarded 5.04 us diagnostic | PASS | R47=20k/C7=560pF typical model: 100..5140 ns |
| D56 section-1 pulse is the guarded 223 us diagnostic | PASS | R59=33k/C8=15nF typical model: 10000..233000 ns |
| D34 sync probe obeys the traced XOR inputs | PASS | D34 pins 9,10 -> 8: D56.Q2 XOR D56.Q_N |
| Board endpoints for the probed physical sync chain remain exact | PASS | board JSON exact endpoint sets |

## Exported event schema

`time_ns,pit_hsync,pit_vsync,d56_q_n,d56_q2,d56_q2_n,d34_sync,`
`d42_q,d43_q,d37_pixel_n,load_vid,slot_schedule_known`

The controlled run emits the following transition times:

| Event | Time |
| --- | ---: |
| D56.Q2 asserted | 100 ns |
| D56.Q2 released | 5,140 ns |
| D56.Q_N asserted low | 10,000 ns |
| D56.Q_N released high | 233,000 ns |

## Deliberate boundaries

- `probe_slot_schedule_known` is hard-low until the physical shared-DRAM
  arbitration schedule is source-complete.
- D34_SIG is not exported because its input function remains described only
  as the open `pixel^REV?` boundary in the board evidence.
- D42/D43/D37 probes are physical-net observability only; under this controlled
  test they do not claim a valid fetched framebuffer byte.
- D34 output-drive current, VT2, the 75-ohm load, C94, and X7 voltage remain
  separate WP4/physical-calibration boundaries.
