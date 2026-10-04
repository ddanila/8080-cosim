# jmon33 interrupt-path probe

Status: **JMON33 INTERRUPT PATH READY**

This probe exercises the interrupt-driven Juku Monitor 3.3 ROM in cosim.
It runs for a fixed cycle budget and checks initial PIC writes, a logged
frame IRQ, keyboard-port reads, and write-density activity on DB00/DC00.
It does not inject serial traffic or verify interactive command completion.

## Command

Run from the repository root with Python, a C compiler (`CC`, default
`cc`), and `roms/jmon33.bin`. The probe builds a temporary executable,
overwrites this report after simulation, and overwrites `cosim/vram.bin`.
Preserve the VRAM file first if its current contents are needed.

```sh
sync/jmon33_interrupt_probe.py
```

Environment overrides:

- `JMON33_PROBE_MAX_CYCLES` default `5000000`
- `JMON33_PROBE_FRAME_CYCLES` default `200000`

This run requested `5000000` cycles and a `200000`-cycle frame interval.

## Evidence

| Check | Result |
| --- | --- |
| ROM load reports 16384 bytes (explicit `roms/jmon33.bin` input) | PASS |
| Initial PIC writes are `00h=56h`, `01h=FFh` | PASS |
| First frame IRQ logged; trace contains vector `FF54h` | PASS |
| Keyboard matrix ports read | PASS |
| Positive write-density count on page `DB00h` or `DC00h` | PASS |

## Remaining Boundary

- This fast probe proves that the interrupt-driven monitor path is alive in
  cosim; it is not the user-visible completion oracle by itself.
- [Ready probe](jmon33-ready-probe.md) records the cosim monitor-idle
  framebuffer oracle. The [HDL cursor probe](jmon33-hdl-cursor-probe.md)
  records the structural comparison status.
