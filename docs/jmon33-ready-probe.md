# jmon33 monitor-idle oracle

Status: **JMON33 MONITOR-IDLE ORACLE READY**

This probe runs the default Juku Monitor 3.3 ROM under cosim with the
frame interrupt enabled for a fixed cycle budget, then checks the final
framebuffer. It does not stop when idle is first reached or measure settling
time. The visible oracle is a solid 8x10 cursor block at
`x=8`, `y=20` plus the full VRAM SHA256.

## Command

Run from the repository root with Python, a C compiler (`CC`, default
`cc`), and `roms/jmon33.bin`. The probe builds a temporary executable
and overwrites this report after simulation. It samples `cosim/vram.bin`,
then restores its previous contents (or removes it if initially absent)
on normal completion, including a failed oracle result.

```sh
sync/jmon33_ready_probe.py
```

Environment overrides:

- `JMON33_READY_MAX_CYCLES` default `20000000`
- `JMON33_READY_FRAME_CYCLES` default `200000`

This run requested `20000000` cycles and a `200000`-cycle frame interval.
Overrides can change the sampled cursor phase and fail the fixed VRAM oracle.

## Evidence

| Check | Result |
| --- | --- |
| Trace exits cleanly | PASS |
| ROM load reports 16384 bytes (explicit `roms/jmon33.bin` input) | PASS |
| Initial PIC writes are `00h=56h`, `01h=FFh` | PASS |
| First frame IRQ logged; IRQ trace contains vector `FF54h` | PASS |
| Keyboard ports `04h` and `05h` each read | PASS |
| VRAM dump is `9640` bytes | PASS |
| VRAM SHA256 equals `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397` | PASS |
| Solid cursor block at `x=8`, `y=20` | PASS |
| Monitor work pages `0xD600`/`0xD700` written | PASS |
| Visible pages `0xDB00`/`0xDC00` written | PASS |

## Summary

- Stop PC: `0xFF54`
- Cycles: `20000009`
- Mode: `1`

## Remaining Boundary

- This is the reproducible cosim monitor-idle oracle. The typed jmon33
  command surface is guarded separately by `sync/jmon33_command_probe.py`.
- [HDL cursor probe](jmon33-hdl-cursor-probe.md) records the structural
  comparison status. Cartridge BASIC has a separate
  [artifact/procedure boundary](cartridge-basic-boundary.md).
