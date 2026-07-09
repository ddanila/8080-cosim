# juku_top post-30,180 divergence

Status: **RESET-RUN DIVERGENCE PINNED TO DISPLAY-TEST CHECKSUM PATH**

The reset-driven `juku_top` Verilator run remains byte-aligned with cosim through
30,180 framebuffer writes on the vendored `JUKU1.CPM` `TDD` path. The first
sampled control-flow divergence is immediately after that, in the ROMBIOS
display-test helper around `0x03CA`.

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
  JUKU_TOP_FDC_STOPFDC=0 \
  JUKU_TOP_FDC_REPORT=/tmp/juku-top-stoppc-03eb-skip4.md \
  sync/juku_top_fdc_probe.sh
```

## Boundary

| VRAM writes | Result | cosim PC | HDL PC | VRAM | Notes |
| ---: | --- | ---: | ---: | --- | --- |
| 30,180 | PASS | `0x03FF` | `0x03FF` | match | Last clean sampled point. |
| 30,180 / fifth `0x03EB` | state FAIL | expected `B=0x3B/ZF=1` | `B=0x00/ZF=0` | before next write | Direct `STOPPC=03EB`, `STOPPC_SKIP=4` stop: branch condition is already wrong before the 30,181st framebuffer write. |
| 30,181 | write-boundary FAIL | `0x03EB` | `0x03EB` | match | Same bad state is visible at the following `MVI M,$F8` write boundary, so the next `JNZ $0402` goes a different way. |
| 30,182 | control-flow FAIL | `0x03F5` | `0x03EB` | mismatch | HDL repeats the `0x03EB` path instead of advancing through the blanking writes at `0x03F4`/`0x03F9`. |
| 30,185 | FAIL | `0x03FF` | `0x0244` | mismatch | HDL has branched back into the early `0x0242` RAM-fill loop. |

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

- The full 70,000-write FDC mismatch is downstream of this display-test branch,
  not an FDC/PIC decode failure.
- The next useful fix target is the `CALL $0426` / `CMP B` result feeding
  `0x03EB`: in cosim the zero flag is set and execution falls through to the
  `0x03F4` blanking writes; in reset-driven HDL `B` is already wrong at the
  fifth `0x03EB` visit (`A=0x3B`, `B=0x00`, `ZF=0`, `vram=30180`), so ROMBIOS
  takes the `0x0402` path and soon returns to the early RAM-fill loop.
- The top-level state dump now reports `xchg_dh` and maps vm80a DE/HL latches
  dynamically, because this core swaps the D/E and H/L selectors after `XCHG`.
