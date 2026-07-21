# Next bench / photo session — consolidated checklist

Status: **OWNER ACTION LIST** (hand-maintained; the auto-generated superset is
`docs/owner-measurement-shortlist.md`). Ordered by unlock value. **Before adding
or re-asking any measurement here, check `docs/owner-measured-facts.md` — it
indexes what has already been probed, so nothing gets re-requested.** Produced-board
photos are the ultimate truth; manual probes are truth at ~95%; the schematic
PDF is the prototype and may differ.

## Closed in the 2026-07-19 bench session

The revision-3 reader passed an empty-socket release test and known-D2 control
reads, then produced three identical D6 reads including a power cycle.
Continuity confirmed `pins 9,10,11,12 -> Nano A1,D2,D3,D4`. The former D6
artifact was an exact four-bit reversal; the corrected table now executes
directly. See `docs/rt4-dump-acquisition.md`.

D94 continuity then corrected the former pin/photo interpretation. R87/R88/R89
pull up D94.4/.3/.2; R8 2 kΩ pulls up D94.1; D94.2 reaches D99.9, D94.5 is NC,
D93.1 alone owns the open stub, and D94.13 is D105.3 qualified peripheral `/WR`.
Raw D5.27 reaches D7.10; D7.8 closes to D105.1/D6.15, and D13.4 closes to
D105.2. D104.7 remains separate (~84 kΩ from D94.13).

## Remaining P0 connectivity (batch in the same session)

2. **D94 `.092` live steering:** owner continuity on 2026-07-21 closes
   D94 D5-D7/pins 6, 7, and 9 plus D104.10 as NC, matching the exact-revision
   drawing. During port `1F` data-register
   transfers, also capture D101.7/A4, D94.1/D0, D93.4 `/RE`, and D93.2 `/WE`:
   A4 low must steer to D0 with both D93 strobes released, while A4 high restores
   the direction-appropriate D93 strobe
   (`docs/d94-reconstruction-constraints.md`).
3. **FDC support pins** (only if pursuing FDC later; not on the VJUGA path):
   D101 select
   pins (`docs/fdc-hardware-handoff.md`).
4. **Factory Вид В details:** D56.5->D34.9 and D56.12->D55.15/.18 are now
   owner-closed. D56's three physical callout locations are fixed as the
   separate left annulus plus D56.5/D56.12; identify the installed item-159
   material and the remaining auxiliary-annulus/adjacent-rail disposition.
   Position 150 is tubing, not a cut. Also continuity-test D14's registered fifth-landing conductor, three long traces, and
   right-row dogleg/D14.7; the available photos are exhausted there. At D11,
   continuity-test the registered four-landmark bridge and its remote endpoints;
   two-sided package-local projection has exhausted the solder photos, and the
   old pins-4–6 scar is a different feature. D15's A2/A1 cut and D14's
   local D32.4/GND-to-D14.1 link are photo-closed (`docs/factory-modification-disposition.md`).

## Programmable-parts corroboration (optional, Tier-3)

5. Independent re-reads of the D2/D6/D8/D94 PROMs, and dumps of the D15/D16
   EPROMs, only as corroboration of the validated captures
   (`docs/community-prom-media-request.md`).

The D6 output-order and D94 static-output blockers are closed; the highest-value
remaining live bench item is the D94 port-`1F` steering capture above.
