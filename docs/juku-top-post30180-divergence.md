# juku_top post-30,180 divergence

Status: **RESOLVED: RESET-RUN CHECKSUM PATH MATCHES COSIM**

The reset-driven `juku_top` Verilator run now remains byte-aligned with cosim
through the old post-30,180 boundary on the vendored `JUKU1.CPM` `TDD` path.
The divergence was caused by an incomplete D6 reset-overlay ROM decode in
`hdl/devices.v`: mode 0 was documented as `0x0000..0x3FFF`, but the HDL only
selected ROM for `0x0000..0x1FFF`. The ROMBIOS checksum helper therefore read
RAM at the `0x2000` high-BIOS block and computed the wrong byte.

## Commands

```sh
JUKU_TOP_FDC_SIM=verilator JUKU_TOP_FDC_TIMECAP=4000000000 \
  JUKU_TOP_30000_WRITES=30180 \
  JUKU_TOP_30000_REPORT=/tmp/juku-top-30180-fixed.md \
  sync/juku_top_30000_state_probe.sh

JUKU_TOP_FDC_SIM=verilator JUKU_TOP_FDC_TIMECAP=4000000000 \
  JUKU_TOP_30000_WRITES=30181 \
  JUKU_TOP_30000_REPORT=/tmp/juku-top-30181-fixed.md \
  sync/juku_top_30000_state_probe.sh

JUKU_TOP_FDC_SIM=verilator JUKU_TOP_FDC_TIMECAP=4000000000 \
  JUKU_TOP_30000_WRITES=30182 \
  JUKU_TOP_30000_REPORT=/tmp/juku-top-30182-fixed.md \
  sync/juku_top_30000_state_probe.sh

JUKU_TOP_FDC_SIM=verilator JUKU_TOP_FDC_TIMECAP=4000000000 \
  JUKU_TOP_FDC_STOPPC=03EB JUKU_TOP_FDC_STOPPC_SKIP=4 \
  JUKU_TOP_FDC_TRACECHK=2 \
  JUKU_TOP_FDC_STOPFDC=0 \
  JUKU_TOP_FDC_REPORT=/tmp/juku-top-stoppc-03eb-skip4.md \
  sync/juku_top_fdc_probe.sh
```

## Boundary

| VRAM writes | Result | cosim PC | HDL PC | VRAM | Notes |
| ---: | --- | ---: | ---: | --- | --- |
| 30,180 | PASS | `0x03FF` | `0x03FF` | match | Last sampled point before the old failure. |
| 30,182 | PASS | `0x03F5` | `0x03F5` | match | HDL now falls through the checksum branch and performs the blanking write sequence like cosim. |
| 30,520 | PASS | `0x031C` | `0x031C` | match | The reset-driven run reaches the fast cosim first-PIC window with matching visible state. |

## Relevant ROMBIOS Path

```text
0266: CALL $047C      ; clear VRAM
0269: MVI  A,$0E
026B: OUT  $07
026D: LXI  H,$D8C8
0270: SHLD $D450
0278: LXI  D,$000B
027B: CALL $03CA

03E2: LHLD $D450
03E5: INX  H
03E6: SHLD $D450
03E9: MVI  M,$F8
03EB: JNZ  $0402
03EE: LXI  B,$FFB0
03F1: DAD  B
03F2: MVI  A,$20
03F4: MOV  M,A
03F5: LXI  B,$0028
03F8: DAD  B
03F9: MOV  M,A
03FA: DAD  B
03FB: DAD  B
03FC: MOV  M,A
03FD: DAD  B
03FE: MOV  M,A
03FF: JMP  $0415
```

## Disposition

- The D6 mode-0 ROM-region condition is now `BA[15:14] == 2'b00`, matching the
  documented reset overlay and the cosim memory map.
- `juku_top_tb` keeps an opt-in `+tracechk=N` diagnostic. At level 2 it prints
  the ROMBIOS checksum helper's memory reads, including whether each access was
  decoded as ROM or RAM, so any future high-ROM checksum regression is local.
- The reset-driven Verilator run now reaches decoded PIC setup and, with
  `JUKU_TOP_FDC_FRAMEIRQ=200000`, the first decoded WD1793 status read. The
  remaining target is the uninterrupted ROMBIOS `TDD` FDC command/data path to
  EKDOS `A>`.
