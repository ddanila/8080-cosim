# К555ИЕ10 / 74LS161 counter readiness

Status: **PACKAGE AND TRACED D103 /13 LOOP GUARDED**

The `ie10_ctr` primitive models the К555ИЕ10 / SN74LS161A-class package at
D103. The structural top now uses the source-proved `0011` preset instead of
the former placeholder zero, so D103 RCO through inverter D33 back to D103
`/LOAD` executes the traced modulo-13 circuit.

## Primary specification

Texas Instruments, *SN54160 through SN54163, SN54LS160A through SN54LS163A,
SN74LS160A through SN74LS163A — Synchronous 4-Bit Counters*, SDLS060,
October 1976, revised March 1988:

<https://www.ti.com/lit/ds/symlink/sn74ls161a.pdf>

The guard covers:

- active-low direct/asynchronous clear;
- active-low synchronous parallel load with priority over counting;
- independent ENP and ENT count gating;
- all sixteen binary states and wrap;
- combinational ENT-qualified terminal RCO; and
- the board-proved D103 RCO -> D33 inverter -> `/LOAD` loop, which repeats
  `3..F` every 13 input clocks and drives Q3's labeled 1.23 MHz rail from 16 MHz.

## Command

```sh
sync/ie10_check.sh
```

## Result

```text
IE10-CTR: PASS direct-clear sync-load enables RCO traced-div13
```

## Evidence boundary

This closes D103's standard digital behavior and the already traced local /13
feedback topology. The native sheet still does not visibly close the upstream
OSC-to-XTAL16M bundle, so `XTAL16M` remains a physical continuity boundary; the
runnable raster continues to use its explicit simulation dot-clock input.
