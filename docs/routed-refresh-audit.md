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
| Source footprints | 271 |
| Routed-snapshot footprints | 240 |
| Source-only footprints | 35 |
| Routed-only off-board connector bodies | 4 |
| Routed copper nets | 326 |
| Nets with identical endpoints and pad coordinates | 227 |
| Nets requiring reroute | 99 |
| Reusable track/via items | 5,284 |
| Quarantined track/via items | 3,372 |

The 35 source-only footprints are `A17`, `A21-A32`, `A45-A62`, `R18`, `R30`,
`R94`, and `R104`. The four routed-only bodies are the bracket-mounted
`S1`, `X3`, `X8`, and `X9`; the authoritative source intentionally represents
their PCB cable landings instead.

The source board currently has 7 electrical shorts and 17 clearance findings
before any routed copper is transplanted. The conservatively merged audit
candidate has 33 shorts and 41 clearance findings, so it is correctly rejected.
The extra collisions localize old routes crossing newly fitted D2/D10/D94/FDC
support geometry and the added cable/passive landings.

A clean refresh therefore requires this order:

1. repair source-placement electrical overlaps;
2. generate the compatible-copper candidate;
3. iteratively remove any transplanted net implicated by DRC;
4. route the quarantined nets against the current placement;
5. replace `juku_routed.kicad_pcb` only after endpoint parity and zero electrical
   DRC findings are both proved.

## Rejected full reroute

A fresh Freerouting 2.2.4 run from the current 359-net source was also tested.
Pass 1 took 8 minutes 43 seconds and still had 299 unrouted connections; pass 2
did not finish within another five minutes. That inferior candidate was stopped
and deleted rather than replacing the nearly routed snapshot.
