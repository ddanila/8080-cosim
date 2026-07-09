# juku_top 33812-write state probe

Status: **PASS**

This slow diagnostic compares the fast cosim and LVS-checked `juku_top` at
33812 framebuffer writes on the vendored `JUKU1.CPM` `TDD` path. The fast
cosim timing reference first touches PIC at 30,520 writes; the default 30,000
write target proves whether the expensive top-level simulation is still aligned
immediately before that post-banner PIC/FDC window.

## Command

```sh
sync/juku_top_30000_state_probe.sh
```

## Evidence

| Check | Result |
| --- | --- |
| Target VRAM writes | `33812` |
| HDL simulator | `verilator` |
| Cosim frame cycles | `0` |
| HDL frame settings | `FRAMEIRQ=0 FRAMEPHASE=0 FRAMEMCYC=0` |
| Keyboard start VRAM | `42000` |
| HDL reached dump point | PASS |
| HDL timeout exit code | `0` |
| Cosim stop PC | `0x0E23` |
| HDL stop PC | `0x0e24` |
| HDL effective PC | `0x0e23` |
| Cosim/HDL effective PC match | PASS |
| VRAM dump bytes | `9640` |
| Cosim VRAM SHA256 | `559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d` |
| HDL VRAM SHA256 | `559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d` |
| Cosim/HDL VRAM match | PASS |
| Cosim/HDL visible state match | PASS |

## Stop State

- Cosim first VRAM line: `[VRAM] first video write @0xD800 cyc=98649`
- Cosim stop line: `stopped pc=0x0E23 cyc=3199972 halted=0 iff=1 mode=0 switches=16`
- HDL VRAM stop line: `[VRAM] 33812 writes (mcyc=811306) -- sync dump`
- HDL CPU state line: `[CPU] pc=0x0e24 sp=0xd434 instr=0x03 ba=0x0e23 db=0x03 mcyc=811306 vram=33812 memr_n=0 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0 xchg_dh=1`
- HDL visible state line: `[STATE] pc=0e24 sp=d434 a=00 b=e4 c=b1 d=00 e=28 h=fd l=d0 sf=0 zf=1 hf=0 pf=1 cf=0 iff=1 mode=0 portc=00 kbd_col=07 pic_icw1=d6 pic_icw2=fe pic_mask=df pic_expect_icw2=0 fdc_motor_on=0 fdc_status=80 fdc_track=00 fdc_sector=01 fdc_data=00 fdc_command=00 fdc_buffer_pos=0 fdc_buffer_len=0`
- HDL I/O summary line: `[IO] raw_ios=97 raw_reads=33 raw_writes=64 pic_ios=4 pic_reads=0 pic_writes=4 ppi_ios=72 ppi_reads=33 ppi_writes=39 ppi_key_reads=8 fdc_ios=0 fdc_reads=0 fdc_writes=0 frame_ticks=0 intr_edges=0 inta_edges=0`

## Disposition

- When HDL reaches the requested dump point, this guard compares PC,
  framebuffer bytes, and visible CPU/PPI/PIC/FDC register state against cosim.
- FDC status is intentionally excluded at this pre-FDC boundary because the HDL
  shim reports not-ready before motor/command activity.
- If HDL does not reach the requested dump point within the bound, the result is
  a reachability limit rather than a functional mismatch.

## Result Interpretation

- HDL reached the 33812-write dump point, so the PC, framebuffer, and visible
  state comparisons above are authoritative for that boundary.
