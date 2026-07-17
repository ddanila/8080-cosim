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

This closes the standard package's digital behavior. It does **not** promote
unseen Juku PCB continuity around D106: only D106.7 Q3 to D93.26 RCLK is
photo-closed. D106 load, clear, clocks, presets, the other outputs, and their
remote destinations remain owner-continuity boundaries.
