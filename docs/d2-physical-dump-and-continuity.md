# D2 physical dump and local continuity

Status date: **2026-07-13**.

Status: **OWNER-MEASURED / HIGH-CONFIDENCE EVIDENCE / MODEL ADOPTION PENDING**

This report records continuity measurements made directly on the owner's
unpowered `.009` processor board and a repeated read of its socketed
`КР556РТ4` D2 PROM, programmed drawing `ДГШ5.106.037`. The owner considers
the measurements highly confident but allows for ordinary probing or pin-count
error; they should be treated as physical evidence to adopt and independently
cross-check, not as an infallible replacement for the board photographs.

## Physical identification correction

In the component-side close-up
`ref/photos/juku-pcb-2/PXL_20260710_200411500.jpg`, the horizontal row is
`РТ4`, `РЕ3`, `ИД7`, `ЛА3`. D2 is the socketed РТ4 mounted perpendicular
immediately below that row, not either of the two horizontal socketed PROMs.
The existing component-side D2 package registration therefore requires
correction before more photo-derived endpoints are accepted from it.

## Reader and capture

`tools/rt4_dumper/rt4_dumper.ino` was compiled for an Arduino Nano 3
(`ATmega328P`) and loaded through USBasp. The reader used the physical RT4
address order already recorded for D2:

| RT4 role | RT4 pins | Nano pins |
| --- | --- | --- |
| A0-A7 | 5, 6, 7, 4, 3, 2, 1, 15 | D2-D9 |
| D0-D3 | 12, 11, 10, 9 | D10-D13 |
| V1, V2 | 13, 14 | GND |
| GND, +5 V | 8, 16 | GND, Nano +5 V |

The breadboard reader used one 3 kOhm pull-up per output and a 100 nF Vishay
MKT film bypass capacitor. Two complete reads in one powered session agreed at
all 256 addresses; each address was sampled eight times and both reads reported
zero unstable addresses. Output pins 9-12 were checked unpowered and were not
shorted to one another. A separately power-cycled third raw serial capture is
still preferred, because the two original terminal streams were observed but
not preserved as unchanged capture files for `scripts/validate_rt4_dump.py`.

All four physical outputs agreed at every address. The observed active-low
asserted nibbles were:

```text
00: FFFFFFFFFFFFFFFF
10: FFFFFFFFFFFFFFFF
20: FFFFFFFFFFFFFFFF
30: FFFFFFFFFFFFFFFF
40: FFFFFFFFFFFFFFFF
50: FFFFFFFFFFFFFFFF
60: FFFFFFFFFFFFFFFF
70: FFFFFFFFFFFFFFFF
80: 00F000000F000000
90: 00F000000F000000
A0: 00F000000F000000
B0: 00F000000F000000
C0: 000000F0000000F0
D0: 0000000000000000
E0: FFFFFFFFFFFFFFFF
F0: FFFFFFFFFFFFFFFF
```

This is a credible preliminary recovery of `.037`, not yet a preservation-grade
binary artifact. The raw electrical table is the low-nibble complement of the
display above and remains the authoritative representation when captures are
preserved and validated.

## Confirmed continuity

The following direct-continuity results supersede conflicting assumptions from
the older drawing interpretation:

```text
D2.12  <-> D30.2
D2.12  -/-> D105.9

D30.2  <-> R6; other side of R6 <-> +5 V
D30.5  <-> R29 <-> D1.23 READY
D30.10 <-> D30.12 <-> R5; other side of R5 <-> +5 V
D30.13 <-> D105.11

D105.9  <-> D1.17 DBIN
D105.10 <-> pulled-up edge-bus net H <-> D13.13
D105.8  <-> D105.4 <-> D105.5
D105.6  <-> D5.4 DBIN
D105.12 <-> D105.13 <-> D5.26 MEMW_N

D13.12 <-> D6.11 <-> D6.12
```

D105 is the ЛА3 below D30 with D13 physically between them. The exact edge
connector contact and pull-up reference/value on `H` were difficult to access
and remain unresolved. No D6.11/D6.12 continuity to any D8 or D9 pin was found.

## Functional interpretation

The first D30 section is the CPU READY latch: D2's open-collector D0 output
overrides R6 and is sampled by D30, whose Q reaches CPU READY through R29. The
old `D2.12 -> D105.9` assignment is not present on this board.

D105.9/.10 and D105.4/.5 form two NAND stages, so the confirmed path implements:

```text
D5.DBIN = D1.DBIN AND H
```

`H` is an externally available pulled-up qualifier, also inverted by D13. The
joined `D13.12/D6.11/D6.12` net disproves the current model's assumption that
D6 pins 11 and 12 are independently routed `RAM_N` and `ROM_N` outputs on this
physical revision. D5.26 is `MEMW_N`; D105.12/.13 invert it onto D30.13.

## Adoption boundary

This evidence requires a dedicated connectivity-adoption change to reconcile
board JSON, structural HDL, generated KiCad artifacts, photo registration, and
the generated D2/D30/D105 reports together. Until that synchronized change is
made, generated documents describing `D2.12 -> D105.9`, a direct CPU-to-D5
DBIN connection, or independent D6.11/D6.12 nets are known stale against these
owner measurements.

