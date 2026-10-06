# D96 FDC read-clock readiness

Status: **SECTION 1 DIVIDE GUARDED / RESTART PHASE UNDEFINED / SECTION 2 CLEAR SOURCE OPEN**

Recovered `.009` Э3 sheet 3 closes D96 section 1 as the read-clock
divide-by-two toggle: WREQ_N drives both active-low asynchronous controls,
/Q feeds D, the D28/R85 recovered-clock node clocks the flip-flop, and Q drives
D93 RCLK. Source connectivity is guarded separately; the simulations below
check modeled divide-by-two behavior after WREQ release.

The separately drawn section 2 is not unused. D28.10/.12 and R95 drive the
same node into D96.10 `/PRE2` and D96.12 `D2`. D96.11 `CLK2` is
source-joined to D94.2/D99.9/R89.1; D96.9 `Q2` drives the D101
address island with R92/R99. See [the clock-source review](d96-clock2-source-review.md)
for the conditional owner-photo DRQ conflict. Neither island is established
by this device simulation alone.
D96.8 `/Q2` reaches an isolated test landing. The exact sheet-3 detail
joins D96.13 `/CLR2` to D99.10 `B2`; their sheet-1 source is unread.

## Command

Run from the repository root with Bash, Icarus Verilog (`iverilog` and
`vvp`), `sha256sum` and `grep`. Simulator files are temporary; the
command replaces this report, or the file selected by `D96_REPORT`.

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

The conditioned node cannot drive Q2 from 1 back to 0. An asserted `/CLR2`
can do that, and pin13 is source-joined to D99.10 and a sheet-1 continuation.
The remote source and waveform are still unknown. The section must not be
described as a complete conditioner until they are verified.

## Evidence boundary

This guard checks the both-asserted WREQ state and modeled divide-by-two
behavior after release. The test uses the model's retained high/high state;
it does not sweep physical restart phases or establish a deterministic
WREQ reset/restart phase.
It does not replace bench measurement of D28/R85 open-collector rise time,
duty cycle, D96 setup/hold margin, or separator lock over both 4/8 MHz modes.
Capture WREQ_N at pins1/4 with Q1/pin5 and /Q1/pin6 to establish the actual
post-write phase and recovery margin.
For section 2, continuity-check D96.13 to D99.10, locate their shared sheet-1
source, verify the registered pin9/11 islands, and capture pins8-13 during DRQ, INTRQ, and interrupt
acknowledgement. An observed Q2 falling edge should align with /CLR2 assertion.
Exact connectivity is guarded separately by
`kicad/check_fdc_read_clock_toggle.py` and documented in
`ref/schematics/fdc-read-clock-toggle-map.md`. The primary device contract
is pinned in `ref/datasheets/k555tm2-pinout.txt`.
