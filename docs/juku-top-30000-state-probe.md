# juku_top 30,000-write state probe

Status: **PASS**

This slow diagnostic compares the fast cosim and LVS-checked `juku_top` at
30,000 framebuffer writes on the vendored `JUKU1.CPM` `TDD` path. The fast
cosim timing reference first touches PIC at 30,520 writes, so this proves whether
the expensive top-level simulation is still aligned immediately before that
post-banner PIC/FDC window.

## Command

```sh
sync/juku_top_30000_state_probe.sh
```

## Evidence

| Check | Result |
| --- | --- |
| Target VRAM writes | `30000` |
| Cosim stop PC | `0x0484` |
| HDL stop PC | `0x0484` |
| Cosim/HDL PC match | PASS |
| VRAM dump bytes | `9640` |
| Cosim VRAM SHA256 | `0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68` |
| HDL VRAM SHA256 | `0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68` |
| Cosim/HDL VRAM match | PASS |
| Cosim/HDL visible state match | PASS |

## Stop State

- Cosim first VRAM line: `[VRAM] first video write @0xD800 cyc=98649`
- Cosim stop line: `stopped pc=0x0484 cyc=1963707 halted=0 iff=0 mode=0 switches=0`
- HDL VRAM stop line: `[VRAM] 30000 writes (mcyc=522138) -- dump`
- HDL CPU state line: `[CPU] pc=0x0484 sp=0xd44c instr=0x36 ba=0xfd2f db=0xff mcyc=522138 vram=30000 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0`
- HDL visible state line: `[STATE] pc=0484 sp=d44c a=a1 b=d7 c=e7 d=00 e=a1 h=fd l=2f sf=1 zf=0 hf=0 pf=0 cf=0 iff=0 mode=0 portc=80 kbd_col=0f pic_icw1=00 pic_icw2=00 pic_mask=ff pic_expect_icw2=0 fdc_motor_on=0 fdc_status=80 fdc_track=00 fdc_sector=01 fdc_data=00 fdc_command=00 fdc_buffer_pos=0 fdc_buffer_len=0`
- HDL I/O summary line: `[IO] raw_ios=29 raw_reads=1 raw_writes=28 pic_ios=0 pic_reads=0 pic_writes=0 ppi_ios=8 ppi_reads=1 ppi_writes=7 ppi_key_reads=0 fdc_ios=0 fdc_reads=0 fdc_writes=0 frame_ticks=49 intr_edges=0 inta_edges=0`

## Disposition

- At 30,000 VRAM writes, `juku_top` and cosim both stop at PC `0x0484`,
  their framebuffer dumps match byte-for-byte, and their visible CPU/PPI/PIC/FDC
  register state matches. FDC status is intentionally excluded at this pre-FDC
  boundary because the HDL shim reports not-ready before motor/command activity.
- The top-level has not diverged before the PIC setup point; it is simply too
  slow for repeated brute-force wall-time probing past 30,520 writes.
- The next useful M2 automation is a checkpoint/fast-forward strategy or a
  narrower post-banner harness, not another larger timeout.
