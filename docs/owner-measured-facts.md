# Owner-measured facts — single index (check this BEFORE asking to re-measure)

Purpose: one place that lists what the owner has already physically measured, so
nobody re-asks for a measurement that exists. This is an **index into the
authoritative docs** (each row cites its source); it does not restate results in
a way that could drift. Provenance tags: `probe` = multimeter/continuity,
`photo` = read from board photos (treat as ~90% until probed), `owner-continuity`
= chip-removed / powered-off continuity session.

**Convention:** before adding an "owner-measurement" ask anywhere (PLAN.md,
shortlists, agent prompts), grep this file and the cited docs first. When a new
measurement lands, add a row here.

## D6 (К556РТ4 memory-map decode)

| Fact | Provenance | Source |
| --- | --- | --- |
| `D6.12 ROM_N -> D8.15 E_N` (direct); `D6.11 -/-> D8.15`; D6.11/D6.12 socket pads separate | owner-continuity (chip-removed) | `docs/d6-input-continuity.md` |
| `D6.11 RAM_N -> D2.15 (A7 / -WREQ)`, and `-> D92.5` + `R12.2` (R12 other side +5 V pull-up) | owner-continuity | `docs/d6-input-continuity.md` |
| `D6.9 -> D13.1`, `D13.2 -> D37.4`, `D37.6 -> D58.9` (RAM-output-enable chain) | owner-continuity | `docs/d6-input-continuity.md` |
| `D13.12 -> D6.14 V2`; `D6.13 V1 <-> D6.14 V2` (bottom-layer copper) | owner-continuity + visual | `docs/d6-input-continuity.md` |
| `D6.1/A6 <- D3.4 <- /PC1`; `D6.2/A5 <- D3.6 <- /PC0` | owner-continuity | `docs/d6-physical-decode.md` |
| `D7.8 -> D105.1 -> D6.15/A7` (`IO_CYCLE_H`) | owner-continuity, 2026-07-19 | `docs/d6-input-continuity.md` |
| D8.15 `/E` has a +5 V pull-up; `D6.12->D8.15` looks direct | photo (grain of salt) | owner note 2026-07-15 (unconfirmed by probe) |
| Reader wiring `D6 pins 9,10,11,12 -> Nano A1,D2,D3,D4`; three revision-3 D6 reads including a power cycle agree, and a D2 control agrees with the prior D2 artifact | owner-continuity + repeated capture | `docs/rt4-dump-acquisition.md` |

## D30 / WAIT-READY

| Fact | Provenance | Source |
| --- | --- | --- |
| `D30.1 /CLR1 <-> D30.4 /PRE1 <-> D30.10 /PRE2 <-> D30.12 D2 <-> R5.2`; `R5.1 -> +5 V`; the common conductor is driven by `D38.8` active-low STB | exact `.009` sheet + owner-continuity, 2026-07-22 | `docs/d30-section-b-scan-chase.md`; `docs/d2-physical-dump-and-continuity.md` |
| `D30.11 -> D105.2 / D13.4 / D11.20`; `D30.8 -> D29.7` | owner-continuity | `docs/d30-section-b-scan-chase.md` |
| `X1.107B -BLOCK / H -> D13.13 -> D105.10`, pulled up by R1 2 kΩ to +5 V | native sheet + `.009` drawing/photo + owner-continuity | `docs/d105-h-boundary.md` |

## D93 / D94 (FDC-era; FDC currently out of scope)

