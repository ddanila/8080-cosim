# Factory insulated-wire route fidelity

Status: **FACTORY WIRE LANDING EVIDENCE HOLD**

The `.009` assembly table proves ten on-board insulated links. Their
logical endpoints are source-closed, but logical net equality is not
permission to replace the original flying wire with PCB etch. This report
separates those two claims. Source/routed parity and electrical DRC are held,
but factory-construction release remains held until all ten links are
represented as explicit assembly wires between split copper islands.

## Command and scope

Run `/usr/bin/python3 kicad/report_factory_wire_route_fidelity.py`
from the repository root with KiCad Python bindings and `kicad-cli` available.
It reruns the landing evidence
guards and DRC on both routed variants, then compares source pad
identities, nets, and centers before overwriting this report. A successful
exit means the invoked
evidence guards passed; release additionally requires the report status
and every parity, DRC, and construction condition below to be ready.
Failed evidence guards produce exit status 1 after the report is written;
exit status 0 can still accompany a route/construction hold.
The report counts DRC unconnected items; it does not summarize or gate
electrical violations in the DRC violation list. Review the full DRC
before release, even if the report status becomes ready.

## Guarded state

- Logical endpoint check: `PASS`
- Landing-registration check: `PASS`
- Board-fit photo/copper evidence checks: `FAIL (5/9)`
- Drawing-image landing endpoints registered: `20/20`
- Landing endpoints fitted to PCB coordinates/islands: `10/20`
- Paired A-point landing terminals modeled: `14/20`
- Photo-confirmed modeled landing relocations still required: `W7.1, W14.1`
- Promoted/source pad identities equal: `FAIL`
- Promoted/source pad-net mismatches: `3`
- Promoted/source moved pads (>50 nm): `210`
- Explicit assembly-wire island splits: `7/10`
- Same-net copper substitutions still held: `3/10`
- Promoted DRC unconnected items: `59`
- Routed-candidate board audit:
  - Candidate/source pad identities equal: `FAIL`
  - Candidate/source pad-net mismatches: `3`
  - Candidate/source moved pads (>50 nm): `210`
  - Link nets carrying candidate copper: `9/10`
  - Candidate DRC unconnected items: `59`
- Required release state: twenty registered and modeled landing terminals,
  ten split island pairs, ten explicit assembly-wire closures, exact source
  parity, and zero electrical/unconnected DRC findings.

The current parity and DRC results above remain release blockers. Seven
links (A7/A8/A10/A11/A14/A19/A20) are explicit W-footprint assembly wires
between separately named copper islands. A9/A12/A13 lack six evidence-gated
landing coordinates, so their endpoints remain same-net copper routes. A7B
and A14B are also masked candidates, and W7.1/W14.1 still need relocation. This
construction hold is additional to the electrical and placement holds.
The candidate results are regenerated from `kicad/juku_routed_candidate.kicad_pcb`;
they do not authorize the promoted board.

The split-island count checks that the two routed W pads have different net
names. It does not by itself prove copper separation, correct endpoint
routing, or an installed wire. Modeled-terminal counts use the source PCB;
copper counts include routed tracks and vias on the named primary island.

## Link audit

| Conductor | Board point | Length cm | Logical net | Guarded logical endpoints | Image-registered endpoints | Modeled A-point terminals | Promoted construction | Copper items on primary island |
| ---: | ---: | ---: | --- | --- | ---: | ---: | --- | ---: |
| 3 | А:7 | ~24 | `PHI1` | D1.22, D35.10 | 2 | 2 | explicit wire / split islands | 95 |
| 4 | А:8 | ~19 | `STSTB` | D38.8, D5.1 | 2 | 2 | explicit wire / split islands | 4 |
| 5 | А:9 | ~12 | `SYNC` | D1.19, D38.12 | 2 | 0 | same-net copper / landing hold | 236 |
| 6 | А:10 | 13.5 | `W10_QA_SEL` | D41.13, D50.1 | 2 | 2 | explicit wire / split islands | 1 |
| 7 | А:11 | ~11.5 | `MEMR` | D7.1, D92.13 | 2 | 2 | explicit wire / split islands | 213 |
| 8 | А:12 | ~20 | `RAM_OUT_EN` | D13.2, D37.4 | 2 | 0 | same-net copper / landing hold | 208 |
| 9 | А:13 | ~15 | `ROE` | D13.1, D92.1 | 2 | 0 | same-net copper / landing hold | 286 |
| 10 | А:14 | ~23 | `PHI2` | D1.15, D35.12 | 2 | 2 | explicit wire / split islands | 48 |
| 13 | А:19 | ~9.5 | `MEMW` | D5.26, D7.2 | 2 | 2 | explicit wire / split islands | 378 |
| 14 | А:20 | ~6 | `S_TTL` | A23.1, D3.10, X3.3 | 2 | 2 | explicit wire / split islands | 0 |

