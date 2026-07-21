# D96 FDC read-clock readiness

Status: **SECTION 1 DIVIDE GUARDED / RESTART PHASE UNDEFINED / SECTION 2 SET-ONLY**

Recovered `.009` Э3 sheet 3 closes D96 section 1 as the read-clock
divide-by-two toggle: WREQ_N drives both active-low asynchronous controls,
/Q feeds D, the D28/R85 recovered-clock node clocks the flip-flop, and Q drives
D93 RCLK. Its connectivity and phase-independent divide-by-two behavior after
WREQ release are source-closed.

The separately drawn section 2 is not unused. D28.10/.12 and R95 drive the
same node into D96.10 `/PRE2` and D96.12 `D2`; D96.11 `CLK2` and
D96.9 `Q2` leave through distinct unresolved sheet-1 continuations,
D96.8 `/Q2` reaches an isolated test landing, and sheet 3 leaves D96.13
`/CLR2` unconnected.

## Command

```sh
sync/d96_check.sh
```

## Result

```text
D96-RCLK: PASS both-async state exposed; /Q feedback divides after release
D96-IRQ-CONSTRAINT: PASS shared PRE_N/D only sets Q; CLR_N is sole clear
```

## Section-1 asynchronous-control consequence

WREQ_N drives both `/CLR1` and `/PRE1`. The primary truth table therefore
requires Q1=1 and /Q1=1 while WREQ_N is low; assigning "clear wins" is not a
valid device model. Simultaneously releasing the two controls does not define
a deterministic restart phase. Once a recovered-clock edge resolves the state,
/Q feedback produces the required divide-by-two sequence, but its initial phase
must not be claimed from the local drawing.

## Section-2 logic consequence

The TI SN74LS74A truth table makes the recovered wiring set-only when
`/CLR2` is inactive:

| Shared `FDC_IRQ_CONDITIONED_N` | Event | Q2 result |
| ---: | --- | ---: |
| 0 | asynchronous `/PRE2` assertion | 1 |
| 1 | rising `CLK2` samples D2=1 | 1 |
| 1 | no rising edge | holds prior state |

No documented section-2 input can drive Q2 from 1 back to 0. Only an asserted
`/CLR2` can do that, yet pin13 is the sheet-omitted no-connect. A floating
LS-TTL input may tend high electrically, but it is not a guaranteed reset or a
safe substitute for a designed logic source. Therefore the exact drawing is
preserved, but the section must not be described as a complete conditioner.

## Evidence boundary

This guard proves the both-asserted WREQ state and phase-independent
divide-by-two behavior after release; it deliberately does not claim a
deterministic WREQ reset/restart phase.
It does not replace bench measurement of D28/R85 open-collector rise time,
duty cycle, D96 setup/hold margin, or separator lock over both 4/8 MHz modes.
Capture WREQ_N at pins1/4 with Q1/pin5 and /Q1/pin6 to establish the actual
post-write phase and recovery margin.
For section 2, continuity-check pins9, 11, and 13 and capture pins8-13 during
DRQ, INTRQ, and interrupt acknowledgement. An observed Q2 falling edge requires
a real clear mechanism absent from the recovered local drawing.
Exact connectivity is guarded separately by
`kicad/check_fdc_read_clock_toggle.py` and documented in
`ref/schematics/fdc-read-clock-toggle-map.md`. The primary device contract
is pinned in `ref/datasheets/k555tm2-pinout.txt`.
