# jmon33 monitor-idle oracle

Status: **JMON33 MONITOR-IDLE ORACLE READY**

This probe runs the default Juku Monitor 3.3 ROM under cosim with the
frame interrupt enabled until the deterministic idle framebuffer state is
reached. The current visible oracle is a solid 8x10 cursor block at
`x=8`, `y=20` plus the full VRAM SHA256.

## Command

```sh
sync/jmon33_ready_probe.py
```

Environment overrides:

- `JMON33_READY_MAX_CYCLES` default `20000000`
- `JMON33_READY_FRAME_CYCLES` default `200000`

## Evidence

| Check | Result |
| --- | --- |
| Trace exits cleanly | PASS |
| jmon33 ROM loaded | PASS |
| 8259 programmed for MCS-80 vectoring | PASS |
| Frame interrupt taken at `0xFF54` | PASS |
| Keyboard matrix ports scanned | PASS |
| VRAM dump is `9640` bytes | PASS |
| VRAM SHA256 equals `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397` | PASS |
| Solid cursor block at `x=8`, `y=20` | PASS |
| Monitor work pages `0xD600`/`0xD700` written | PASS |
| Visible pages `0xDB00`/`0xDC00` written | PASS |

## Summary

- Stop PC: `0xFF54`
- Cycles: `20000009`
- Mode: `1`
- Mode switches: `43`
- Actual VRAM SHA256: `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`
- Write pages: `0x0000=589637, 0xD600=1488, 0xD700=5778, 0xDB00=42, 0xDC00=28, 0xFD00=8, 0xFF00=192`

Trace highlights:

```text
[IRQ] taken #1 g_vw=196 cyc=600003 pc=2ECD icw1=56 icw2=FF mask=DF vec=FF54
[IRQ] taken #2 g_vw=196 cyc=800001 pc=2ECD icw1=56 icw2=FF mask=DF vec=FF54
[IRQ] taken #3 g_vw=200 cyc=1400004 pc=FC90 icw1=56 icw2=FF mask=DF vec=FF54
stopped pc=0xFF54 cyc=20000009 halted=0 iff=0 mode=1 switches=43
```

## Remaining Boundary

- This is a reproducible cosim monitor-idle oracle, not yet the full
  user-visible jmon33 command prompt or BASIC launch path.
- The HDL probe still compares only the first video write; the next HDL step
  is to run `juku_top` to this stronger VRAM hash boundary.