## Remaining release closure

10 PCB landing coordinates/island assignments remain evidence-gated:
`A7B`, `A8B`, `A9A`, `A9B`, `A10B`, `A12A`, `A13A`, `A13B`, `A14B`, and `A12B`. Existing registered component and
solder views either occlude the termination or leave its through-hole
pairing, copper path, or cable identity unproved. A13B now has a
strong photo-traced D92.1/ROE candidate, still awaiting continuity.
A7B/A14B wire terminations are hidden by mastic; their landing coordinates
and cut lengths remain under measurement hold.
The routed board and fabrication package remain under design
hold because A8/A9/A10/A12/A13 physical landings or construction
remain unproved, and because the broader functional P0 netlist is open.
A:7, A:8, A:10, A:11, A:14, A:19, and A:20 are already split into modeled landing pairs and
explicit assembly-wire components. After owner continuity or a newly exposing
photograph closes the unresolved joints:

1. Finish the twenty landing terminals and split each remaining logical
   net into its two original copper islands joined by an explicit wire-link
   assembly object.
2. Add W9/W12/W13 assembly footprints, split their island net names, reroute
   only the affected islands, and achieve zero electrical/unconnected DRC
   findings.
3. Regenerate the fabrication package and emit a wire cut/installation table
   with physically qualified cut lengths and the source lengths shown separately.

## Landing dispositions

Detailed coordinates, image hashes, rejected candidates and probe waypoints
belong to `ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json`
and the per-link physical-fit guards listed in this report's generator.
Current dispositions are:

| Link | Accepted evidence and remaining action |
| --- | --- |
| A7/A14 | CPU-side surface joints are accepted. W7.1/W14.1 still occupy obsolete through-hole positions and need relocation plus copper rework. The remote joints are mastic-covered; their former D41-based coordinates are withdrawn. Cut lengths require measurement. |
| A8 | D5-side A8A is accepted. A8B lacks a proved copper/island assignment; the 19 cm table value is not an approved cut length. See `a8b-corrected-trace-review.json`. |
| A9 | Both ends remain unpromoted. The former remote candidate traces to D92.1/ROE, not D38.12/SYNC. Do not merge SYNC with nearby D38.10/13. See `a9b-corrected-trace-review.json`. |
| A10 | A10A is fitted to D50.1. A10B lacks an identified wire landing; require cable-to-D41.13 continuity. The 13.5 cm source reading is not a qualified replacement cut length. |
| A11 | Both distinct surface landings are fitted on MEMR. Their 119.177 mm chord exceeds the 11.5 cm source reading; measure the replacement cut length. |
| A12 | Both coordinates/island assignments remain held. Candidate joints near the C96 supply-group region do not prove a RAM_OUT_EN wire termination. See `c96-a12-solder-review.json`. |
| A13 | A13A lacks ROE continuity and a traced cable destination; A13B has a strong D92.1/ROE photo-trace candidate but still requires continuity. See `a13a-c95-d50-candidate-review.json` and the A13 boundary guard. |
| A19 | Both distinct MEMW surface landings are fitted; the 94.721 mm span agrees with the approximate 9.5 cm source length. |
| A20 | The D3.10-side surface joint and shared A23.1/X3.3 through-hole landing are fitted on S_TTL. Keep this wire separate from D14/SER_TXD. |

Photo-review JSON names above are under `ref/photos/juku-pcb-2/`.