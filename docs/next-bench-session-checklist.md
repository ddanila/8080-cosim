# Next bench / photo session — consolidated checklist

Status: **OWNER ACTION LIST** (hand-maintained; the auto-generated superset is
`docs/owner-measurement-shortlist.md`). Ordered by unlock value. **Before adding
or re-asking any measurement here, check `docs/owner-measured-facts.md` — it
indexes what has already been probed, so nothing gets re-requested.** Produced-board
photos are the ultimate truth; manual probes are truth at ~95%; the schematic
PDF is the prototype and may differ.

## Highest value — unblocks the digital twin + VJUGA at once

1. **D6 corrected re-read / output polarity (unblocks D6 firmware adoption AND
   VJUGA Phase 2).** Use reader revision 2 in `tools/rt4_dumper`: D3/pin 9 moves
   from Nano D13 to A0, /CE pin 14 moves to A1, and every capture must pass the
   disabled-output `F` pull-up check. Re-read known D2 first, then D6 three times
   including a power cycle; compare raw bytes as described in
   `docs/rt4-dump-acquisition.md`. This discriminates the capture path from the
   already measured direct consumer conductors without assuming either answer.
   - *Cheaper operating-level cross-check:* at the reset fetch (address `0000`, must read
     ROM), is the D8/РЕ3 enable pin (`D6.12 -> D8.15`) physically **low** (ROM
     enabled) while `D6.12` itself reads **high**? If so, an inverting stage
     exists between them and the physical table adoption is justified.
   - *Photo re-trace:* does `D6.12 -> D8.15` and/or `D6.9 -> D13` pass through
     an inverting gate rather than the direct route the prototype PDF shows?
     (`D6.10 -> D9` stays direct — `rev` is already correct.)
   See root `PLAN.md` highest-priority item 1.

## Remaining P0 connectivity (batch in the same session)

2. **D30 / `H` WAIT-READY edge:** exact edge contact + pull-up reference feeding
   `H`/D105.10/D13.13 (`docs/d30-section-b-scan-chase.md`).
3. **D94 `.092` continuity:** the pull-up references on D94.13/D94.14/D94.1,
   D104.10, and the D5-D7 far destinations (`docs/d94-reconstruction-constraints.md`).
4. **FDC support pins** (only if pursuing FDC later; not on the VJUGA path):
   D106.11-D93.27, D106.14-D93.33 layer-handoff tests, and the D95/D101 select
   pins (`docs/fdc-hardware-handoff.md`).
5. **Factory Вид В modifications:** the poz.150/159 cut pads / removed segments /
   replacement nets at D56/D11, plus D14's fifth landing, three long traces,
   and right-row dogleg. D15's A2/A1 cut and D14's D32.4/GND-to-D14.1 link are
   photo-closed and need no continuity probe (`docs/factory-modification-disposition.md`).

## Programmable-parts corroboration (optional, Tier-3)

6. Independent re-reads of the D2/D6/D8/D94 PROMs, and dumps of the D15/D16
   EPROMs, only as corroboration of the validated captures
   (`docs/community-prom-media-request.md`).

The single most valuable item is **#1**. The corrected re-read can close D6
adoption directly; if it exactly matches the old bytes, the reset-fetch probe
or photo re-trace becomes decisive for both the main twin and VJUGA workbench.
