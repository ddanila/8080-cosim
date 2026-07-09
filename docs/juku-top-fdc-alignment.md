# juku_top FDC reset alignment

Status: **HDL RESET RUN REACHES DECODED FDC COMMAND I/O**

This generated report summarizes the committed reset-driven Verilator
`juku_top` FDC probe for the vendored `media/disks/JUKU1.CPM` path.
The old post-30,180 reset-run divergence is resolved. The current
uninterrupted boundary reaches decoded WD1793 command/data I/O, but
lands in an early interrupt-path read-sector attempt with sector `0xAA`
rather than the cosim `TDD` sector sequence.
The no-key keyboard scan now matches the cosim anchor; the remaining
reset-run mismatch is the frame-IRQ phase/timer boundary.

## Commands

```sh
python3 scripts/report_juku_top_fdc_alignment.py
JUKU_TOP_FDC_SIM=verilator \
JUKU_TOP_FDC_FRAMEIRQ=200000 \
JUKU_TOP_FDC_FRAMEPHASE=0 \
JUKU_TOP_FDC_STOPPIC=0 \
JUKU_TOP_FDC_STOPFDC=80 \
JUKU_TOP_FDC_TIMECAP=2400000000 \
JUKU_TOP_FDC_MAXVRAM=90000 \
JUKU_TOP_FDC_TIMEOUT=300 \
sync/juku_top_fdc_probe.sh
```

Current HDL probe values: `SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=200000 FRAMEPHASE=0 TRACEPROGRESS=5000 TRACEIO=0 TRACECHK=0 TRACEPPI=1 TRACEIRQ=1 STOPIO=0 MAXVRAM=90000 TIMECAP=2400000000 STOPFDC=80 STOPPIC=0 STOPPPI=0 STOPPROMPT=0 STOPPC=none STOPPC_SKIP=0 TIMEOUT=300`.

## Boundary

| Signal | juku_top Verilator report |
| --- | ---: |
| PC | `0xE5AA` |
| SP | `0xD436` |
| M-cycles | `1014893` |
| VRAM writes | `30524` |
| memory mode | `1` |
| PPI0 port C | `0x75` |
| PIC ICW1/ICW2/mask | `0xD6` / `0xFE` / `0xFF` |
| frame ticks / IRQ edges | `40` / `10` |
| keyboard-port scans | `178` |
| FDC command/status | `0x80` / `0x10` |
| FDC track/sector/data | `0x00` / `0xAA` / `0x00` |
| decoded FDC reads/writes | `77` / `3` (`80` ios) |

## HDL Report Anchors

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- Last VRAM progress line: `[VRAM] progress writes=30000 mcyc=522138`
- VRAM stop line: `none`
- First PIC line: `[PIC] OUT port=0x00 reg=0 data=0xd6 mcyc=776238 vram=30520 ios=1`
- First IRQ line: `[IRQ] intr rise count=1 pc=0xdb02 sp=0xd440 osc=6200001 mcyc=785934 vram=30524`
- First PPI key-read line: `[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1213 mcyc=776367 vram=30520 key_reads=1`
- First PPI line: `[PPI0] IN  port=0x05 reg=1 data=0xcf col=15 key_col=0 key_bit=0 pressed=0 pc=0x1213 mcyc=776367 vram=30520 key_reads=1`
- First FDC line: `[FDC] IN  port=0x1c reg=0 data=0x80 pc=0xe771 sp=0xd432 a=0x11 b=0x00 c=0xd7 d=0x0d e=0x47 h=0x01 l=0xd9 mcyc=1012756 vram=30524 ios=1`
- FDC stop line: `[FDC] stop ios=80 reads=77 writes=3 mcyc=1014893`
- CPU line: `[CPU] pc=0xe5aa sp=0xd436 instr=0xdb ba=0x1f1f db=0xff mcyc=1014893 vram=30524 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0 xchg_dh=1`
- State line: `[STATE] pc=e5aa sp=d436 a=00 b=01 c=35 d=08 e=aa h=aa l=f3 sf=0 zf=0 hf=0 pf=0 cf=0 iff=0 mode=1 portc=75 kbd_col=00 pic_icw1=d6 pic_icw2=fe pic_mask=ff pic_expect_icw2=0 fdc_motor_on=1 fdc_status=10 fdc_track=00 fdc_sector=aa fdc_data=00 fdc_command=80 fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=845 raw_reads=508 raw_writes=337 pic_ios=37 pic_reads=0 pic_writes=37 ppi_ios=647 ppi_reads=411 ppi_writes=236 ppi_key_reads=178 fdc_ios=80 fdc_reads=77 fdc_writes=3 frame_ticks=40 intr_edges=10 inta_edges=30`

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

It reaches `[VRAM] 33812 writes (mcyc=852989) -- dump` with no frame IRQ
and no decoded FDC I/O, matching the cosim first-frame-IRQ framebuffer
position before the reset-run timer currently diverts into the early FDC
helper.

## Disposition

- The D6 reset-overlay ROM decode now covers `0x0000..0x3FFF`, so the high-BIOS checksum path matches cosim past the old 30,181-write split.
- The HDL WD1793 status read now reflects live motor/disk readiness, so the reset run exits the stale not-ready poll and reaches command/data-register traffic.
- The first HDL keyboard-port read is now visible and matches the cosim no-key anchor: `IN 0x05 = 0xCF` at PC `0x1213`, VRAM `30520`.
- With `JUKU_TOP_FDC_FRAMEIRQ=200000`, the uninterrupted reset run programs the PIC, takes frame interrupts, writes WD1793 sector/data/command registers, and enters data-register reads.
- The first frame IRQ is still too early: current reset-run IRQ is at VRAM `30524`, while `docs/ekdos-timing-reference.md` pins the cosim first frame IRQ at VRAM `33812`; a no-frame HDL bound reaches VRAM `33812` at `mcyc=852989` before FDC I/O.
- The remaining uninterrupted HDL target is to align this early interrupt-path read-sector attempt with the cosim ROMBIOS `TDD` sequence: first command `0x02`, sector `0x02`, and then EKDOS `A>`.
