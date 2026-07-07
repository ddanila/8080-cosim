# juku_top checkpoint FDC probe

Status: **BOUNDARY NOT YET FDC**

This diagnostic starts from the 30,000-write EKDOS/TDD cosim
checkpoint, loads it into `juku_top`, enables frame IRQs and the
fixed `TDD` keyboard stimulus, and runs toward the first decoded
WD1793/VG93 I/O. It is the checkpointed counterpart to
`sync/juku_top_fdc_probe.sh`.

## Command

```sh
sync/juku_top_checkpoint_fdc_probe.py
```

Environment overrides:

- `JUKU_TOP_CHECKPOINT_FDC_TIMEOUT` default `300` seconds
- `JUKU_TOP_CHECKPOINT_FDC_FRAMEIRQ` default `80000`
- `JUKU_TOP_CHECKPOINT_FDC_KEYAT` default `42000`
- `JUKU_TOP_CHECKPOINT_FDC_KHOLD` default `900000`
- `JUKU_TOP_CHECKPOINT_FDC_KGAP` default `900000`
- `JUKU_TOP_CHECKPOINT_FDC_MAX_MCYC` default `1000000`
- `JUKU_TOP_CHECKPOINT_FDC_TIMECAP` default `900000000`

## Evidence

- Cosim checkpoint exit code: `0`
- HDL resume exit code: `124`
- Timed out: `yes`
- First PIC line: `[RESUME-PIC] OUT port=0x00 data=0xd6 mcyc=25615 vram=30321 pc=0x02b9`
- First no-key keyboard line: `[RESUME-KBD] IN port=0x05 data=0xcf mcyc=25744 vram=30321 pc=0x1213`
- First key stimulus line: `none`
- Last key stimulus line: `none`
- First IRQ line: `[RESUME-IRQ] inta fall count=1 mcyc=1 vram=30000`
- Last IRQ line: `[RESUME-IRQ] intr rise count=2 mcyc=40406 vram=30560`
- First VRAM line: `[RESUME-VRAM] writes=30100 mcyc=20946 pc=0x031c`
- Last complete VRAM line: `[RESUME-VRAM] writes=35900 mcyc=94598 pc=0x0e23`
- First FDC line: `none`
- FDC stop line: `none`
- Stop/fail line: `none`

| Trace | Lines |
| --- | ---: |
| PIC writes | `4` |
| keyboard reads | `8` |
| key stimulus | `0` |
| IRQ events | `6` |
| VRAM progress | `60` |
| FDC events | `0` |

## Boundary

- This is not a prompt proof until decoded FDC I/O and then EKDOS `A>`
  are reached through CPU execution.
- A timeout with PIC/KBD/IRQ/key evidence is still useful: it proves the
  checkpointed run is past the previous no-frame/no-key boundary and
  identifies the next missing event.
- Current boundary: the checkpointed run now enables frame interrupts and
  reaches the frame-handler drawing loop around PC `0x0e23`, but no key
  stimulus is emitted before the timeout because the run does not reach the
  real `TDD` key window at 42,000 framebuffer writes.

## Failures

- checkpoint-resumed HDL run did not reach decoded FDC I/O

## HDL stdout tail

