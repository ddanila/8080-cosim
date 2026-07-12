# D105 H/DBIN boundary

Status: **D105 H/DBIN HANDOFF ADOPTED / ROUTED REFRESH REQUIRED**

Direct owner continuity on the physical `.009` board supersedes the older
interpretation of this package. D105.10 is the pulled-up edge-bus `H` net
shared with D13.13, not the −5 V supply. CPU D1.17 `DBIN` reaches D105.9;
D105.9/.10 feed one NAND and tied D105.4/.5 invert it again, so D105.6
drives D5.4 as `DBIN AND H`. Tied D105.12/.13 receive `MEMW`, while
D105.11 drives D30.13.

The authoritative board JSON, source PCB, and HDL now preserve that measured
topology. The routed PCB/DSN/SES predate it and remain deliberately stale:
they must be regenerated after the separately documented placement collisions
are resolved, not patched locally around invalid package placement.

| Check | Result | Evidence |
| --- | --- | --- |
| Source model preserves D105_10_H | PASS | `[('D105', '10'), ('D13', '13')]` |
| Source model preserves DBIN | PASS | `[('D1', '17'), ('D105', '9')]` |
| Source model preserves DBIN_GATED | PASS | `[('D105', '6'), ('D5', '4')]` |
| Source model preserves D105_WAIT_STAGE | PASS | `[('D105', '4'), ('D105', '5'), ('D105', '8')]` |
| Source model preserves D105_MEMW_INV | PASS | `[('D105', '11'), ('D30', '13')]` |
| MEMW reaches tied D105 inputs | PASS | `[('D105', '12'), ('D105', '13')]` |
| H remains separate from derived -5 V | PASS | `[('D1', '11'), ('E5', '1'), ('R19', '2'), ('VD5', '2')]` |
| Source PCB assigns D105.10 to D105_10_H | PASS | `D105_10_H` |
| Source PCB assigns D13.13 to D105_10_H | PASS | `D105_10_H` |
| Source PCB assigns D1.17 to DBIN | PASS | `DBIN` |
| Source PCB assigns D105.9 to DBIN | PASS | `DBIN` |
| Source PCB assigns D105.6 to DBIN_GATED | PASS | `DBIN_GATED` |
| Source PCB assigns D5.4 to DBIN_GATED | PASS | `DBIN_GATED` |
| Source PCB assigns D105.12 to MEMW | PASS | `MEMW` |
| Source PCB assigns D105.13 to MEMW | PASS | `MEMW` |
| HDL models pulled-up H and gated DBIN | PASS | `hdl/juku_top.v` |
| Invalid routed snapshot is explicitly stale | PASS | `D105.9: D2_WAIT_RAW != DBIN; D105.6: D105_WAIT_PREINV != DBIN_GATED; D5.4: DBIN != DBIN_GATED; D105.12: MEMR != MEMW; D105.13: MEMR != MEMW` |

## Rejected routed-snapshot repairs

Earlier local copper trials attempted to preserve the obsolete routed netlist.
They produced shorts or clearance failures around PHI2TTL, PHI2, RESIN, GND,
RAM_OUT_EN, and the E3 control routing. Those trials remain rejected. The
correct next operation is a complete routed refresh from the measured source
netlist after collision-free placement, followed by DRC—not restoration of the
old D2.12-to-D105.9 assumption or a hidden jumper.
