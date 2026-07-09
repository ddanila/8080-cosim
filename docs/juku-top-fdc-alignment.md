# juku_top FDC reset alignment

Status: **HDL RESET RUN REACHES EKDOS A> PROMPT**

This generated report summarizes the committed reset-driven Verilator
`juku_top` FDC probe for the vendored `media/disks/JUKU1.CPM` path.
The old post-30,180 reset-run divergence is resolved. The current
uninterrupted boundary now reaches the EKDOS `A>` prompt bitmap from
reset through the cosim ROMBIOS `TDD` path: first FDC command at VRAM
63,085, all 10,752 FDC data-register reads drained, and prompt at
VRAM 73,405.
The no-key keyboard scan now matches the cosim anchor, and the
no-frame reset run now matches cosim through the first-frame anchor
after the PPI0 Port C latch fix.

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

Current HDL probe values: `SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=0 FRAMEPHASE=49891 FRAMEMCYC=50761 TRACEPROGRESS=10000 VRAMSTOP_SYNC=0 TRACEIO=0 TRACECHK=0 TRACEPPI=0 TRACEIRQ=0 TRACEFDC=0 STOPIO=0 MAXVRAM=100000 TIMECAP=12000000000 STOPFDC=0 STOPFDCDATA=0 STOPPIC=0 STOPPPI=0 STOPPROMPT=1 STOPPC=none STOPPC_SKIP=0 TIMEOUT=420`.

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

## Frame Calibration Check

The no-frame calibration bound used for the current diagnosis is:

```sh
JUKU_TOP_FDC_SIM=verilator \
JUKU_TOP_FDC_FRAMEIRQ=0 \
JUKU_TOP_FDC_STOPFDC=0 \
JUKU_TOP_FDC_MAXVRAM=33812 \
JUKU_TOP_FDC_TIMECAP=1200000000 \
JUKU_TOP_FDC_TIMEOUT=180 \
sync/juku_top_fdc_probe.sh
```

It reaches `[VRAM] 33812 writes (mcyc=811306) -- sync dump` with no
frame IRQ and no decoded FDC I/O. The effective HDL PC is `0x0E23`,
the framebuffer hash is byte-identical to cosim, and visible
CPU/PPI/PIC/FDC state matches at the first-frame anchor.

## Machine-Cycle Frame Probe

The top-level FDC wrapper also has an opt-in machine-cycle frame scheduler:

```sh
JUKU_TOP_FDC_SIM=verilator \
JUKU_TOP_FDC_FRAMEIRQ=0 \
JUKU_TOP_FDC_FRAMEMCYC=50761 \
JUKU_TOP_FDC_FRAMEPHASE=49891 \
JUKU_TOP_FDC_TRACEIRQ=2 \
JUKU_TOP_FDC_MAXVRAM=50000 \
JUKU_TOP_FDC_TIMECAP=300000000 \
JUKU_TOP_FDC_TIMEOUT=90 \
sync/juku_top_fdc_probe.sh
```

That post-fix calibration keeps the first accepted HDL frame IRQ at
the cosim framebuffer/mcycle anchor: `[IRQ] intr rise count=1
pc=0x0e24 sp=0xd434 ... mcyc=811306 vram=33812`, followed by INTA
bytes `0xCD 0xD4 0xFE`. The 50,761-mcycle period also tracks the
cosim 200,000-cycle frame cadence closely enough for the reset run to
reach the first ROMBIOS FDC command at PC `0xE5DE`, drain all
10,752 data-register reads, and render the EKDOS `A>` prompt.

## Disposition

- The D6 reset-overlay ROM decode now covers `0x0000..0x3FFF`, so the high-BIOS checksum path matches cosim past the old 30,181-write split.
- The HDL WD1793 status read now reflects live motor/disk readiness, so the reset run exits the stale not-ready poll and reaches command/data-register traffic.
- The first HDL keyboard-port read is now visible and matches the cosim no-key anchor: `IN 0x05 = 0xCF` at PC `0x1213`, VRAM `30520`.
- With `JUKU_TOP_FDC_FRAMEMCYC=50761` and `JUKU_TOP_FDC_FRAMEPHASE=49891`, the uninterrupted reset run programs the PIC, takes calibrated frame interrupts, writes WD1793 sector/data/command registers, and enters the ROMBIOS FDC path at the cosim VRAM boundary.
- The oscillator-period reset run still takes its first IRQ too early: current reset-run IRQ is at VRAM `30524`, while `docs/ekdos-timing-reference.md` pins the cosim first frame IRQ at VRAM `33812`.
- The machine-cycle scheduler now aligns the first accepted frame IRQ to `mcyc=811306` / VRAM `33812`; the HDL effective PC, framebuffer, and visible state match cosim there after the PPI0 Port C latch fix.
- The uninterrupted reset run now drains all 10,752 FDC data-register reads and reaches the EKDOS `A>` prompt bitmap at VRAM `73405`, PC `0x097A`.
