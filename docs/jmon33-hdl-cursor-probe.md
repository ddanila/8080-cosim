# jmon33 HDL cursor-boundary probe

Status: **JMON33 HDL CURSOR ORACLE REACHED**

This bounded diagnostic runs Monitor 3.3 on `juku_top` with frame
interrupts enabled and an optional `+cursorstop=1` testbench hook. It
records whether the structural HDL reaches the same monitor-idle cursor
oracle that cosim records in `docs/jmon33-ready-probe.md`.

## Command

```sh
sync/jmon33_hdl_cursor_probe.py
```

Environment overrides:

- `JMON33_HDL_CURSOR_MAXVRAM` default `1200`
- `JMON33_HDL_CURSOR_SIM` default `verilator`; optional `verilator`
- `JMON33_HDL_CURSOR_STOPHOOK` default `1`
- `JMON33_HDL_CURSOR_FRAMEIRQ` default `200000`
- `JMON33_HDL_CURSOR_TIMECAP` default `30000000000`
- `JMON33_HDL_CURSOR_TRACEPROGRESS` default `100`
- `JMON33_HDL_CURSOR_TIMEOUT` default `900` seconds

## Evidence

| Check | Result |
| --- | --- |
| simulator | `verilator` |
| simulator exit code | `0` |
| subprocess timeout | NO |
| first jmon33 video write is `0xFF40` | PASS |
| cursor hook reached | PASS |
| framebuffer dump observed | PASS |
| framebuffer cursor bytes match cosim | PASS |
| solid cursor rows at `x=8`, `y=20..29` | `10/10` |
| cursor row bytes | `[255, 255, 255, 255, 255, 255, 255, 255, 255, 255]` |
| visible framebuffer pixels | `80` |
| nonzero framebuffer bytes | `10` |
| framebuffer SHA256 | `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397` |
| cosim cursor SHA256 | `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397` |

## Stop State

- Stop reason: `cursor`
- Stop writes: `402`
- Stop machine cycle: `710291`
- Last progress writes: `400`
- Last progress machine cycle: `710271`
- First-write machine cycle: `12151`

## Disposition

- `juku_top` reached the cosim monitor-idle cursor boundary in this bounded run.
