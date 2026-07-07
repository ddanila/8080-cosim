# juku_top checkpoint FDC probe

Status: **PASS**

This diagnostic starts from a generated EKDOS/TDD cosim checkpoint
(`JUKU_TOP_CHECKPOINT_FDC_CYCLES=10066690` or
`JUKU_TOP_CHECKPOINT_FDC_WRITES=63085` when cycle stop is disabled),
loads it into `juku_top`, enables frame IRQs and the
fixed `TDD` keyboard stimulus, and runs toward the 4096 FDC data-register reads.
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
- `JUKU_TOP_CHECKPOINT_FDC_REPORT` default
  `docs/juku-top-checkpoint-fdc-probe.md`

Known useful windows:

- Default `JUKU_TOP_CHECKPOINT_FDC_CYCLES=8711550` proves the first
  13 sectors / 6,656 data-register reads.
- `JUKU_TOP_CHECKPOINT_FDC_CYCLES=10066690
  JUKU_TOP_CHECKPOINT_FDC_STOP_DATA_READS=4096` proves the later
  8 sectors / 4,096 data-register reads.

## Evidence

- Cosim checkpoint exit code: `0`
- Cosim checkpoint cycle: `10066693`
- Cosim checkpoint writes: `73386`
- Cosim checkpoint PC: `0xE5A0`
- Cosim checkpoint key position/phase: `3` / `0`
- HDL resume exit code: `0`
- Timed out: `no`
- First PIC line: `[RESUME-PIC] OUT port=0x01 data=0xdf mcyc=7055 vram=73386 pc=0x068b`
- First no-key keyboard line: `[RESUME-KBD] IN port=0x05 data=0xcf mcyc=10871 vram=73386 pc=0x1463`
- First key stimulus line: `none`
- Last key stimulus line: `none`
- First IRQ line: `[RESUME-IRQ] intr rise count=1 mcyc=10567 vram=73386`
- Last IRQ line: `[RESUME-IRQ] inta fall count=39 mcyc=192205 vram=73396`
- First VRAM line: `none`
- Last complete VRAM line: `none`
- First FDC line: `[RESUME-FDC] OUT port=0x1c reg=0 data=0x80 mcyc=3 vram=73386 ios=1`
- FDC stop line: `[RESUME-FDC] stop reason=data-read-count target=4096 ios=4146 reads=4124 data_reads=4096 writes=22 data=0xe5 mcyc=208825 vram=73396`
- Stop/fail line: `none`

| Trace | Lines |
| --- | ---: |
| PIC writes | `67` |
| keyboard reads | `221` |
| key stimulus | `0` |
| IRQ events | `52` |
| VRAM progress | `0` |
| FDC events | `4147` |

## Boundary

- This is not a prompt proof until EKDOS `A>` is reached through
  checkpoint-resumed `juku_top` CPU execution.
- The default proves the ROMBIOS FDC path drains 13 full 512-byte sectors
  through FDC data-register reads from a checkpointed CPU run.
- A second clean late-sector window at
  `JUKU_TOP_CHECKPOINT_FDC_CYCLES=10066690` resumes at PC `0xE5A0`,
  issues `OUT 0x1C = 0x80`, and drains the remaining 8 full sectors
  (4,096 data-register reads).
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
