# juku_top FDC reset alignment

Status: **HDL RESET RUN REACHES DECODED FDC STATUS I/O**

This generated report summarizes the committed reset-driven Verilator
`juku_top` FDC probe for the vendored `media/disks/JUKU1.CPM` path.
The old post-30,180 reset-run divergence is resolved; the current
uninterrupted boundary is the first decoded WD1793 status poll, not the
full EKDOS `A>` prompt.

## Commands

```sh
python3 scripts/report_juku_top_fdc_alignment.py
JUKU_TOP_FDC_SIM=verilator \
JUKU_TOP_FDC_FRAMEIRQ=200000 \
JUKU_TOP_FDC_STOPPIC=0 \
JUKU_TOP_FDC_STOPFDC=1 \
JUKU_TOP_FDC_TIMECAP=1200000000 \
JUKU_TOP_FDC_TIMEOUT=180 \
sync/juku_top_fdc_probe.sh
```

Current HDL probe values: `SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=200000 TRACEPROGRESS=5000 TRACEIO=0 TRACECHK=0 STOPIO=0 MAXVRAM=40000 TIMECAP=1200000000 STOPFDC=1 STOPPIC=0 STOPPPI=0 STOPPROMPT=0 STOPPC=none STOPPC_SKIP=0 TIMEOUT=180`.

## Boundary

| Signal | juku_top Verilator report |
| --- | ---: |
| PC | `0xE771` |
| SP | `0xD432` |
| M-cycles | `1012756` |
| VRAM writes | `30524` |
| memory mode | `1` |
| PPI0 port C | `0x01` |
| PIC ICW1/ICW2/mask | `0xD6` / `0xFE` / `0xDF` |
| frame ticks / IRQ edges | `40` / `10` |
| FDC status | `0x80` |
| decoded FDC reads/writes | `1` / `0` (`1` ios) |

## HDL Report Anchors

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- Last VRAM progress line: `[VRAM] progress writes=30000 mcyc=522138`
- VRAM stop line: `none`
- First PIC line: `[PIC] OUT port=0x00 reg=0 data=0xd6 mcyc=776238 vram=30520 ios=1`
- First IRQ line: `[IRQ] intr rise count=1 mcyc=785934 vram=30524`
- First PPI key-read line: `none`
- First FDC line: `[FDC] IN  port=0x1c reg=0 data=0x80 mcyc=1012756 ios=1`
- FDC stop line: `[FDC] stop ios=1 reads=1 writes=0 mcyc=1012756`
- CPU line: `[CPU] pc=0xe771 sp=0xd432 instr=0xdb ba=0x1c1c db=0xff mcyc=1012756 vram=30524 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0 xchg_dh=1`
- State line: `[STATE] pc=e771 sp=d432 a=80 b=00 c=d7 d=0d e=47 h=01 l=d9 sf=0 zf=1 hf=1 pf=1 cf=0 iff=1 mode=1 portc=01 kbd_col=00 pic_icw1=d6 pic_icw2=fe pic_mask=df pic_expect_icw2=0 fdc_motor_on=0 fdc_status=80 fdc_track=00 fdc_sector=01 fdc_data=00 fdc_command=00 fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=746 raw_reads=424 raw_writes=322 pic_ios=34 pic_reads=0 pic_writes=34 ppi_ios=630 ppi_reads=403 ppi_writes=227 ppi_key_reads=0 fdc_ios=1 fdc_reads=1 fdc_writes=0 frame_ticks=40 intr_edges=10 inta_edges=30`

## Disposition

- The D6 reset-overlay ROM decode now covers `0x0000..0x3FFF`, so the high-BIOS checksum path matches cosim past the old 30,181-write split.
- With `JUKU_TOP_FDC_FRAMEIRQ=200000`, the uninterrupted reset run programs the PIC, takes frame interrupts, and reaches decoded WD1793 status I/O.
- The remaining uninterrupted HDL target is to advance from this first status-poll boundary into the ROMBIOS `TDD` FDC command/data path and the EKDOS `A>` prompt.
