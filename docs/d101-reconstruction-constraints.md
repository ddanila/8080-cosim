# D101 first-half reconstruction constraints

Status: **D101 FIRST HALF LOGIC-CONSTRAINED / FIVE SOURCE JOINS MEASUREMENT-GATED**

D101 is the target-board К555КП12 / SN74LS253 dual 4:1 multiplexer.
Its Q1 write-precompensation half is source-closed. This report narrows
the separate Q0 half that drives D94 A4. The drawing closes /OE0
to D26 PA6/IMDRG and joins D96.9 Q2 to all four section-A data inputs. Physical
continuity of IMDRG, D96.9, and three data-input branches remains unmeasured.

## Command

Run from the repository root. The report requires standard-library Python 3;
the simulation requires Bash and Icarus Verilog (`iverilog` and `vvp`).
The generator replaces this report and exits 1 if any listed check fails.

```sh
python3 scripts/report_d101_reconstruction_constraints.py
sync/kp12_check.sh
```

The generator checks the pinned PDF/image hashes, JSON pin/net/value
invariants, selected pinout and HDL/test text markers, and eight D94
register-3 image rows. It does not execute the mux simulation or inspect
physical components. Run `sync/kp12_check.sh` separately for simulation.

CLOSED below means represented by source or owner evidence; it does not
certify every physical joint. SOURCE-CLOSED / MEASURE flags the listed
D101 pins awaiting direct continuity, with D96.9 checked separately.

## Evidence checks

| Check | Result |
| --- | --- |
| TI SN74LS253 PDF and validated D94 image hashes match | PASS |
| D101 all-pin JSON mapping matches the expected source/owner model | PASS |
| D101 section-A JSON net contains the expected seven endpoints | PASS |
| IMDRG, Q0, and EARLY/LATE JSON nets match the expected endpoints | PASS |
| R92/R99 modeled values match 1.3 kΩ / 4.7 kΩ | PASS |
| Local pinout interpretation separates source and physical D101 evidence | PASS |
| HDL/test contains selected select-order and disable markers | PASS |
| Physical D94 register-3 rows obey the exact A4 steering contract | PASS |

## Exact pin disposition

The TI truth table calls physical pin 2 select `B` and pin 14 select
`A`. Repository signal names `A1`/`A0` preserve the same ordering.

| Pin | Device role | Board net | State |
| ---: | --- | --- | --- |
| 1 | /OE0 | `FDC_IMDRG` | SOURCE-CLOSED / MEASURE |
| 2 | select B / EARLY | `FDC_EARLY_SEL` | CLOSED |
| 3 | D03 | `D101_D02_R92_R99` | SOURCE-CLOSED / MEASURE |
| 4 | D02 | `D101_D02_R92_R99` | CLOSED |
| 5 | D01 | `D101_D02_R92_R99` | SOURCE-CLOSED / MEASURE |
| 6 | D00 | `D101_D02_R92_R99` | SOURCE-CLOSED / MEASURE |
| 7 | Q0 / D94 A4 | `D94_A4_D101_Q0` | CLOSED |
| 8 | GND | `GND` | CLOSED |
| 9 | Q1 / precomp output | `FDC_PRECOMP_WRDATA` | CLOSED |
| 10 | D10 / tap 1 | `PRECOMP_TAP_1` | CLOSED |
| 11 | D11 / tap 2 | `PRECOMP_TAP_2` | CLOSED |
| 12 | D12 / tap 3 | `PRECOMP_TAP_3` | CLOSED |
| 13 | D13 / GND | `GND` | CLOSED |
| 14 | select A / LATE | `FDC_LATE_SEL` | CLOSED |
| 15 | /OE1 / GND | `GND` | CLOSED |
| 16 | +5 V | `P5V` | CLOSED |

## Datasheet-exact Q0 selection

When `/OE0` is high, Q0 is high impedance. When `/OE0` is low,
Q0 equals the selected input; there is no inversion.

| EARLY / B | LATE / A | Selected input | Physical pin | Board state |
| ---: | ---: | --- | ---: | --- |
| 0 | 0 | D00 | 6 | source-joined to D02/R92/R99; physical check pending |
| 0 | 1 | D01 | 5 | source-joined to D02/R92/R99; physical check pending |
| 1 | 0 | D02 | 4 | owner-visible R92/R99 ladder from D95.14 density-control conductor |
| 1 | 1 | D03 | 3 | source-joined to D02/R92/R99; physical check pending |

R92=1.3 kΩ joins the D95.14 density-control conductor to D101.4;
R99=4.7 kΩ returns D101.4 to ground. With an ideal 5 V source high,
the passive divider is nominally 3.92 V. This is a probe prediction,
not a measured threshold or proof of the other three physical joins.
If those joins exist on the board, Q0's selected data is the same
for every EARLY/LATE combination whenever IMDRG enables section A.

## Physical D94 register-3 constraint

The table below reads the validated `.092` image directly. `yes` means
the open-collector output is programmed active (raw bit zero). A1:A0
is fixed at `11`, the only register address where A4 changes D0/D2/D3.

| A4 / Q0 | A3 / qualified /WR | A2 / IORD | Address | Raw | D0 active | /RE active | /WE active |
| ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 0 | 0 | 0 | `03` | `FE` | yes | no | no |
| 0 | 0 | 1 | `07` | `FC` | yes | no | no |
| 0 | 1 | 0 | `0B` | `FC` | yes | no | no |
| 0 | 1 | 1 | `0F` | `FE` | yes | no | no |
| 1 | 0 | 0 | `13` | `FF` | no | no | no |
| 1 | 0 | 1 | `17` | `F5` | no | no | yes |
| 1 | 1 | 0 | `1B` | `F9` | no | yes | no |
| 1 | 1 | 1 | `1F` | `FF` | no | no | no |

Therefore A4 low always asserts D94 D0 and releases both D93 strobes
at register 3. A4 high always releases D0 and restores the mutually
exclusive direction-appropriate `/RE` or `/WE` strobe. No other FDC
register address depends on A4.

## D0-to-IMDRG isolation test

D94.1/D0 and D101.1 `/OE0` (D26 PA6/IMDRG) are separate in the
source model; the drawing does **not** join those pins. Owner continuity found only R8
on D94.1; further chip-removed checks must establish the hidden-load
disposition within their measured scope. Do not merge D0 and IMDRG
from functional resemblance. Any measured join requires source/board
reconciliation before runtime inference: it would also connect D94's
open-collector output to D26 PA6.

## Minimal closure sequence

1. Remove D94 and D101; measure D94.1 to D101.1 directly, then repeat
   D94.1 against the nearby D99/D101 support pins.
2. With D96 and D101 removed, confirm D101.1-D26.38 IMDRG continuity and
   check D96.9 and D101.3/.5/.6 each against D101.4/R92.1/R99.2. Preserve
   pin 4 as the already-closed R92/R99 ladder.
3. Only after continuity closure, capture EARLY, LATE, `/OE0`, Q0/A4,
   D94 D0, `/RE`, and `/WE` during port `1F` transfers.
4. Promote copper only when the direct measurements agree; otherwise
   split any disproved source joins or document a redesign.

## Reconstruction boundary

Derived constraints: mux select order and the eight D94 register-3 rows.
The canonical model records the source and owner connections above.
Runnable HDL omits the D97/D102/D101 precompensation chain and holds
D94 A4 high; these Q0 constraints describe the structural/source path.
Still physical: D101.1-D26.38 IMDRG continuity, input ties at
D96.9 and D101.3/.5/.6, the D94 D0 hidden-load disposition, and
powered analog behavior.
