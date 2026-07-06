# jmon33 HDL probe

Status: **JMON33 REACHES VIDEO RAM ON JUKU_TOP**

This probe runs the Monitor 3.3 ROM on the LVS-checked structural model
`juku_top` with frame interrupts enabled. It proves that the HDL twin reaches
jmon33's first video-memory write instead of only proving the path in cosim.

## Command

```sh
sync/jmon33_hdl_probe.sh
```

Environment overrides:

- `JMON33_HDL_MAXVRAM` default `1`
- `JMON33_HDL_FRAMEIRQ` default `200000`
- `JMON33_HDL_TIMECAP` default `120000000`

## Evidence

| Check | Result |
| --- | --- |
| jmon33 readmemh generated from `roms/jmon33.bin` | PASS |
| `juku_top` runs with frame IRQ period `200000` | PASS |
| first video write address | `0xff40` |
| first video write machine cycle | `12151` |
| captured video writes | `1` |

## Remaining Boundary

- This is a first-video-write HDL probe, not a user-visible jmon33 prompt.
- The cosim-side interrupt path is deeper and remains documented in
  `docs/jmon33-interrupt-probe.md`.
- Next step: identify a stable monitor-ready screen/RAM oracle and compare the
  cosim and `juku_top` jmon33 states at that boundary.
