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

- `JMON33_HDL_CURSOR_MAXVRAM` default `300`
- `JMON33_HDL_CURSOR_FRAMEIRQ` default `200000`
- `JMON33_HDL_CURSOR_TIMECAP` default `1200000000`
- `JMON33_HDL_CURSOR_TIMEOUT` default `90` seconds

## Evidence

| Check | Result |
| --- | --- |
| vvp exit code | `0` |
| subprocess timeout | NO |
| first jmon33 video write is `0xFF40` | PASS |
| cursor hook reached | NO |
| framebuffer cursor bytes match cosim | NO |
| visible framebuffer pixels | `0` |
| nonzero framebuffer bytes | `0` |
| framebuffer SHA256 | `559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d` |
| cosim cursor SHA256 | `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397` |

## Stop State

- Stop reason: `maxvram`
- Stop writes: `300`
- Stop machine cycle: `126631`
- First-write machine cycle: `12151`

## Disposition

- The fast HDL jmon33 first-write guard remains the automated passing gate.
- This bounded run documents that the stronger cursor boundary is still open
  for `juku_top`; the next step is reducing the long interrupt/high-memory
  path enough to complete this comparison reproducibly.
