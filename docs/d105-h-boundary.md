# D105 H/DBIN boundary

Status: **D105 H/DBIN + X1.107B/R1 ROUTED CLOSURE VERIFIED**

The native full-resolution sheet closes edge contact `X1.107B` (`-BLOCK`)
directly onto D13.13/`H` and labels its pull-up `R1 2 kΩ` to rail A (+5 V).
The `.009` assembly drawing identifies R1 between D13 and D105, the owner
photo registers the populated landings, and direct continuity independently
closes D13.13 to D105.10. Thus D105.10 is not the −5 V supply. CPU D1.17
`DBIN` reaches D105.9;
D105.9/.10 feed one NAND and tied D105.4/.5 invert it again, so D105.6
drives D5.4 as `DBIN AND H`. Tied D105.12/.13 receive `MEMW`, while
D105.11 drives D30.13.

The authoritative board JSON, source PCB, HDL, and promoted routed PCB now
preserve that measured topology. The routed board has exact source-pad identity
and the stable-KiCad route/package gates report zero opens and zero electrical
blockers. Historical DSN/SES and rejected local repair trials remain audit
artifacts only.

| Check | Result | Evidence |
| --- | --- | --- |
| Source model preserves D105_10_H | PASS | `[('D105', '10'), ('D13', '13'), ('R1', '2'), ('X1', '107B')]` |
| Source model preserves DBIN | PASS | `[('D1', '17'), ('D105', '9')]` |
| Source model preserves DBIN_GATED | PASS | `[('D105', '6'), ('D5', '4')]` |
| Source model preserves D105_WAIT_STAGE | PASS | `[('D105', '4'), ('D105', '5'), ('D105', '8')]` |
| Source model preserves D105_MEMW_INV | PASS | `[('D105', '11'), ('D30', '13')]` |
| MEMW reaches tied D105 inputs | PASS | `[('D105', '12'), ('D105', '13')]` |
| H remains separate from derived -5 V | PASS | `[('D1', '11'), ('E5', '1'), ('R19', '2'), ('VD5', '2')]` |
| Native R1 pull-up value is preserved | PASS | `R1=2к; R1.1 on P5V=True` |
| Native/.009/owner evidence registration is intact | PASS | `three source hashes + X1.107B/R1 2к` |
| Source PCB assigns D105.10 to D105_10_H | PASS | `D105_10_H` |
| Source PCB assigns D13.13 to D105_10_H | PASS | `D105_10_H` |
| Source PCB assigns X1.107B to D105_10_H | PASS | `D105_10_H` |
| Source PCB assigns R1.2 to D105_10_H | PASS | `D105_10_H` |
| Source PCB assigns R1.1 to P5V | PASS | `P5V` |
| Source PCB assigns D1.17 to DBIN | PASS | `DBIN` |
| Source PCB assigns D105.9 to DBIN | PASS | `DBIN` |
| Source PCB assigns D105.6 to DBIN_GATED | PASS | `DBIN_GATED` |
| Source PCB assigns D5.4 to DBIN_GATED | PASS | `DBIN_GATED` |
| Source PCB assigns D105.12 to MEMW | PASS | `MEMW` |
| Source PCB assigns D105.13 to MEMW | PASS | `MEMW` |
| Source PCB preserves the registered R1 landings | PASS | `R1.1=(40.88, 210.0); R1.2=(30.72, 210.0)` |
| R1 uses the photographed component-side surface landings | PASS | `F.Cu SMD; no drilled/B.Cu pads` |
| D13/D105 preserve their photographed right-facing notches | PASS | `D13=270.0; D105=270.0` |
| D105 preserves its factory centre with owner-photo orientation | PASS | `(31.9, 215.505)` |
| HDL models pulled-up H and gated DBIN | PASS | `hdl/juku_top.v` |
| Promoted routed PCB preserves the measured D105 nets | PASS | `exact source parity` |

## Rejected routed-snapshot repairs

Earlier local copper trials attempted to preserve the obsolete routed netlist.
They produced shorts or clearance failures around PHI2TTL, PHI2, RESIN, GND,
RAM_OUT_EN, and the E3 control routing. Those trials remain rejected. The
Promoted exact-source routing supersedes those trials and passes DRC without
restoring the old D2.12-to-D105.9 assumption or adding a hidden jumper. Any
future source-net change must regenerate and re-verify the complete package.
