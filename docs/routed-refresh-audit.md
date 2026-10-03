# Routed PCB refresh audit

Status: **DESIGN HOLD / SOURCE REFRESH AND REROUTE REQUIRED**.

The source PCB is the current placement/net model. The routed PCB is an
engineering snapshot: matching net names do not establish matching physical
pads, reusable copper or fabrication readiness. The current drift inventory
is in [factory-wire-route-fidelity.md](factory-wire-route-fidelity.md).

## Reproducible audit

```sh
/usr/bin/python3 kicad/refresh_routed_from_source.py
/usr/bin/python3 kicad/refresh_routed_from_source.py --check-report docs/routed-refresh-audit.md
```

The script compares complete endpoint sets and exact pad coordinates per net.
It reuses copper only when both agree. After an intentional source or routed
change, update the current-result table with `--report docs/routed-refresh-audit.md`.

Generate a candidate explicitly and inspect it before adopting copper:

```sh
/usr/bin/python3 kicad/refresh_routed_from_source.py --output /tmp/juku-routed-refresh.kicad_pcb
```

## Current result

<!-- routed-refresh-current:start -->
| Item | Count |
| --- | ---: |
| Source PCB SHA-256 | `c1fbfcdeae9a859f76d9c46f79c570f83e7d1a98a5a136ef60e818d801482b97` |
| Routed-snapshot PCB SHA-256 | `f22f7ba849a6088d7b41e8f2ada8153cda9226c8848bec00128044177643e26a` |
| Source footprints | 324 |
| Routed-snapshot footprints | 322 |
| Source-only footprints | 2 |
| Routed-only footprints | 0 |
| Routed copper nets classified by the refresh | 404 |
| Nets with currently reusable routed copper | 285 |
| Routed nets currently quarantined | 119 |
| Reusable non-duplicate track/via items | 15,210 |
| Quarantined/duplicate track/via items | 15,133 |
| Common-pad net mismatches requiring reroute | 3 |
<!-- routed-refresh-current:end -->

## Acceptance boundary

Check the candidate against the current board model, physical package and
factory-wire evidence, connectivity and DRC. Resolve placement conflicts
before copying old copper. The authoritative release command is
`kicad/check_replica_manufacturing_ready.sh`; the current upload package must
be regenerated after source/routing repair.

Detailed measured pad drift belongs in the factory-wire report. Rejected
routing experiments and their hash-bound diagnostics remain under
`ref/routing/`; superseded execution sequences are available in Git history.
