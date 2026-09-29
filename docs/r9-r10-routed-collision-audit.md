# R9/R10 routed placement collision

The exact .009 drawing and owner photo identify R10 as the outer-left and R9 as the inner-right 2 kΩ pull-ups beside D3. `ref/photos/juku-pcb-2/r9-r10-r15-r16-identity-review.json` records the source evidence and photo registration. The source PCB has both footprints at their photo-projected positions; the two routed variants still omit them.

## Temporary insertion trial

The unmodified R9/R10 footprint blocks from `kicad/juku.kicad_pcb` were inserted into a temporary copy of `kicad/juku_routed.kicad_pcb`. Neither routed board was changed by this trial. KiCad 10 error-only DRC without zone refill reported 176 violations and 61 unconnected items before insertion, versus 241 violations and 64 unconnected items after insertion. The 65 added violations comprise 22 shorts, 22 solder-mask bridges, 10 copper clearances, 6 hole clearances, 3 plated-hole/courtyard collisions, and 2 courtyard overlaps.

Those first unconnected-item counts are historical. The same two unmodified
source footprints were duplicated into a fresh temporary copy of the current
routed board with their pad nets remapped by name. Error-only, no-refill
`kicad-cli pcb drc` now reports **176 violations / 54 unconnected** before
insertion and **241 violations / 57 unconnected** after it. The current
delta is again 65 violations and three open items, with exactly the same
category breakdown above. The temporary board is
`/tmp/juku_r9_r10_current_trial.kicad_pcb`; neither tracked routed board
was changed. This reproduces the collision diagnosis against the present
power-route state, but is still a placement-only trial rather than a reroute.

The source footprint positions are R10.1 `INT6_RAW` `(211.204,93.578)` mm, R10.2 `P5V` `(211.204,83.418)`, R9.1 `INT7_RAW` `(214.319,94.881)`, and R9.2 `P5V` `(214.319,84.721)`. Representative trial conflicts:

| Pad | Existing routed item | Consequence |
| --- | --- | --- |
| R10.1 | IR7 B.Cu around `(211.5,93.5)`; FRAME_INT via `(212.125,94.0)`; P5V F.Cu diagonal | Short and hole clearance failures |
| R10.2 | WREQ_N B.Cu around `(210.5,83.25)`; D12 pins 5/6 nearby | Short and pad clearance failures |
| R9.1 | INTA F.Cu/B.Cu and via `(213.5,95.25)`; P12V F.Cu near `(214.25,94.75)` | Multiple direct shorts and hole clearance failures |
| R9.2 | INTA via `(214.5,84.5)` and IR7 B.Cu | Direct shorts |

The current temporary trial's 22 shorting-item DRC records group into
eight net pairs. Some records refer to the same via on two copper layers,
so these are report counts rather than 22 independent places to move:

| Conflicting nets | DRC records | Local priority |
| --- | ---: | --- |
| `INT7_RAW` / `INTA` | 5 | R9.1 and INTA tracks/via near `(213.5,95.25)` |
| `P5V` / `INTA` | 4 | R9.2 and INTA via near `(214.5,84.5)` |
| `INT7_RAW` / `P12V` | 3 | R9.1 and +12 V front track near `(214.25,94.75)` |
| `INT6_RAW` / `FRAME_INT` | 3 | R10.1 and FRAME_INT via near `(212.125,94.0)` |
| `INT6_RAW` / `IR7` | 2 | R10.1 and IR7 back tracks near `(211.5,94.0)` |
| `P5V` / `IR7` | 2 | R9.2 and IR7 back tracks near `(215,85)` |
| `P5V` / `WREQ_N` | 2 | R10.2 and WREQ_N back tracks near `(210.5,83.25)` |
| `INT6_RAW` / `P5V` | 1 | R10.1 and +5 V front diagonal |

This list comes from the fresh temporary DRC JSON, with each record
requiring local copper inspection before any track is removed.

## Cause and correction boundary

