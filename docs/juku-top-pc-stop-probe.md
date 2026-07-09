# juku_top PC-stop probe

Status: **PASS**

This fast diagnostic proves the `juku_top_tb` `+stoppc=HEX` hook used by
`sync/juku_top_fdc_probe.sh`. It stops at an early ROMBIOS address before the
long framebuffer clear, so it can guard the instrumentation without paying the
full post-banner simulation cost.

## Command

```sh
sync/juku_top_pc_stop_probe.sh
```

## Evidence

| Check | Result |
| --- | --- |
| Target PC | `0x01A8` |
| PC stop line observed | PASS |

## Stop State

- PC stop line: `[PC] stop pc=0x01a8 mcyc=33 vram=0 seen=0 skip=0`
- CPU state line: `[CPU] pc=0x01a8 sp=0xxxxx instr=0xd3 ba=0x01a7 db=0xff mcyc=33 vram=0 memr_n=1 memw_n=1 iord_n=1 iowr_n=1 inta_n=1 sync=0 intr=0 xchg_dh=0`

## Disposition

- Use `JUKU_TOP_FDC_STOPPC=HEX` plus optional `JUKU_TOP_FDC_STOPPC_SKIP=N`
  with `sync/juku_top_fdc_probe.sh` for ROMBIOS boundary stops.
- The hook is diagnostic only; default boot and LVS guards leave it disabled.
