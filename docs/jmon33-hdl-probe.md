# jmon33 HDL probe

Status: **JMON33 FIRST-WRITE MATCHES COSIM AND JUKU_TOP**

This probe runs the Monitor 3.3 ROM on the structural model
`juku_top` with frame interrupts enabled. It proves that the HDL twin reaches
jmon33's first video-memory write at FF40h and compares the captured VRAM
bytes with cosim. The default capture stops after one write; overrides change
the capture size. The reported cycle counts are diagnostic, not compared.
This script does not run LVS or verify that a frame interrupt was serviced.

## Command

Run from the repository root with Bash, Python 3, a C compiler (`CC`,
default `cc`), and Icarus Verilog (`iverilog` and `vvp`). The guard
overwrites `cosim/vram.bin`, `hdl/sim/vram_top.bin`, and the generated
`hdl/sim/jmon33.hex`; preserve any captures needed before running it.
It replaces this report only after all checks pass.

```sh
JMON33_HDL_MAXVRAM=1 JMON33_HDL_FRAMEIRQ=200000 JMON33_HDL_TIMECAP=120000000 sync/jmon33_hdl_probe.sh
```

Environment overrides:

- `JMON33_HDL_MAXVRAM` default `1`
- `JMON33_HDL_FRAMEIRQ` default `200000`
- `JMON33_HDL_TIMECAP` default `120000000`

The underlying HDL testbench also accepts `+cursorstop=1`, which stops when
the cosim jmon33 monitor-idle cursor bytes are present in `juku_top` VRAM.
That stronger boundary is intentionally not the default for this fast guard.

## Evidence

| Check | Result |
| --- | --- |
| jmon33 readmemh generated from `roms/jmon33.bin` | PASS |
| cosim first video write address | `0xFF40` |
| cosim first video write cycle | `48521` |
| `juku_top` runs with frame IRQ period `200000` | PASS |
| `juku_top` first video write address | `0xff40` |
| `juku_top` first video write machine cycle | `12151` |
| captured video writes | `1` |
| first-write VRAM dump equals cosim | PASS |

## Scope

- This remains the fast first-video-write HDL guard; it is not the stronger
  user-visible completion check by itself.
- The cosim-side interrupt path is documented in
  `docs/jmon33-interrupt-probe.md`.
- `docs/jmon33-ready-probe.md` defines the cosim monitor-idle framebuffer
  oracle. [HDL cursor probe](jmon33-hdl-cursor-probe.md) records the
  structural comparison status.
