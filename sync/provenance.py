#!/usr/bin/env python3
# Report the provenance of a board spec: how much of the connectivity is read
# from the schematic scan vs assumed/convention/datasheet. Keeps the "source of
# truth" honest -- nothing should be silently invented.
#
# Usage: provenance.py <board.json>
import sys, json
from collections import Counter

LEGEND = {
    "scan":       "read directly off the schematic scan",
    "datasheet":  "standard-part pin from datasheet (cross-checked vs scan where possible)",
    "convention": "standard 8080-system wiring assumed from general knowledge, NOT yet traced on the scan",
    "assumed":    "simplifying assumption (bus bit-order / byte-split) pending a scan trace",
    "placeholder":"provisional pin numbers/refdes, not yet sourced",
}

b = json.load(open(sys.argv[1]))
print(f"# provenance: {sys.argv[1]}\n")
nc = Counter()
for name, e in b["nets"].items():
    src = e.get("src", "untagged") if isinstance(e, dict) else "untagged"
    nc[src] += 1
print("NETS by source:")
for src, n in sorted(nc.items(), key=lambda x: -x[1]):
    print(f"  {n:3}  {src:11} — {LEGEND.get(src,'?')}")
print("\nCHIPS:")
for c in b["chips"]:
    p = c.get("prov", {})
    print(f"  {c['ref']:5} {c['type']:9}  type={p.get('type','?')}, refdes={p.get('refdes','?')}, pins={p.get('pins','?')}")
scan = nc.get("scan",0)+nc.get("datasheet",0)
total = sum(nc.values())
print(f"\nscan/datasheet-grounded nets: {scan}/{total}; "
      f"assumed/convention: {total-scan}/{total}  <-- harden these against the scan")
