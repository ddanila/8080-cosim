# juku_top checkpoint FDC probe

Status: **PASS**

This diagnostic starts from a generated EKDOS/TDD cosim checkpoint
(`JUKU_TOP_CHECKPOINT_FDC_CYCLES`, default 8,711,550, the
first-data-read setup window),
loads it into `juku_top`, enables frame IRQs and the
fixed `TDD` keyboard stimulus, and runs toward the FDC data-register read.
It is the checkpointed counterpart to
`sync/juku_top_fdc_probe.sh`.

## Command

```sh
sync/juku_top_checkpoint_fdc_probe.py
```

Environment overrides:

- `JUKU_TOP_CHECKPOINT_FDC_TIMEOUT` default `300` seconds
- `JUKU_TOP_CHECKPOINT_FDC_CYCLES` default `8711550`; set to `0` to use
  the framebuffer-write checkpoint stop instead
- `JUKU_TOP_CHECKPOINT_FDC_WRITES` default `63085` when cycle stop is disabled
- `JUKU_TOP_CHECKPOINT_FDC_FRAMEIRQ` default `80000`
- `JUKU_TOP_CHECKPOINT_FDC_KEYAT` default `42000`
- `JUKU_TOP_CHECKPOINT_FDC_KHOLD` default `900000`
- `JUKU_TOP_CHECKPOINT_FDC_KGAP` default `900000`
- `JUKU_TOP_CHECKPOINT_FDC_MAX_MCYC` default `1000000`
- `JUKU_TOP_CHECKPOINT_FDC_TIMECAP` default `900000000`
- `JUKU_TOP_CHECKPOINT_FDC_STOP_IO` default `0`
- `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READ` default `1`

## Evidence

- Cosim checkpoint exit code: `0`
- Cosim checkpoint cycle: `8711550`
- Cosim checkpoint writes: `63095`
- Cosim checkpoint PC: `0xE643`
- Cosim checkpoint key position/phase: `3` / `0`
- HDL resume exit code: `0`
- Timed out: `no`
- First PIC line: `[RESUME-PIC] OUT port=0x01 data=0xff mcyc=10065 vram=63095 pc=0xd7c1`
- First no-key keyboard line: `[RESUME-KBD] IN port=0x05 data=0xcf mcyc=10304 vram=63095 pc=0x1463`
- First key stimulus line: `none`
- Last key stimulus line: `none`
- First IRQ line: `[RESUME-IRQ] intr rise count=1 mcyc=10000 vram=63095`
- Last IRQ line: `[RESUME-IRQ] inta fall count=24 mcyc=82127 vram=63095`
- First VRAM line: `none`
- Last complete VRAM line: `none`
- First FDC line: `[RESUME-FDC] OUT port=0x1c reg=0 data=0x02 mcyc=58712 vram=63095 ios=1`
- FDC stop line: `[RESUME-FDC] stop reason=data-read ios=11 reads=7 writes=4 data=0x00 mcyc=83789 vram=63095`
- Stop/fail line: `none`

| Trace | Lines |
| --- | ---: |
| PIC writes | `27` |
| keyboard reads | `136` |
| key stimulus | `0` |
| IRQ events | `32` |
| VRAM progress | `0` |
| FDC events | `12` |

## Boundary

- This is not a prompt proof until EKDOS `A>` is reached through
  checkpoint-resumed `juku_top` CPU execution.
- The default proves the ROMBIOS FDC path advances from command/setup I/O
  into an FDC data-register read from a checkpointed CPU run.
- Use `JUKU_TOP_CHECKPOINT_FDC_CYCLES=0 JUKU_TOP_CHECKPOINT_FDC_WRITES=63085
  JUKU_TOP_CHECKPOINT_FDC_STOP_IO=1 JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READ=0`
  for the older first-command boundary.
- Use `JUKU_TOP_CHECKPOINT_FDC_CYCLES=0 JUKU_TOP_CHECKPOINT_FDC_WRITES=42000`
  for the earlier key-window narrowing run.
