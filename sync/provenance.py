#!/usr/bin/env python3
# Report the source annotations of a board spec. Net `src` fields now contain
# free-form evidence descriptions, so prefix counts are descriptive only; the
# board-fidelity gap ledger identifies unresolved claims.
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
    "boundary":   "chip pins traced, but the net's other end is an un-modeled subsystem",
    "prom":       "PROM-derived net: the selected rail depends on off-schematic PROM "
                  "contents or an emulator-recovered map; D6 is the memory decode PROM, "
                  "while D2 is a separate bus/wait PROM with no burnable fallback here",
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
scan = sum(n for src, n in nc.items() if src.startswith(("scan", "datasheet")))
prom = nc.get("prom",0)
total = sum(nc.values())
rest = total - scan - prom
print(f"\nscan/datasheet-prefixed: {scan}/{total};  prom: {prom};  "
      f"other free-form source notes: {rest}")
print("Unresolved claims are inventoried in docs/board-fidelity-gap-ledger.md; "
      "prefix counts are not a completeness measure.")
