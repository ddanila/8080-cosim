# juku_top checkpoint FDC probe

Status: **PASS**

This diagnostic starts from a generated EKDOS/TDD cosim checkpoint
(`JUKU_TOP_CHECKPOINT_FDC_WRITES`, default 63,085, the first-FDC window),
loads it into `juku_top`, enables frame IRQs and the
fixed `TDD` keyboard stimulus, and runs toward the first decoded FDC I/O.
It is the checkpointed counterpart to
`sync/juku_top_fdc_probe.sh`.

## Command

```sh
sync/juku_top_checkpoint_fdc_probe.py
```

Environment overrides:

- `JUKU_TOP_CHECKPOINT_FDC_TIMEOUT` default `300` seconds
- `JUKU_TOP_CHECKPOINT_FDC_WRITES` default `63085`
- `JUKU_TOP_CHECKPOINT_FDC_FRAMEIRQ` default `80000`
- `JUKU_TOP_CHECKPOINT_FDC_KEYAT` default `42000`
- `JUKU_TOP_CHECKPOINT_FDC_KHOLD` default `900000`
- `JUKU_TOP_CHECKPOINT_FDC_KGAP` default `900000`
- `JUKU_TOP_CHECKPOINT_FDC_MAX_MCYC` default `1000000`
- `JUKU_TOP_CHECKPOINT_FDC_TIMECAP` default `900000000`
- `JUKU_TOP_CHECKPOINT_FDC_STOP_IO` default `1`
- `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READ` default `0`

## Evidence

- Cosim checkpoint exit code: `0`
- Cosim checkpoint writes: `63085`
- Cosim checkpoint PC: `0x097A`
- Cosim checkpoint key position/phase: `2` / `1`
- HDL resume exit code: `0`
- Timed out: `no`
- First PIC line: `[RESUME-PIC] OUT port=0x01 data=0xff mcyc=27435 vram=63085 pc=0x068b`
- First no-key keyboard line: `none`
- First key stimulus line: `[RESUME-KBD-STIM] press key=2 col=6 bit=5 shift=1 mcyc=0 vram=63085`
- Last key stimulus line: `[RESUME-KBD-STIM] press key=2 col=6 bit=5 shift=1 mcyc=0 vram=63085`
- First IRQ line: `[RESUME-IRQ] inta fall count=1 mcyc=1 vram=63085`
- Last IRQ line: `[RESUME-IRQ] inta fall count=7 mcyc=27663 vram=63085`
- First VRAM line: `none`
- Last complete VRAM line: `none`
- First FDC line: `[RESUME-FDC] OUT port=0x1c reg=0 data=0x02 mcyc=29272 vram=63085 ios=1`
- FDC stop line: `[RESUME-FDC] stop ios=1 reads=0 writes=1 mcyc=29272 vram=63085`
- Stop/fail line: `none`

| Trace | Lines |
| --- | ---: |
| PIC writes | `2` |
| keyboard reads | `0` |
| key stimulus | `1` |
| IRQ events | `9` |
| VRAM progress | `0` |
| FDC events | `2` |

## Boundary

- This is not a prompt proof until EKDOS `A>` is reached through
  checkpoint-resumed `juku_top` CPU execution.
- The default proves the first decoded ROMBIOS FDC command from a
  checkpointed CPU run.
- Use `JUKU_TOP_CHECKPOINT_FDC_STOP_IO=0
  JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READ=1` to target the first FDC
  data-register read; the current 63,095-write candidate lands at
  PC `0x1006` and does not yet resume to decoded FDC traffic.
- Use `JUKU_TOP_CHECKPOINT_FDC_WRITES=42000` for the earlier key-window
  narrowing run.
