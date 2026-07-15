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
| `D6.15/A7 <-> D105.1` (net exists; driver/pull source NOT yet measured) | owner-continuity (partial) | `docs/d6-input-continuity.md` |
| D8.15 `/E` has a +5 V pull-up; `D6.12->D8.15` looks direct | photo (grain of salt) | owner note 2026-07-15 (unconfirmed by probe) |

## D30 / WAIT-READY

| Fact | Provenance | Source |
| --- | --- | --- |
| `D30.11 -> D105.2 / D13.4 / D11.20`; `D30.8 -> D29.7` | owner-continuity | `docs/d30-section-b-scan-chase.md` |

## D93 / D94 (FDC-era; FDC currently out of scope)

| Fact | Provenance | Source |
| --- | --- | --- |
| `D93.40 VDD_12V` on the +12 V rail | owner-continuity | `docs/d93-pin40-photo-chase.md` |
| `D94.15->D93.3`, `D94.2->D99.8/GND`, `D94.3->D93.4`, `D94.4->D93.2`; D94 D4/pin5 -> D93.1 socket; A0=BA0/A1=BA1/A2=IORD; A3=D104.7+pullup; A4=D101.7+pullup | owner-continuity + socket photo | `docs/d94-reconstruction-constraints.md` |
| `D106.7 Q3 -> D93.26 RCLK` | photo-closed | `docs/fdc-hardware-handoff.md` |

## NOT yet measured (open asks) — see `docs/next-bench-session-checklist.md`

- **D6 РТ4 re-read on pins 12 (D0) and 9 (D3)** with a corrected reader (avoid
  Arduino D13/LED pin for data; require the revision-2 disabled-output pull-up
  check and a byte-identical D2 control read). Sim shows only those two bits
  need inverting to boot from the physical table. The re-read discriminates a
  capture-path issue from an untraced consumer inversion; it does not presume
  either result. Cheaper cross-check: D6.12/D8.15 operating LEVELS during a ROM
  fetch (continuity is already done).
- D6.15/A7 driver/pull source.
- D30 `H` exact edge contact + pull-up value.
- Factory Вид В position-159 replacement landings at D56, D14's fifth landing /
  remaining replacement traces, and D11's registered four-landmark bridge
  endpoints. D56 position 150 is photo-closed as the D56.12-side wide-rail cut.
  The older D11
  pins-4–6 solder scar is now excluded as a different feature. D15's executed
  A2/A1 cut and D14's D32.4/GND-to-D14.1 position-159 link are photo-closed.
