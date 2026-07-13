# Routed PCB refresh audit

The routed fabrication snapshot predates substantial photo-driven placement and
connectivity work. It cannot safely receive the current source PCB's pad nets by
name alone: added and moved footprints now intersect old copper corridors.

## Reproducible audit

```sh
/usr/bin/python3 kicad/refresh_routed_from_source.py
```

The script compares complete endpoint sets and exact pad coordinates per net.
It classifies copper as reusable only when both are identical between
`juku.kicad_pcb` and `juku_routed.kicad_pcb`. Candidate generation is explicit:

```sh
/usr/bin/python3 kicad/refresh_routed_from_source.py \
  --output /tmp/juku-routed-refresh.kicad_pcb
```

The temporary candidate is an audit artifact, not a fabrication deliverable.

## Current result

| Item | Count |
| --- | ---: |
| Source footprints | 277 |
| Routed-snapshot footprints | 240 |
| Source-only footprints | 42 |
| Routed-only off-board connector bodies | 5 |
| Routed copper nets | 326 |
| Nets with reusable routed copper | 207 |
| Routed nets quarantined before DRC | 119 |
| Initially reusable track/via items | 4,874 |
| Initially quarantined/duplicate items | 3,782 |
| Additional nets quarantined from candidate DRC | 16 |
| Reusable items after DRC quarantine | 4,330 |

The source-only set includes `A17`, `A21-A32`, `AX401-AX423`, `A45-A62`, newly modeled FDC
support/passive parts, and the photo-fitted serial resistors. The five routed-only bodies are the off-board
`S1`, `S4`, `X3`, `X8`, and `X9`; the authoritative source intentionally represents
their PCB cable landings instead. X4 is likewise schematic-only in the source;
its newly modeled `AX401-AX423` landing row is absent from the stale routed snapshot.

The July-2026 refresh audit found 48 short violations in the first candidate.
Feeding that DRC JSON back through `--exclude-drc` quarantines 16 implicated
routed nets and removes every transplanted-track short. The remaining 12 DRC
short violations were six duplicated pad-to-pad placement collisions already
present in that source snapshot: approximate analog-part positions overlapped the
factory-registered D95/D97/D102 cluster. The current regenerated source has nine
collision pairs because the corrected factory/photo-proven VD3, R86, and C19 positions expose
the old unregistered L1, legacy `.006` VT3, and approximate R74 seeds as false. S4 is now correctly schematic/off-board
and no longer contributes a fabricated footprint collision. The routed candidate therefore
remains rejected. This corrected audit supersedes the earlier false zero-short
statement, which inspected a nonexistent top-level JSON field instead of
`violations[type=shorting_items]`.

A clean refresh therefore requires this order:

1. repair the nine current source-placement electrical overlaps from stronger placement evidence;
2. generate the compatible-copper candidate;
3. iteratively quarantine any transplanted net implicated by DRC using `--exclude-drc`;
4. route the quarantined nets against the current placement;
5. replace `juku_routed.kicad_pcb` only after endpoint parity and zero electrical
   DRC findings are both proved.

## Rejected full reroute

A fresh Freerouting 2.2.4 run from the current 359-net source was also tested.
Pass 1 took 8 minutes 43 seconds and still had 299 unrouted connections; pass 2
did not finish within another five minutes. That inferior candidate was stopped
and deleted rather than replacing the nearly routed snapshot.