```
[RESUME-IRQ] intr rise count=1 mcyc=30404 vram=30560
[RESUME-IRQ] inta fall count=2 mcyc=30407 vram=30560
[RESUME-IRQ] inta fall count=3 mcyc=30408 vram=30560
[RESUME-IRQ] inta fall count=4 mcyc=30409 vram=30560
[RESUME-IRQ] intr rise count=2 mcyc=40406 vram=30560
[RESUME-VRAM] writes=30600 mcyc=41840 pc=0x0fe7
[RESUME-VRAM] writes=30700 mcyc=42666 pc=0x0fe7
[RESUME-VRAM] writes=30800 mcyc=43598 pc=0x0e23
[RESUME-VRAM] writes=30900 mcyc=44598 pc=0x0e23
[RESUME-VRAM] writes=31000 mcyc=45598 pc=0x0e23
[RESUME-VRAM] writes=31100 mcyc=46598 pc=0x0e23
[RESUME-VRAM] writes=31200 mcyc=47598 pc=0x0e23
[RESUME-VRAM] writes=31300 mcyc=48598 pc=0x0e23
[RESUME-VRAM] writes=31400 mcyc=49598 pc=0x0e23
[RESUME-VRAM] writes=31500 mcyc=50598 pc=0x0e23
[RESUME-VRAM] writes=31600 mcyc=51598 pc=0x0e23
[RESUME-VRAM] writes=31700 mcyc=52598 pc=0x0e23
[RESUME-VRAM] writes=31800 mcyc=53598 pc=0x0e23
[RESUME-VRAM] writes=31900 mcyc=54598 pc=0x0e23
[RESUME-VRAM] writes=32000 mcyc=55598 pc=0x0e23
[RESUME-VRAM] writes=32100 mcyc=56598 pc=0x0e23
[RESUME-VRAM] writes=32200 mcyc=57598 pc=0x0e23
[RESUME-VRAM] writes=32300 mcyc=58598 pc=0x0e23
[RESUME-VRAM] writes=32400 mcyc=59598 pc=0x0e23
[RESUME-VRAM] writes=32500 mcyc=60598 pc=0x0e23
[RESUME-VRAM] writes=32600 mcyc=61598 pc=0x0e23
[RESUME-VRAM] writes=32700 mcyc=62598 pc=0x0e23
[RESUME-VRAM] writes=32800 mcyc=63598 pc=0x0e23
[RESUME-VRAM] writes=32900 mcyc=64598 pc=0x0e23
[RESUME-VRAM] writes=33000 mcyc=65598 pc=0x0e23
[RESUME-VRAM] writes=33100 mcyc=66598 pc=0x0e23
[RESUME-VRAM] writes=33200 mcyc=67598 pc=0x0e23
[RESUME-VRAM] writes=33300 mcyc=68598 pc=0x0e23
[RESUME-VRAM] writes=33400 mcyc=69598 pc=0x0e23
[RESUME-VRAM] writes=33500 mcyc=70598 pc=0x0e23
[RESUME-VRAM] writes=33600 mcyc=71598 pc=0x0e23
[RESUME-VRAM] writes=33700 mcyc=72598 pc=0x0e23
[RESUME-VRAM] writes=33800 mcyc=73598 pc=0x0e23
[RESUME-VRAM] writes=33900 mcyc=74598 pc=0x0e23
[RESUME-VRAM] writes=34000 mcyc=75598 pc=0x0e23
[RESUME-VRAM] writes=34100 mcyc=76598 pc=0x0e23
[RESUME-VRAM] writes=34200 mcyc=77598 pc=0x0e23
[RESUME-VRAM] writes=34300 mcyc=78598 pc=0x0e23
[RESUME-VRAM] writes=34400 mcyc=79598 pc=0x0e23
[RESUME-VRAM] writes=34500 mcyc=80598 pc=0x0e23
[RESUME-VRAM] writes=34600 mcyc=81598 pc=0x0e23
[RESUME-VRAM] writes=34700 mcyc=82598 pc=0x0e23
[RESUME-VRAM] writes=34800 mcyc=83598 pc=0x0e23
[RESUME-VRAM] writes=34900 mcyc=84598 pc=0x0e23
[RESUME-VRAM] writes=35000 mcyc=85598 pc=0x0e23
[RESUME-VRAM] writes=35100 mcyc=86598 pc=0x0e23
[RESUME-VRAM] writes=35200 mcyc=87598 pc=0x0e23
[RESUME-VRAM] writes=35300 mcyc=88598 pc=0x0e23
[RESUME-VRAM] writes=35400 mcyc=89598 pc=0x0e23
[RESUME-VRAM] writes=35500 mcyc=90598 pc=0x0e23
[RESUME-VRAM] writes=35600 mcyc=91598 pc=0x0e23
[RESUME-VRAM] writes=35700 mcyc=92598 pc=0x0e23
[RESUME-VRAM] writes=35800 mcyc=93598 pc=0x0e23
[RESUME-VRAM] writes=35900 mcyc=94598 pc=0x0e23
[RESUME-VRAM] writes=3600
```
