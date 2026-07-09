# juku_top FDC Verilator probe

Status: **HDL JUKU_TOP FDC PATH NOT YET OBSERVED**

This bounded diagnostic runs the LVS-checked `juku_top` with the vendored
Juku disk image, frame interrupts, and the fixed ROMBIOS `TDD` keyboard
sequence enabled. The default simulator is Icarus Verilog, matching the CI
toolchain. Set `JUKU_TOP_FDC_SIM=verilator` for a faster local/deep reset
run through the same testbench and stop hooks.

## Command

```sh
sync/juku_top_fdc_probe.sh
```

Environment overrides:

- `JUKU_TOP_FDC_DISK` default `media/disks/JUKU1.CPM`
- `JUKU_TOP_FDC_SIM` default `icarus`; optional `verilator`
- `JUKU_TOP_FDC_KEYAT` default `42000`
- `JUKU_TOP_FDC_KHOLD` default `900000`
- `JUKU_TOP_FDC_KGAP` default `900000`
- `JUKU_TOP_FDC_FRAMEIRQ` default `80000`
- `JUKU_TOP_FDC_TRACEPROGRESS` default `5000`
- `JUKU_TOP_FDC_TRACEIO` default `0`
- `JUKU_TOP_FDC_STOPIO` default `0`
- `JUKU_TOP_FDC_STOPFDC` default `1`
- `JUKU_TOP_FDC_STOPPIC` default `0`
- `JUKU_TOP_FDC_STOPPPI` default `0`
- `JUKU_TOP_FDC_STOPPROMPT` default `0`; set to `1` to stop when the
  EKDOS `A>` bitmap appears at `x=0`, `y=70`
- `JUKU_TOP_FDC_STOPPC` optional hexadecimal CPU PC stop hook
- `JUKU_TOP_FDC_TIMEOUT` default `60` seconds

Current values: `SIM=verilator KEYAT=42000 KHOLD=900000 KGAP=900000 FRAMEIRQ=80000 TRACEPROGRESS=5000 TRACEIO=0 STOPIO=0 MAXVRAM=70000 TIMECAP=4000000000 STOPFDC=1 STOPPIC=1 STOPPPI=0 STOPPROMPT=0 STOPPC=none TIMEOUT=420`.

## Evidence

| Check | Result |
| --- | --- |
| simulator | `verilator` |
| vvp/timeout exit code | `0` |
| vendored raw disk loaded | PASS |
| first VRAM write observed | PASS |
| VRAM progress trace observed | PASS |
| keyboard trace observed | PASS |
| raw I/O trace observed | NO |
| PIC setup trace observed | NO |
| PPI key-read trace observed | NO |
| IRQ trace observed | NO |
| decoded FDC I/O observed | NO |
| EKDOS `A>` prompt bitmap observed | NO |
| keyboard trace lines | `6` |
| VRAM progress trace lines | `14` |
| PIC trace lines | `0` |
| PPI key-read trace lines | `0` |
| IRQ trace lines | `0` |
| raw I/O trace lines | `0` |
| FDC trace lines | `0` |

## Stop State

- Disk line: `FDC-1793: loaded raw disk media/disks/JUKU1.CPM (2 sides)`
- Build summary line: `- Verilator: Walltime 15.848 s (elab=0.020, cvt=0.184, bld=15.594); cpu 0.254 s on 1 threads; alloced 17.203 MB`
- Verilator walltime line: `- Verilator: $finish at 3s; walltime 200.190 s; speed 13.808 ms/s`
- First VRAM line: `[VRAM] first video write @0xd800 mcyc=25011`
- Last VRAM progress line: `[VRAM] progress writes=70000 mcyc=16759491`
- VRAM stop line: `[VRAM] 70000 writes (mcyc=16759491) -- dump`
- First keyboard line: `[KBD] press key=0 col=4 bit=3 shift=1 mcyc=8520743 vram=42000`
- Last keyboard line: `[KBD] release key=2 mcyc=9089124 vram=60365`
- First PIC line: `none`
- PIC stop line: `none`
- First PPI key-read line: `none`
- PPI stop line: `none`
- First IRQ line: `none`
- First raw I/O line: `none`
- Raw I/O stop line: `none`
- First FDC line: `none`
- FDC stop line: `none`
- EKDOS prompt line: `none`
- PC stop line: `none`
- Time-cap line: `none`
- CPU state line: `[CPU] pc=0x0244 sp=0xd44e instr=0x36 ba=0xfd9f db=0xff mcyc=16759491 vram=70000 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0`
- Visible state line: `[STATE] pc=0244 sp=d44e a=63 b=d7 c=e7 d=02 e=61 h=fd l=9f sf=0 zf=0 hf=0 pf=1 cf=0 iff=0 mode=0 portc=80 kbd_col=0f pic_icw1=00 pic_icw2=00 pic_mask=ff pic_expect_icw2=0 fdc_motor_on=0 fdc_status=80 fdc_track=00 fdc_sector=01 fdc_data=00 fdc_command=00 fdc_buffer_pos=0 fdc_buffer_len=0`
- I/O summary line: `[IO] raw_ios=661 raw_reads=107 raw_writes=554 pic_ios=0 pic_reads=0 pic_writes=0 ppi_ios=442 ppi_reads=107 ppi_writes=335 ppi_key_reads=0 fdc_ios=0 fdc_reads=0 fdc_writes=0 frame_ticks=1727 intr_edges=0 inta_edges=0`

## Disposition

- The top-level bench now has opt-in `+ekdoskeys=1`, `+traceio=1`,
  `+stopio=N`, `+tracepic=1`, `+stoppic=N`, `+tracefdc=1`, and
  `+stopfdc=N`, plus `+stopprompt=1` for the EKDOS `A>` bitmap and
  `+stoppc=HEX` for exact CPU address stops.
- Existing boot guards keep those hooks disabled, preserving the byte-identical
  ekta37 boot comparison.
- `docs/ekdos-timing-reference.md` shows the fast cosim target for this same
  vendored `TDD` path: first PIC/PPI setup around 30,520 VRAM writes, first
  frame IRQ at 33,812 VRAM writes, and first FDC command at 63,085 VRAM writes.
- The remaining M2 target is still the full `juku_top` ROMBIOS `TDD` path to
  an EKDOS `A>` prompt.
