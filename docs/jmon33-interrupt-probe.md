# jmon33 interrupt-path probe

Status: **JMON33 INTERRUPT PATH READY**

This probe exercises the interrupt-driven Juku Monitor 3.3 ROM in cosim.
Unlike ekta37, jmon33 depends on frame interrupts and keyboard/serial
service paths before it becomes useful as an interactive monitor.

## Command

```sh
sync/jmon33_interrupt_probe.py
```

Environment overrides:

- `JMON33_PROBE_MAX_CYCLES` default `5000000`
- `JMON33_PROBE_FRAME_CYCLES` default `200000`

## Evidence

| Check | Result |
| --- | --- |
| jmon33 ROM loaded | PASS |
| 8259 programmed for MCS-80 vectoring | PASS |
| Frame interrupt taken at `0xFF54` | PASS |
| Keyboard matrix ports read | PASS |
| Monitor writes video RAM | PASS |

## Trace Highlights

```text
[IRQ] taken #1 g_vw=196 cyc=600003 pc=2ECD icw1=56 icw2=FF mask=DF vec=FF54
[IRQ] taken #2 g_vw=196 cyc=800001 pc=2ECD icw1=56 icw2=FF mask=DF vec=FF54
[IRQ] taken #3 g_vw=200 cyc=1400004 pc=FC90 icw1=56 icw2=FF mask=DF vec=FF54
stopped pc=0xFF54 cyc=5000001 halted=0 iff=0 mode=1 switches=31
```

First I/O activity:

```text
[OUT] first write port 0x13 = 0x15
[OUT] first write port 0x17 = 0x35
[OUT] first write port 0x1B = 0x1F
[OUT] first write port 0x10 = 0x64
[OUT] first write port 0x14 = 0x12
[OUT] first write port 0x18 = 0x32
[OUT] first write port 0x1A = 0xFF
[OUT] first write port 0x0F = 0x9B
[OUT] first write port 0x07 = 0x82
[IN ] first read  port 0x06
[OUT] first write port 0x06 = 0x01
[OUT] first write port 0x11 = 0x24
[OUT] first write port 0x12 = 0x08
[OUT] first write port 0x15 = 0x72
[OUT] first write port 0x16 = 0x25
[OUT] first write port 0x00 = 0x56
[OUT] first write port 0x01 = 0xFF
[OUT] first write port 0x04 = 0x27
[IN ] first read  port 0x04
[IN ] first read  port 0x05
[IN ] first read  port 0x1A
```

## Remaining Boundary

- This fast probe proves that the interrupt-driven monitor path is alive in
  cosim; it is not the user-visible completion oracle by itself.
- `docs/jmon33-ready-probe.md` records the stronger cosim monitor-idle
  framebuffer oracle, and `docs/jmon33-hdl-cursor-probe.md` records the
  matching structural-HDL cursor result.
