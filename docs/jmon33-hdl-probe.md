# jmon33 HDL probe

Status: **JMON33 FIRST-WRITE MATCHES COSIM AND JUKU_TOP**

This probe runs the Monitor 3.3 ROM on the LVS-checked structural model
`juku_top` with frame interrupts enabled. It proves that the HDL twin reaches
jmon33's first video-memory write and matches the cosim first-write boundary.

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
| cosim first video write address | `0xFF40` |
| cosim first video write cycle | `48521` |
| `juku_top` runs with frame IRQ period `200000` | PASS |
| `juku_top` first video write address | `0xff40` |
| `juku_top` first video write machine cycle | `12151` |
| captured video writes | `1` |
| first-write VRAM dump equals cosim | PASS |

## Remaining Boundary

- This is a first-video-write HDL probe, not a user-visible jmon33 prompt.
- The cosim-side interrupt path over a longer run remains documented in
  `docs/jmon33-interrupt-probe.md`.
- Next step: identify a stable monitor-ready screen/RAM oracle and compare the
  cosim and `juku_top` jmon33 states at that stronger boundary.
