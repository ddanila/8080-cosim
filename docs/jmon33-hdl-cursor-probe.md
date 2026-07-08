# jmon33 HDL cursor-boundary probe

Status: **JMON33 HDL CURSOR ORACLE NOT YET REACHED**

This bounded diagnostic runs Monitor 3.3 on `juku_top` with frame
interrupts enabled and the `+cursorstop=1` testbench hook active. It
records whether the structural HDL reaches the same monitor-idle cursor
oracle that cosim records in `docs/jmon33-ready-probe.md`.

## Command

```sh
sync/jmon33_hdl_cursor_probe.py
```

Environment overrides:

- `JMON33_HDL_CURSOR_MAXVRAM` default `400`
- `JMON33_HDL_CURSOR_FRAMEIRQ` default `200000`
- `JMON33_HDL_CURSOR_TIMECAP` default `4000000000`
- `JMON33_HDL_CURSOR_TRACEPROGRESS` default `100`
- `JMON33_HDL_CURSOR_TIMEOUT` default `240` seconds

## Evidence

| Check | Result |
| --- | --- |
| vvp exit code | `0` |
| subprocess timeout | NO |
| first jmon33 video write is `0xFF40` | PASS |
| cursor hook reached | NO |
| framebuffer dump observed | PASS |
| framebuffer cursor bytes match cosim | NO |
| visible framebuffer pixels | `64` |
| nonzero framebuffer bytes | `8` |
| framebuffer SHA256 | `fc7086afaf9ed608a15768aa8670341f10e24a8a70ff8545442d5c032630ea99` |
| cosim cursor SHA256 | `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397` |

## Stop State

- Stop reason: `maxvram`
- Stop writes: `400`
- Stop machine cycle: `579068`
- Last progress writes: `400`
- Last progress machine cycle: `579068`
- First-write machine cycle: `12151`

## Disposition

- The fast HDL jmon33 first-write guard remains the automated passing gate.
- This bounded run documents that the stronger cursor boundary is still open
  for `juku_top`; the next step is reducing the long interrupt/high-memory
  path enough to complete this comparison reproducibly.
