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

Recorded HDL probe values: `DISK=media/disks/JUKU1.CPM SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=0 FRAMEPHASE=49891 FRAMEMCYC=50761 TRACEPROGRESS=10000 VRAMSTOP_SYNC=0 TRACEIO=0 TRACECHK=0 TRACEPPI=0 TRACEIRQ=0 TRACEFDC=0 STOPIO=0 MAXVRAM=100000 TIMECAP=12000000000 STOPFDC=0 STOPFDCDATA=0 STOPPIC=0 STOPPPI=0 STOPPROMPT=1 STOPPC=none STOPPC_SKIP=0 TIMEOUT=420`.

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

## HDL Report Anchors

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- Last VRAM progress line: `[VRAM] progress writes=70000 mcyc=2381003`
- VRAM stop line: `none`
- First PIC line: `[PIC] OUT port=0x00 reg=0 data=0xd6 mcyc=776238 vram=30520 ios=1`
- First IRQ line: `none`
- First PPI key-read line: `none`
- First PPI line: `none`
- First FDC line: `none`
- FDC stop line: `none`
- FDC data-stop line: `none`
- EKDOS prompt line: `[PROMPT] EKDOS A> prompt reached x=0 y=70 mcyc=2701313 vram=73405 pc=0x097a`
- CPU line: `[CPU] pc=0x097a sp=0xd2e8 instr=0x77 ba=0xe431 db=0xff mcyc=2701313 vram=73405 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0 xchg_dh=1`
- State line: `[STATE] pc=097a sp=d2e8 a=00 b=02 c=28 d=d4 e=97 h=e4 l=31 sf=0 zf=0 hf=1 pf=0 cf=0 iff=1 mode=0 portc=04 kbd_col=00 pic_icw1=d6 pic_icw2=fe pic_mask=df pic_expect_icw2=0 fdc_motor_on=1 fdc_status=00 fdc_track=02 fdc_sector=06 fdc_data=e5 fdc_command=80 fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=22945 raw_reads=16765 raw_writes=6180 pic_ios=190 pic_reads=0 pic_writes=190 ppi_ios=11613 ppi_reads=5847 ppi_writes=5766 ppi_key_reads=552 fdc_ios=10925 fdc_reads=10854 fdc_writes=71 frame_ticks=53 intr_edges=32 inta_edges=96`
- FDC state line: `[FDCSTATE] data_reads=10752 buffer_pos=0 buffer_len=0`

## Scope

- The recorded configuration uses a machine-cycle frame period of
  50,761 with the first tick at 49,891, rather than the oscillator-period
  frame scheduler. These values align this ROM/disk path with the C oracle.
- `sync/juku_top_fdc_prompt_check.sh` normally checks committed report
  evidence. Set `JUKU_TOP_FDC_PROMPT_DEEP=1` to compile and rerun the HDL.
- Report consistency alone does not establish current-source execution
  or physical FDC qualification.