| Fact | Provenance | Source |
| --- | --- | --- |
| `D93.40 VDD_12V` on the +12 V rail | owner-continuity | `docs/d93-pin40-photo-chase.md` |
| D94 A0/A1/A2 = BA0/BA1/IORD; A3 = D105.3 qualified `/WR`; A4 = D101.7. D94.15→D93.3; D94.2→D99.9+R89; D94.3→D93.4+R88; D94.4→D93.2+R87. D94.1 has only R8 2 kΩ to +5 V. D94.5 is NC; D93.1 alone owns the visible open stub. | owner-continuity + full-resolution visual recheck, 2026-07-19 | `docs/d94-reconstruction-constraints.md` |
| D5.27→D7.10 is raw `IOWR_N`. D7.8→D105.1→D6.15 is I/O-cycle-active high; D1.18/D5.3→D13.3 and D13.4→D105.2 supply write-active high; D105.3 drives qualified peripheral `/WR` including D94.13, D29.5, D10.2, D11.10, D26.36, and D27.36. | owner-continuity, 2026-07-19 | `kicad/juku.board.json` |
| `D106.7 Q3 -> D93.26 RCLK` | photo-closed | `docs/fdc-hardware-handoff.md` |
| `D93.38 DRQ -> D28.11 -> R94.1`; R94 is `10к`, immediately above D28, and R94.2 -> +5 V. The video cable can obscure its body; the photographed 220-ohm body near D98 is not R94 and remains unassigned. | owner-continuity + owner visual identification, 2026-07-20 | `ref/schematics/fdc-irq-conditioner-map.md`; `ref/photos/juku-pcb-2/r94-photo-exhaustion.json` |
| With D93 removed, `D93.19 MR_N -> D13.8` and the outer-bus contact physically at the rightmost position of the middle row (board viewed from top). `D13.9 -> D1.12 RESET`; D13 section 9->8 therefore inverts active-high RESET for D93. Exact X1 contact code remains unresolved. | owner-continuity, 2026-07-20 | `ref/schematics/fdc-controller-static-map.md` |
| D94 outputs D5-D7/pins 6, 7, and 9 are NC; D104 receiver output pin 10 is also NC. Exact-revision `.009 E3` drawing review agrees with direct continuity. | owner-continuity + exact-revision drawing, 2026-07-21 | `docs/d94-reconstruction-constraints.md`; `docs/serial-handoff.md` |

## D54-D57 / D56 video timing

| Fact | Provenance | Source |
| --- | --- | --- |
| `D54.17 H.SYNC DSL -> D56.10/B2`; `D55.17 VERT SYNC DSL -> D56.2/B`; the former D57.17-to-both-trigger interpretation is false. | owner-continuity + exact-revision `.009 E3` sheet 2, 2026-07-21 | `docs/memory-timing-boundary.md`; `ref/photos/dgsh5-109-009-e3/` |
| `D56.12/Q2_N -> D55.15/CLK1 + D55.18/CLK2` on conductor 16; it is distinct from the DRAM write rail also marked 16. | owner-continuity + exact-revision `.009 E3` sheet 2, 2026-07-21 | `docs/memory-timing-boundary.md` |
| `D56.5/Q2 -> D34.9` as drawn. | owner-continuity + exact-revision `.009 E3` sheet 2, 2026-07-21 | `docs/memory-timing-boundary.md` |

## D40/D59/D92/D95 1 MHz slot clock

| Fact | Provenance | Source |
| --- | --- | --- |
| `D40.11 -> D59.5 -> D92.2 -> D95.5/.6`; D95.5 and D95.6 are externally tied КП12 inputs, not an internal IC short. The `.009` drawing independently labels D40.11 and the D95 arrival as 1 MHz and visibly ties D92.2/.3. | owner-continuity + exact `.009` sheets 2/3, 2026-07-22 | `docs/d40-d59-d92-d95-1mhz-route.md`; `ref/schematics/fdc-clock-mux-map.md` |
| `D59.5 -> D51.15 /G`; inverted `D59.6 -> D48.15 /G`. The factory drawing extends the paired enable islands to D50.15 and D49.15 through E14/E13. | owner-continuity + exact `.009` sheet 2, 2026-07-22 | `docs/d40-d59-d92-d95-1mhz-route.md` |
| Tentative `D96.6` membership is not accepted: sheet 3 makes it the active `/Q1` output fed back only to D96.2, so a real join to active D40.11 would be a conflict. | unconfirmed continuity-beeper observation + exact `.009` sheet 3 | `docs/d40-d59-d92-d95-1mhz-route.md`; `ref/schematics/fdc-read-clock-toggle-map.md` |

## NOT yet measured (open asks) — see `docs/next-bench-session-checklist.md`

- Factory Вид В item-159 material and auxiliary-annulus/adjacent-rail disposition at the registered D56.12/D56.5 level (the package-pad functional nets themselves are closed),
  D14's photo-exhausted D14.2/.7 and registered fifth-landing conductor /
  remaining drawn traces, and D11's registered
  four-landmark bridge endpoints. Position 150 is tubing at solder locations,
  not a D56 cut instruction. The older D11
  pins-4–6 solder scar is now excluded as a different feature. D15's executed
  A2/A1 cut and D14's local D32.4/GND-to-D14.1 link are photo-closed.
