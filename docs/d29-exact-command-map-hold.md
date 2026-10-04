# D29 exact .009 command pin map

Status: **SOURCE MODEL CORRECTED / PHYSICAL AND ROUTING HOLD**

The original-resolution `.009 Э3` sheet-1 crop
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101813438.jpg`
`(1520,3000)–(2360,3580)` prints every D29 physical input pin, paired
output pin, and command label. The transcription is preserved in
`ref/schematics/d29-exact-009-pinmap-review.json`. Its pairs match the
КР580ВА86/Intel 8286 physical pairs: 1↔19, 2↔18, …, 8↔12. Symbol row order
is permuted and cannot substitute for pad numbers.

| Input pin | Output pin | Exact .009 output label | Corrected replica output at that pad |
| ---: | ---: | --- | --- |
| 3 | 17 | `-INHIB` | `INHIB_N` (aligned) |
| 1 | 19 | `CCLCK` | `CCLCK` |
| 2 | 18 | `-IO/M` | `IOM_N` |
| 7 | 13 | `-MWC` | `MWC_N` |
| 6 | 14 | `-MRC` | `MRC_N` (aligned) |
| 8 | 12 | `-AMWC` | `AMWC_N` |
| 4 | 16 | `-IORC` | `IORC_N` |
| 5 | 15 | `-IOWC` | `IOWC_N` |

The board JSON, schematic, all three PCB pad maps, HDL bus ordering, and
8286 pinout audit now use these exact rows. D29.1 is on PHI2TTL; D35.13 is
on the separate post-R35 node. The three passive parts R35, R106, and C29
exist in the source model but await footprint placement and owner measurements.
The D29.1/.2/.3/.6 component probe centres are approximately
`(2213,1438)/(2265,1438)/(2318,1438)/(2478,1438)`; reflected solder
centres are `(2489,1588)/(2441,1588)/(2393,1588)/(2249,1588)`. Both
sets follow the visible ten-contact lower row and left-notch pin count;
they do not constitute owner continuity measurements.
In component photo `200354648`, D29.2's lower lead has a front-copper
segment toward the white cable; a collinear segment below the cable ends
at an exposed annulus near `(2255,2352)`. The cable hides the intervening
copper, so the annulus is a probe candidate rather than a closed join.
Independent tile matching places that waypoint at front `(2480,1015)` in
`200411500`. D7/D9 local reflections register its opposite-face hole near
`(3065,730)` in solder view `200525009`; the long D29-only extrapolation into
`200509593` does not identify the same hole. The current evidence is in
`ref/photos/juku-pcb-2/d29-pin2-front-chase.json` and summarized with the
D7-side probe candidates in [the D7 review](d7-gates-source-review.md).
Photo registration does not close the cable-hidden D29.2 segment or the
D7.3 remote join; verify both by continuity.

Exact sheet-1 detail `(1000,3040)–(1740,3540)` shows D7.3 directly feeding
D29.2; the riser crosses D29.7 without a dot. The lower continuation puts
D29.8 on `-MWR`/MEMW, D29.4 on `-IORD`, and D29.5 on `-IOWR`. These
connections are now modeled. The source-drawn D7.3→D29.2 join still requires
owner-board continuity before physical fidelity can be claimed. Native
sheet-1 pixels show D7.11 and D105.3 on
separate local strokes, correcting the earlier claimed output tie.

## Verification and routing hold

Run from the repository root with Python's standard library:

```sh
python3 scripts/report_8286_pinout_audit.py
```

This regenerates [the pinout audit](8286-pinout-audit.md), checking selected
source-model endpoints and LVS mapping data. It does not run LVS or inspect
PCB copper. Current routing
and DRC holds are recorded in [factory-wire fidelity](factory-wire-route-fidelity.md)
and [the routed audit](routed-refresh-audit.md). Physical continuity and
R35/R106/C29 placement/value questions remain open.
