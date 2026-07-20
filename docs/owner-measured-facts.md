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
| `D30.11 -> D105.2 / D13.4 / D11.20`; `D30.8 -> D29.7` | owner-continuity | `docs/d30-section-b-scan-chase.md` |
| `X1.107B -BLOCK / H -> D13.13 -> D105.10`, pulled up by R1 2 kΩ to +5 V | native sheet + `.009` drawing/photo + owner-continuity | `docs/d105-h-boundary.md` |

## D93 / D94 (FDC-era; FDC currently out of scope)

| Fact | Provenance | Source |
| --- | --- | --- |
| `D93.40 VDD_12V` on the +12 V rail | owner-continuity | `docs/d93-pin40-photo-chase.md` |
| D94 A0/A1/A2 = BA0/BA1/IORD; A3 = D105.3 qualified `/WR`; A4 = D101.7. D94.15→D93.3; D94.2→D99.9+R89; D94.3→D93.4+R88; D94.4→D93.2+R87. D94.1 has only R8 2 kΩ to +5 V. D94.5 is NC; D93.1 alone owns the visible open stub. | owner-continuity + full-resolution visual recheck, 2026-07-19 | `docs/d94-reconstruction-constraints.md` |
| D5.27→D7.10 is raw `IOWR_N`. D7.8→D105.1→D6.15 is I/O-cycle-active high; D1.18/D5.3→D13.3 and D13.4→D105.2 supply write-active high; D105.3 drives qualified peripheral `/WR` including D94.13, D29.5, D10.2, D11.10, D26.36, and D27.36. | owner-continuity, 2026-07-19 | `kicad/juku.board.json` |
| `D106.7 Q3 -> D93.26 RCLK` | photo-closed | `docs/fdc-hardware-handoff.md` |

## NOT yet measured (open asks) — see `docs/next-bench-session-checklist.md`

- Factory Вид В callout conductors at the registered D56.12/D56.5 level,
  D14's photo-exhausted D14.2/.7 and registered fifth-landing conductor /
  remaining drawn traces, and D11's registered
  four-landmark bridge endpoints. Position 150 is tubing at solder locations,
  not a D56 cut instruction. The older D11
  pins-4–6 solder scar is now excluded as a different feature. D15's executed
  A2/A1 cut and D14's local D32.4/GND-to-D14.1 link are photo-closed.
