# Factory insulated-wire route fidelity

Status: **LOGICAL LINKS ADOPTED / LANDING REGISTRATION PARTIAL / ROUTED CANDIDATE HOLD**

The `.009` assembly table proves ten on-board insulated links. Their
logical endpoints are source-closed, but logical net equality is not
permission to replace the original flying wire with PCB etch. This report
separates those two claims and blocks production adoption of the current
zero-open routing checkpoint.

## Guarded state

- Logical endpoint check: `PASS`
- Landing-registration check: `PASS`
- Board-fit photo/copper evidence checks: `PASS`
- Drawing-image landing endpoints registered: `20/20`
- Landing endpoints fitted to PCB coordinates/islands: `9/20`
- Paired A-point landing terminals modeled: `0/20`
- Candidate/source pad identities equal: `PASS`
- Candidate/source pad-net mismatches: `35`
- Candidate/source moved pads (>50 nm): `138`
- Link nets carrying candidate copper: `10/10`
- Candidate DRC unconnected items: `0`
- Required release state: twenty registered landing terminals, no copper
  bridge between each island pair, and exactly ten assembly-wire closures.

The current candidate's zero unconnected items are useful routing-convergence
evidence, but for these ten links they prove copper substitution rather than
historical construction fidelity. It is also a preserved checkpoint rather
than a current-source route: later net and photo-placement corrections must
be incorporated only after the landing islands and functional netlist freeze.

## Link audit

| Conductor | Board point | Length cm | Logical net | Guarded logical endpoints | Image-registered endpoints | Modeled A-point terminals | Candidate copper items on net |
| ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| 3 | А:7 | ~24 | `PHI1` | D1.22, D35.10 | 2 | 0 | 241 |
| 4 | А:8 | ~19 | `STSTB` | D38.8, D5.1 | 2 | 0 | 317 |
| 5 | А:9 | ~12 | `SYNC` | D1.19, D38.12 | 2 | 0 | 409 |
| 6 | А:10 | 13.5 | `W10_QA_SEL` | D41.13, D50.1 | 2 | 0 | 272 |
| 7 | А:11 | ~11.5 | `MEMR` | D7.1, D92.13 | 2 | 0 | 189 |
| 8 | А:12 | ~20 | `RAM_OUT_EN` | D13.2, D37.4 | 2 | 0 | 176 |
| 9 | А:13 | ~15 | `ROE` | D13.1, D92.1 | 2 | 0 | 116 |
| 10 | А:14 | ~23 | `PHI2` | D1.15, D35.12 | 2 | 0 | 230 |
| 13 | А:19 | ~9.5 | `MEMW` | D5.26, D7.2 | 2 | 0 | 141 |
| 14 | А:20 | ~6 | `S_TTL` | A23.1, D3.10, X3.3 | 2 | 0 | 11 |

## Next automatic closure

1. Register both physical landing positions for each repeated `А:N` label
   from the full-resolution placement drawing and two-sided owner photos.
2. Add the twenty one-pad landings to the source PCB and split each logical
   net into its two original copper islands joined by an explicit wire-link
   assembly object.
3. Reroute only the affected islands, require exactly ten intentional
   unconnected DRC pairs, and emit a wire cut/installation table with the
   factory lengths.
4. Only then may the refreshed candidate replace production copper.

`А:20` remains on `S_TTL`: enlarged sheet-1 review reads the adjacent
vertical package as `Д104`, not `Д14`, consistent with owner continuity
D3.10-A23-X3.3 and inconsistent with moving the link onto `SER_TXD`.
Its two drawing endpoints are now guarded at `(2022,1408)` and
`(2503,2325)` original-image pixels (each ±6 px). The D3-side white wire
terminates at `(1232,872)` in owner image `200418174`; its short tinned
departure reaches locally fitted D3.10, proving A20B/S_TTL at
`(213.571,78.499)` mm. At the other end, three component overlaps put
the entering white wire and mastic over A23.1; independent solder views
`200506061`/`200509593` show the third-from-right A23 joint with no
solder-side copper departure. This proves the shared A20A/A23.1/X3.3
through-hole joint at `(178.780,15.200)` mm rather than merely net equality.
`А:19` is likewise guarded across two overlapping views: R7 lies between
the left `(1310,3122)` and right `(1283,3110)` image-local endpoints.
At its D5 end, the marked КР580ВК38's complete contact field and
right-facing notch identify D5.26 at `(1214,1480)` in owner image
`200411500`; a straight 113 px copper segment reaches the distinct
white-wire surface joint `(1218,1593)`. This proves A19A/MEMW at
`(35.308,122.281)` mm. The same uninterrupted insulated lead ends at
the distinct `(3255,1585)` surface joint below the marked black D7.
The terminal is `(130.027,121.736)` mm: its 94.721 mm span from A19A
matches the factory approximately 9.5 cm conductor and proves the
D7.2-side MEMW landing rather than a neighboring white-wire endpoint.
The same overlap method guards `А:11` at `(1563,3155)` in `114556899`
and `(1898,2837)` in `114600417`; PCB promotion remains pending.
`А:10` is complete in one drawing view at `(821,3778)` and
`(3016,3702)` in `114556899`. At the D41 end, component joint
`(2148,2174)` and reflected solder joint `(1506,1834)` agree within
0.024 mm and a 2.267 mm copper spur reaches D41.13. At the D50 end,
component joint `(2804,2266)` and reflected solder joint `(915,2000)`
agree within 0.012 mm and a 4.370 mm spur reaches D50.1. This proves
A10A `(240.091,146.982)` mm and A10B `(108.865,152.813)` mm on
`W10_QA_SEL`. Their 131.355 mm chord agrees with the duplicate's
final corrected 13.5 cm conductor length; the earlier tentative
`~11.5` reading is retired.
`А:13` is guarded across `114556899`/`114600417` at `(467,3851)`
and `(1625,3443)`, with C95/D38 between the marks.
`А:9` is guarded across `114604420`/`114600417` at `(2967,1768)`
and `(1159,3623)` on its shallow diagonal run.
`А:14` is the upper of two close parallel lines at `(1277,1832)` in
`114604420` and `(1700,4044)` in `114600417`; the lower line is `А:7`.
That lower `А:7` line is separately guarded at `(1161,1845)` and
`(1761,4062)` in the same respective views.
`А:12` is guarded at `(1714,2216)` in `114604420` and `(1349,2148)`
in `114611058`, spanning the D13/R20-to-C96/D35 drawing regions.
`А:8` completes the drawing-image inventory at `(1624,276)` in
`114604420` and `(1105,443)` in `114611058`; both are plain endpoint
marks, not the separate circled drawing callout after R13. The D5-side
white-wire joint `(1335,1103)` in `200411500` has a visible 42 px
copper spur to fitted D5.1, proving A8A/STSTB at `(40.811,99.989)` mm.
Together with the D38-side landing below, its 195.9 mm chord exceeds
the duplicate's 19 cm entry; endpoint geometry is adopted, but the final
A8 fabrication cut length remains held for re-read or direct measurement.
Two D38-side physical landings are now promoted through the validated
D38/D41 local fits. The right white-wire joint at `(2286,2450)` in
`200418174` reaches via `(2288,2298)` and then fitted D38.12 on continuous
solder copper, proving A9B/SYNC at `(245.695,160.293)` mm. With exactly
two factory-wire joints in that D38 field, the remaining `(1810,2696)`
joint is A8B/D38.8 at `(223.601,170.724)` mm. Both are component-side
surface-soldered copper landings, not invented through-hole pads.
