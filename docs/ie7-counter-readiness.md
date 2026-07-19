# К555ИЕ7 / 74LS193 counter readiness

Status: **FULL DIGITAL DEVICE CONTRACT GUARDED**

The shared `ie7_ctr` primitive models the standard К555ИЕ7 / SN74LS193
package used at video-address counters D44-D47 and identified at FDC data-
separator position D106.

## Primary specification

Texas Instruments, *SN54192, SN54193, SN54LS192, SN54LS193, SN74192,
SN74193, SN74LS192, SN74LS193 — Synchronous 4-Bit Up/Down Counters (Dual
Clock With Clear)*, SDLS074, December 1972, revised March 1988:

<https://www.ti.com/lit/ds/symlink/sn74ls193.pdf>

The guarded contract is:

- active-high asynchronous clear, independent of load and clocks;
- active-low asynchronous parallel load, including data changes while held low;
- rising-edge up/down counting only while the opposite clock is high;
- modulo-16 wrap in both directions;
- active-low carry and borrow pulses equal to the low clock phase at terminal
  counts `F` and `0`;
- two-package carry and borrow cascade without an early or late digit change.

## Command

```sh
sync/ie7_check.sh
```

## Result

```text
IE7-CTR: PASS async-clear/load up/down terminal-pulses cascade
```

## Evidence boundary

This closes the standard package's digital behavior. Recovered `.009` Э3
sheet 3 independently closes the board wiring around D106: D95.9 clocks DOWN,
R78 pulls UP and all four preset inputs high, D97.4/D93.27 RAW READ drives
/LOAD, CLR is grounded, Q3 drives D28.9, and Q0-Q2 plus /CO and /BO are explicit
no-connects. The downstream D28/D96 analog timing and edge quality remain
board bring-up boundaries.
