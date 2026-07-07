# juku_top checkpoint FDC probe

Status: **PASS**

This diagnostic starts from a generated EKDOS/TDD cosim checkpoint
(`JUKU_TOP_CHECKPOINT_FDC_CYCLES=8711550` or
`JUKU_TOP_CHECKPOINT_FDC_WRITES=63085` when cycle stop is disabled),
loads it into `juku_top`, enables frame IRQs and the
fixed `TDD` keyboard stimulus, and runs toward the 6656 FDC data-register reads.
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
- `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READ` default `0` when
  `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS` is nonzero, otherwise `1`
- `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS` default `6656` (13 sectors);
  set to `512` for the first sector or `0` for the first data-register read
- `JUKU_TOP_CHECKPOINT_FDC_STOP_PROMPT` default `0`; set to `1` to stop
  on the EKDOS `A>` prompt bitmap at `x=0`, `y=70`
- `JUKU_TOP_CHECKPOINT_FDC_REPORT` default
  `docs/juku-top-checkpoint-fdc-probe.md`

Known useful windows:

- Default `JUKU_TOP_CHECKPOINT_FDC_CYCLES=8711550` proves the first
  13 sectors / 6,656 data-register reads.
- `JUKU_TOP_CHECKPOINT_FDC_CYCLES=10066690
  JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS=4096` proves the later
  8 sectors / 4,096 data-register reads.
- `JUKU_TOP_CHECKPOINT_FDC_CYCLES=10066690
  JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS=0
  JUKU_TOP_CHECKPOINT_FDC_STOP_PROMPT=1` proves the checkpoint-resumed
  EKDOS `A>` prompt bitmap.

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
- Last IRQ line: `[RESUME-IRQ] inta fall count=36 mcyc=199865 vram=63105`
- First VRAM line: `[RESUME-VRAM] writes=63100 mcyc=179346 pc=0x1006`
- Last complete VRAM line: `[RESUME-VRAM] writes=63100 mcyc=179346 pc=0x1006`
- First FDC line: `[RESUME-FDC] OUT port=0x1c reg=0 data=0x02 mcyc=58712 vram=63095 ios=1`
- FDC stop line: `[RESUME-FDC] stop reason=data-read-count target=6656 ios=6754 reads=6713 data_reads=6656 writes=41 data=0x00 mcyc=216125 vram=63105`
- Prompt stop line: `none`
- Stop/fail line: `none`

| Trace | Lines |
| --- | ---: |
| PIC writes | `87` |
| keyboard reads | `204` |
| key stimulus | `0` |
| IRQ events | `48` |
| VRAM progress | `1` |
| FDC events | `6755` |
| prompt events | `0` |

## Boundary

- This is not a prompt proof until EKDOS `A>` is reached through
  checkpoint-resumed `juku_top` CPU execution.
- The default proves the ROMBIOS FDC path drains 13 full 512-byte sectors
  through FDC data-register reads from a checkpointed CPU run.
- A second clean late-sector window at
  `JUKU_TOP_CHECKPOINT_FDC_CYCLES=10066690` resumes at PC `0xE5A0`,
  issues `OUT 0x1C = 0x80`, and drains the remaining 8 full sectors
  (4,096 data-register reads).
- With `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS=0` and
  `JUKU_TOP_CHECKPOINT_FDC_STOP_PROMPT=1`, the same late checkpoint
  continues past those data reads and reaches the EKDOS `A>` prompt.
- A single full cosim-prompt-count target,
  `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS=10752`, currently times out
  after the 6,656-byte boundary while looping through keyboard/IRQ
  service around VRAM write count 63,155, so the current proof is split
  across the first and late FDC checkpoint windows.
- Use `JUKU_TOP_CHECKPOINT_FDC_CYCLES=0 JUKU_TOP_CHECKPOINT_FDC_WRITES=63085
  JUKU_TOP_CHECKPOINT_FDC_STOP_IO=1 JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READ=0`
  for the older first-command boundary.
- Use `JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS=0` for the older
  first-data-register-read boundary.
- Use `JUKU_TOP_CHECKPOINT_FDC_CYCLES=0 JUKU_TOP_CHECKPOINT_FDC_WRITES=42000`
  for the earlier key-window narrowing run.
