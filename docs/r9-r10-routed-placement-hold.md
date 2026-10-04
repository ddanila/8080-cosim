# R9/R10 routed-placement hold

Both routed variants omit the photo-identified R9/R10 footprints and retain
D12's old placement. The [placement parity report](board-placement-parity.md)
records the current coordinates and rotations.

Relocate D12 and review its routed connections before adding R9/R10. Copying
the source footprints directly into the existing routed copper produced
shorts and clearance failures in a recorded trial. The
[collision audit](r9-r10-routed-collision-audit.md) identifies the affected
copper, mechanical limits, and repair scope.

Reroute the resistor connections and displaced D12 copper, then verify DRC,
connectivity, and placement parity. Owner continuity of the resistor joints
remains a separate requirement.
