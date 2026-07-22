# К555ИР16 primitive readiness

Status: **DATASHEET-EXACT ИР16 PRIMITIVE GUARDED / BOARD CONTROL SOURCES OPEN**

This guard corrects the shared D41/D42/D43 device primitive without
claiming the unresolved board timing rails. The device is the SN74LS295B-
equivalent four-bit register: it changes state on the falling clock edge,
loads when LD/SH is high, shifts right when LD/SH is low, and uses pin 8
as an active-high three-state output control.

## Command

```sh
sync/ir16_check.sh
```

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| К555ИР16 equivalence is pinned | PASS | Texas Instruments SDLS154, March 1988 revision; PDF SHA256 `3e7070d9a860483b9b332e980d81af85062bda260ed59568a5fd5c67f26c7ad6` |
| Clock transition is high-to-low | PASS | standalone HDL test rejects a rising-edge state change |
| LD/SH polarity is literal | PASS | LD/SH=1 loads A-D; LD/SH=0 shifts SER through QA toward QD |
| OC is active-high three-state control | PASS | OC=0 produces Z while sequential state continues |
| D41 output control is physically high | PASS | D41.8 is on P5V |
| D42/D43 output control remains one explicit rail | PASS | SHIFT_G joins D41.CLK to D42.OC/D43.OC; its remote source remains open |

## Physical consequence

- `SHIFT_G` is now correctly classified as the D42/D43 output-control rail;
  it is not a serializer clock or clock-inhibit input.
- D41 uses that same rail as its clock while its own OC pin is tied high.
- D42/D43 still receive their separate clock on `XTAL16M` and their mode
  input on `LOAD_VID`.
- The remote sources of `SHIFT_G` and `TIMING_TAG17` remain evidence gaps,
  so this correction does not claim a physical DRAM slot schedule or pixels.

Source document: [Texas Instruments SDLS154, March 1988 revision](https://www.syntax.com.tw/upload/pdf/IC-74LS295.pdf).
