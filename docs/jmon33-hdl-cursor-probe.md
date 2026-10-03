# jmon33 HDL cursor-boundary probe

Status: **JMON33 HDL CURSOR BUILD BLOCKED**

The `verilator` build exited with code `1`.
No simulation ran; this report does not establish the cursor boundary.

## Reproduce this run

Run from the repository root with the recorded settings:

```sh
JMON33_HDL_CURSOR_MAXVRAM=1200 \
JMON33_HDL_CURSOR_SIM=verilator \
JMON33_HDL_CURSOR_STOPHOOK=1 \
JMON33_HDL_CURSOR_FRAMEIRQ=200000 \
JMON33_HDL_CURSOR_TIMECAP=30000000000 \
JMON33_HDL_CURSOR_TRACEPROGRESS=100 \
JMON33_HDL_CURSOR_TIMEOUT=900 \
  sync/jmon33_hdl_cursor_probe.py
```

## Build errors

```text
%Error-UNSUPPORTED: hdl/devices.v:570:17: disable isn't underneath a begin with name: 'wait_for_expiry1'
%Error-UNSUPPORTED: hdl/devices.v:587:17: disable isn't underneath a begin with name: 'wait_for_expiry2'
%Error: Exiting due to 2 error(s)
```

## Boundary

The expected cosim framebuffer SHA256 is `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`.
Resolve the simulator build failure and rerun before treating the HDL
cursor oracle as verified for the current source.
