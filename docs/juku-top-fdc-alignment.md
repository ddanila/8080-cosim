# juku_top FDC reset alignment

Status: **HDL RESET PATH DIVERGES BEFORE COSIM FDC WINDOW**

This generated report compares the fast cosim `TDD` path at 70,000
framebuffer writes against the committed reset-driven Verilator
`juku_top` report for the same vendored `media/disks/JUKU1.CPM` path.
It keeps the long HDL run out of CI while making the current M2
alignment gap explicit and freshness-checked.

## Commands

```sh
python3 scripts/report_juku_top_fdc_alignment.py
JUKU_TOP_FDC_SIM=verilator JUKU_TOP_FDC_MAXVRAM=70000 JUKU_TOP_FDC_TIMEOUT=420 sync/juku_top_fdc_probe.sh
```

## 70,000-Write State

| Signal | cosim | juku_top Verilator report |
| --- | ---: | ---: |
| PC | `0x0E23` | `0x0244` |
| SP | `0xD2E4` | `0xD44E` |
| cycles/mcycles | `9652795` | `16759491` |
| memory mode | `0` | `0` |
| PPI0 port C | `0x04` | `0x80` |
| PIC ICW1 | `0xD6` | `0x00` |
| PIC ICW2 | `0xFE` | `0x00` |
| PIC mask | `0xDF` | `0xFF` |
| keyboard position/phase | `3` / `0` | visible stimulus only |
| FDC command | `0x80` | `0x00` |
| FDC track/sector | `01` / `04` | `00` / `01` |
| FDC data reads | `6656` | `0` decoded reads (`0` ios) |

## HDL Report Anchors

- Stop line: `[VRAM] 70000 writes (mcyc=16759491) -- dump`
- CPU line: `pc=0x0244 sp=0xd44e instr=0x36 ba=0xfd9f db=0xff mcyc=16759491 vram=70000 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0`
- State line: `pc=0244 sp=d44e a=63 b=d7 c=e7 d=02 e=61 h=fd l=9f sf=0 zf=0 hf=0 pf=1 cf=0 iff=0 mode=0 portc=80 kbd_col=0f pic_icw1=00 pic_icw2=00 pic_mask=ff pic_expect_icw2=0 fdc_motor_on=0 fdc_status=80 fdc_track=00 fdc_sector=01 fdc_data=00 fdc_command=00 fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `raw_ios=661 raw_reads=107 raw_writes=554 pic_ios=0 pic_reads=0 pic_writes=0 ppi_ios=442 ppi_reads=107 ppi_writes=335 ppi_key_reads=0 fdc_ios=0 fdc_reads=0 fdc_writes=0 frame_ticks=1727 intr_edges=0 inta_edges=0`
- First keyboard line: `[KBD] press key=0 col=4 bit=3 shift=1 mcyc=8520743 vram=42000`
- Last keyboard line: `[KBD] release key=2 mcyc=9089124 vram=60365`

## Disposition

- This is not just a simulator-throughput limitation at the 70,000-write boundary.
- Cosim is already in the interrupt/FDC path with 6,656 data-register reads, while reset-driven `juku_top` has not programmed the PIC and has no decoded FDC I/O.
- The next automatic target is the interval after the proven 30,000-write match and before cosim PC `0x02B9` / first PIC programming.
