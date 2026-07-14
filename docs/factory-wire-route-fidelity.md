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
- Drawing-image landing endpoints registered: `16/20`
- Landing endpoints fitted to PCB coordinates/islands: `0/20`
- Paired A-point landing terminals modeled: `0/20`
- Link nets carrying candidate copper: `10/10`
- Candidate DRC unconnected items: `0`
- Required release state: twenty registered landing terminals, no copper
  bridge between each island pair, and exactly ten assembly-wire closures.

The current candidate's zero unconnected items are useful routing-convergence
evidence, but for these ten links they prove copper substitution rather than
historical construction fidelity.

## Link audit

| Conductor | Board point | Length cm | Logical net | Guarded logical endpoints | Image-registered endpoints | Modeled A-point terminals | Candidate copper items on net |
| ---: | ---: | ---: | --- | --- | ---: | ---: | ---: |
| 3 | А:7 | ~24 | `PHI1` | D1.22, D35.10 | 2 | 0 | 241 |
| 4 | А:8 | ~19 | `STSTB` | D38.8, D5.1 | 0 | 0 | 317 |
| 5 | А:9 | ~12 | `SYNC` | D1.19, D38.12 | 2 | 0 | 409 |
| 6 | А:10 | ~11.5 | `W10_QA_SEL` | D41.13, D50.1 | 2 | 0 | 272 |
| 7 | А:11 | ~11.5 | `MEMR` | D7.1, D92.13 | 2 | 0 | 189 |
| 8 | А:12 | ~20 | `RAM_OUT_EN` | D13.2, D37.4 | 0 | 0 | 176 |
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
`(2503,2325)` original-image pixels (each ±6 px). Their PCB coordinates
and island assignments remain deliberately unset pending a checked local fit.
`А:19` is likewise guarded across two overlapping views: R7 lies between
the left `(1310,3122)` and right `(1283,3110)` image-local endpoints.
The same overlap method guards `А:11` at `(1563,3155)` in `114556899`
and `(1898,2837)` in `114600417`; PCB promotion remains pending.
`А:10` is complete in one view at `(821,3778)` and `(3016,3702)`
in `114556899`, again with PCB coordinates deliberately unset.
`А:13` is guarded across `114556899`/`114600417` at `(467,3851)`
and `(1625,3443)`, with C95/D38 between the marks.
`А:9` is guarded across `114604420`/`114600417` at `(2967,1768)`
and `(1159,3623)` on its shallow diagonal run.
`А:14` is the upper of two close parallel lines at `(1277,1832)` in
`114604420` and `(1700,4044)` in `114600417`; the lower line is `А:7`.
That lower `А:7` line is separately guarded at `(1161,1845)` and
`(1761,4062)` in the same respective views.