The source PCB places D12 at `(224.535,67.630)` mm, rotated 180°, directly above D3, matching the exact .009 assembly and owner photo reviewed in `ref/photos/juku-pcb-2/d12-d3-local-placement.json`. Both routed variants still place D12 at `(202.495,77.090)` mm, rotation 0°, left of D3. That stale D12 placement and its local copper occupy the R9/R10 corridor. This is a source-to-routed placement divergence, not evidence that the photographed R9/R10 body locations are wrong.

The full `kicad/report_board_placement_parity.py` comparison finds no other moved or rotated footprint and no other missing source reference in either routed board: D12 and R9/R10 are the complete source-to-routed footprint placement difference (`docs/board-placement-parity.md`).

A read-only DRC of the source PCB with R9/R10 present found no R9/R10 electrical shorts or copper/hole clearances. It did report one D3/R9 courtyard overlap; that mechanical outline still needs review. The source PCB has many unrelated DRC holds, so this does not release the layout.

Native owner crop `(1000,650)-(1600,1350)` of
`ref/photos/juku-pcb-2/PXL_20260710_200418174.jpg` shows the fitted inner
R9 axial body beside D3 with a visible body-to-package gap; its bent leads
also clear the D3 package in this view. That observation rules out an obvious
body collision on the photographed board, but does not validate the generic
replica footprint's courtyard or a substitute resistor's diameter. Review
the fitted body envelope and lead bends before reducing or waiving the
source-board D3/R9 courtyard finding. The routed-board shorts above remain
actual copper collisions and are not explained away by this mechanical view.

The source KiCad geometry makes the warning precise. D3's F.Fab body starts
at x `217.204` mm and R9's F.Fab body ends at x `215.619` mm, leaving
`1.585` mm between drawn bodies. Their F.Courtyard envelopes instead meet
at x `215.544` and `215.844` mm, an overlap of `0.300` mm. Thus the
reported source violation is an assembly-envelope overlap, not a drawn-body
intersection. The photo supports physical body clearance on the original;
the replica's selected parts and insertion method still control the
courtyard disposition.

Refresh D12 to the source/owner position and redesign the displaced D12, INTA, IR7, P12V, FRAME_INT, and WREQ_N copper around the two resistors. Keep R9/R10 at their registered source locations unless stronger owner evidence changes them. Then connect R10.1 to D3.1, R9.1 to D3.13, both upper pads to +5 V, and compare DRC to the routed baseline. Owner continuity of those four physical joints remains pending independently of the replica layout.

## Whole-board refresh trial

`kicad/refresh_routed_from_source.py --output /tmp/juku_d12_refresh_trial.kicad_pcb` was run on a temporary copy only. Its whole-net endpoint rule quarantined seven nets and 2,886 copper items, including 1,382 GND and 992 P5V items, because the added resistors and moved D12 change endpoint sets. The candidate DRC reported 277 violations and 465 unconnected items, versus 176 and 61 on the current routed baseline. This candidate is rejected: it would discard large unrelated power routes. A targeted local relocation/reroute is required; no routed-board D12/R9/R10 mutation was made by either trial.

The `--allow-additive-renames` option retained the added INT6_RAW/INT7_RAW endpoints but still quarantined GND and P5V because D12's power pads moved, leaving 463 opens. An exploratory `--allow-drc-salvage` refresh retained all existing copper and was then passed through `kicad/salvage_routed_copper.py` on a temporary board. DRC removed 55 migrated track/via items in one round; the resulting board has no electrical shorts, copper clearances, track crossings, or hole-clearance blockers. Error-only DRC reports 173 non-electrical violations and 93 unconnected items, compared with 176 and 61 on the current routed board. This is a reproducible *rerouting starting point*, not a completed route: the 32 additional opens need copper repair, and both routed boards remain unchanged.

A bounded exploratory custom FreeRouting run exported the salvaged board to Specctra DSN and began autorouting 144 items (`-mp 3 -mt 10`, JDK 25). It produced no `.ses` before a 180-second timeout, so there is no routed result to import or assess. This timeout is a limit of that trial, not evidence that the opens are impossible to route. Continue with a longer controlled route or targeted local routing, then require KiCad DRC and source-to-routed placement parity before promotion.
