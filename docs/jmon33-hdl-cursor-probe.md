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

- `JMON33_HDL_CURSOR_MAXVRAM` default `1200`
- `JMON33_HDL_CURSOR_FRAMEIRQ` default `200000`
- `JMON33_HDL_CURSOR_TIMECAP` default `4000000000`
- `JMON33_HDL_CURSOR_TRACEPROGRESS` default `100`
- `JMON33_HDL_CURSOR_TIMEOUT` default `240` seconds

## Evidence

| Check | Result |
| --- | --- |
| vvp exit code | `124` |
| subprocess timeout | YES |
| first jmon33 video write is `0xFF40` | PASS |
| cursor hook reached | NO |
| framebuffer cursor bytes match cosim | NO |
| visible framebuffer pixels | `1024` |
| nonzero framebuffer bytes | `255` |
| framebuffer SHA256 | `93cf90f64fbe01cd4923ee14f15b182be24a2efae17d6722488bb9431cf99782` |
| cosim cursor SHA256 | `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397` |

## Stop State

- Stop reason: `timeout`
- Stop writes: `unknown`
- Stop machine cycle: `unknown`
- Last progress writes: `400`
- Last progress machine cycle: `579068`
- First-write machine cycle: `12151`

## Disposition

- The fast HDL jmon33 first-write guard remains the automated passing gate.
- This bounded run documents that the stronger cursor boundary is still open
  for `juku_top`; the next step is reducing the long interrupt/high-memory
  path enough to complete this comparison reproducibly.
