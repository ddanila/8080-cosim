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

The underlying HDL testbench also accepts `+cursorstop=1`, which stops when
the cosim jmon33 monitor-idle cursor bytes are present in `juku_top` VRAM.
That stronger boundary is intentionally not the default for this fast guard.

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

## Scope

- This remains the fast first-video-write HDL guard; it is not the stronger
  user-visible completion check by itself.
- The cosim-side interrupt path is documented in
  `docs/jmon33-interrupt-probe.md`.
- `docs/jmon33-ready-probe.md` defines the cosim monitor-idle framebuffer
  oracle, and `docs/jmon33-hdl-cursor-probe.md` records that `juku_top`
  reaches the matching cursor/hash boundary.
