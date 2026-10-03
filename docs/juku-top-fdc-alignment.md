# juku_top FDC reset alignment

Status: **HDL RESET RUN REACHES EKDOS A> PROMPT**

This report summarizes the [recorded Verilator run](juku-top-fdc-verilator-probe.md)
for `media/disks/JUKU1.CPM`. It checks that report's prompt, PIC and FDC
markers and counts; it does not build or execute the current HDL.
The recorded run drained 10,752 FDC data-register reads and reached
the EKDOS `A>` bitmap at 73,405 framebuffer writes.
See [simulator compatibility](../sync/README.md#simulator-compatibility)
before attempting a current Verilator rerun.

## Commands

```sh
python3 scripts/report_juku_top_fdc_alignment.py
JUKU_TOP_FDC_SIM=verilator \
JUKU_TOP_FDC_FRAMEIRQ=0 \
JUKU_TOP_FDC_FRAMEMCYC=50761 \
JUKU_TOP_FDC_FRAMEPHASE=49891 \
JUKU_TOP_FDC_STOPPIC=0 \
JUKU_TOP_FDC_TRACEFDC=0 \
JUKU_TOP_FDC_STOPFDC=0 \
JUKU_TOP_FDC_STOPPROMPT=1 \
JUKU_TOP_FDC_TIMECAP=12000000000 \
JUKU_TOP_FDC_MAXVRAM=100000 \
JUKU_TOP_FDC_TIMEOUT=420 \
sync/juku_top_fdc_probe.sh
```

## Boundary

| Signal | juku_top Verilator report |
| --- | ---: |
| PC | `0x097A` |
| SP | `0xD2E8` |
| M-cycles | `2701313` |
| VRAM writes | `73405` |
| memory mode | `0` |
| PPI0 port C | `0x04` |
| PIC ICW1/ICW2/mask | `0xD6` / `0xFE` / `0xDF` |
| frame ticks / IRQ edges | `53` / `32` |
| keyboard-port scans | `552` |
| FDC command/status | `0x80` / `0x00` |
| FDC track/sector/data | `0x02` / `0x06` / `0xE5` |
| decoded FDC reads/writes | `10854` / `71` (`10925` ios) |
| FDC data-register reads | `10752` |

## Scope

- The recorded configuration uses a machine-cycle frame period of
  50,761 with the first tick at 49,891, rather than the oscillator-period
  frame scheduler. These values align this ROM/disk path with the C oracle.
- `sync/juku_top_fdc_prompt_check.sh` normally checks committed report
  evidence. Set `JUKU_TOP_FDC_PROMPT_DEEP=1` to compile and rerun the HDL.
- Report consistency alone does not establish current-source execution
  or physical FDC qualification.
