# juku_top FDC reset alignment

Status: **HDL RESET RUN REACHES DECODED FDC COMMAND I/O**

This generated report summarizes the committed reset-driven Verilator
`juku_top` FDC probe for the vendored `media/disks/JUKU1.CPM` path.
The old post-30,180 reset-run divergence is resolved. The current
uninterrupted boundary reaches the cosim ROMBIOS `TDD` first-FDC
sequence: restore command `0x02` at VRAM 63,085, then sector/data
setup at VRAM 63,095.
The no-key keyboard scan now matches the cosim anchor, and the
no-frame reset run now matches cosim through the first-frame anchor
after the PPI0 Port C latch fix. The remaining reset-run mismatch is
after calibrated interrupt entry and before uninterrupted EKDOS prompt.

## Commands

```sh
python3 scripts/report_juku_top_fdc_alignment.py
JUKU_TOP_FDC_SIM=verilator \
JUKU_TOP_FDC_FRAMEIRQ=0 \
JUKU_TOP_FDC_FRAMEMCYC=50761 \
JUKU_TOP_FDC_FRAMEPHASE=49891 \
JUKU_TOP_FDC_STOPPIC=0 \
JUKU_TOP_FDC_STOPFDC=20 \
JUKU_TOP_FDC_TIMECAP=1800000000 \
JUKU_TOP_FDC_MAXVRAM=90000 \
JUKU_TOP_FDC_TIMEOUT=180 \
sync/juku_top_fdc_probe.sh
```

Current HDL probe values: `SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=0 FRAMEPHASE=49891 FRAMEMCYC=50761 TRACEPROGRESS=5000 VRAMSTOP_SYNC=0 TRACEIO=0 TRACECHK=0 TRACEPPI=0 TRACEIRQ=1 STOPIO=0 MAXVRAM=90000 TIMECAP=1800000000 STOPFDC=20 STOPPIC=0 STOPPPI=0 STOPPROMPT=0 STOPPC=none STOPPC_SKIP=0 TIMEOUT=180`.

## Boundary

| Signal | juku_top Verilator report |
| --- | ---: |
| PC | `0xE64D` |
| SP | `0xD6DC` |
| M-cycles | `2159597` |
| VRAM writes | `63095` |
| memory mode | `1` |
| PPI0 port C | `0x05` |
| PIC ICW1/ICW2/mask | `0xD6` / `0xFE` / `0xDF` |
| frame ticks / IRQ edges | `42` / `27` |
| keyboard-port scans | `467` |
| FDC command/status | `0x1A` / `0x00` |
| FDC track/sector/data | `0x00` / `0x03` / `0x00` |
| decoded FDC reads/writes | `12` / `8` (`20` ios) |

## HDL Report Anchors

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- Last VRAM progress line: `[VRAM] progress writes=60000 mcyc=1396952`
- VRAM stop line: `none`
- First PIC line: `[PIC] OUT port=0x00 reg=0 data=0xd6 mcyc=776238 vram=30520 ios=1`
- First IRQ line: `[IRQ] intr rise count=1 pc=0x0e24 sp=0xd434 osc=6400051 mcyc=811306 vram=33812`
- First PPI key-read line: `none`
- First PPI line: `none`
- First FDC line: `[FDC] OUT port=0x1c reg=0 data=0x02 pc=0xe5de sp=0xd6de a=0x02 b=0x00 c=0xea d=0xd9 e=0x44 h=0x01 l=0xe5 mcyc=1590617 vram=63085 ios=1`
- FDC stop line: `[FDC] stop ios=20 reads=12 writes=8 mcyc=2159597`
- CPU line: `[CPU] pc=0xe64d sp=0xd6dc instr=0xd3 ba=0xe64d db=0xff mcyc=2159597 vram=63095 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=1 intr=0 xchg_dh=0`
- State line: `[STATE] pc=e64d sp=d6dc a=1a b=18 c=00 d=02 e=50 h=01 l=e5 sf=0 zf=0 hf=0 pf=0 cf=0 iff=1 mode=1 portc=05 kbd_col=00 pic_icw1=d6 pic_icw2=fe pic_mask=df pic_expect_icw2=0 fdc_motor_on=1 fdc_status=00 fdc_track=00 fdc_sector=03 fdc_data=00 fdc_command=1a fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=10795 raw_reads=5358 raw_writes=5437 pic_ios=93 pic_reads=0 pic_writes=93 ppi_ios=10495 ppi_reads=5292 ppi_writes=5203 ppi_key_reads=467 fdc_ios=20 fdc_reads=12 fdc_writes=8 frame_ticks=42 intr_edges=27 inta_edges=81`

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
reach the first ROMBIOS FDC command at PC `0xE5DE`, VRAM 63,085.

## Disposition

- The D6 reset-overlay ROM decode now covers `0x0000..0x3FFF`, so the high-BIOS checksum path matches cosim past the old 30,181-write split.
- The HDL WD1793 status read now reflects live motor/disk readiness, so the reset run exits the stale not-ready poll and reaches command/data-register traffic.
- The first HDL keyboard-port read is now visible and matches the cosim no-key anchor: `IN 0x05 = 0xCF` at PC `0x1213`, VRAM `30520`.
- With `JUKU_TOP_FDC_FRAMEMCYC=50761` and `JUKU_TOP_FDC_FRAMEPHASE=49891`, the uninterrupted reset run programs the PIC, takes calibrated frame interrupts, writes WD1793 sector/data/command registers, and enters the ROMBIOS FDC path at the cosim VRAM boundary.
- The oscillator-period reset run still takes its first IRQ too early: current reset-run IRQ is at VRAM `30524`, while `docs/ekdos-timing-reference.md` pins the cosim first frame IRQ at VRAM `33812`.
- The machine-cycle scheduler now aligns the first accepted frame IRQ to `mcyc=811306` / VRAM `33812`; the HDL effective PC, framebuffer, and visible state match cosim there after the PPI0 Port C latch fix.
- The remaining uninterrupted HDL target is now the FDC data-drain/prompt path after the observed first command `0x02`, sector `0x02`, and read-sector setup.
