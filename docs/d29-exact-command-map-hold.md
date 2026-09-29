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
The old D29.1/.2/.3/.6 photo seeds in `endpoints.csv` were misplaced on chip
bodies in component view `200354648` and on inter-row traces in solder view
`200509593`. The corrected component probe centres are approximately
`(2213,1438)/(2265,1438)/(2318,1438)/(2478,1438)`; reflected solder
centres are `(2489,1588)/(2441,1588)/(2393,1588)/(2249,1588)`. Both
sets follow the visible ten-contact lower row and left-notch pin count;
they do not constitute owner continuity measurements.
In component photo `200354648`, D29.2's lower lead has a front-copper
segment toward the white cable; a collinear segment below the cable ends
at an exposed annulus near `(2255,2352)`. The cable hides the intervening
copper, so the annulus is a probe candidate rather than a closed join.
The D29-corner cross-face projection of that annulus falls near
`(2451,2393)` in solder view `200509593`, on bare board. A drilled hole
near `(2450,2433)` is about 40 pixels south on a separate narrow trace;
the extrapolation is too long to adopt it as the same hole.
The local chase is recorded in
`ref/photos/juku-pcb-2/d29-pin2-front-chase.json`; the opposite-face route
and D7.3 remote join remain unproved.

Exact sheet-1 detail `(1000,3040)–(1740,3540)` shows D7.3 directly feeding
D29.2; the riser crosses D29.7 without a dot. The lower continuation puts
D29.8 on `-MWR`/MEMW, D29.4 on `-IORD`, and D29.5 on `-IOWR`. These
connections are now modeled. The source-drawn D7.3→D29.2 join and
separate D7.11/D105.3 source output tie still requires owner-board continuity before physical
fidelity can be claimed.

The old routed copper touching the changed D29/D35 pads caused 30 shorts and
three clearances. Removing 32 stale track/via items in each routed variant
restored zero shorts, clearances, and crossings; the remaining 35 unrouted
connections require a fresh routing pass. The deletion list is in
`ref/routing/d29-command-copper-correction.json`. Fabrication remains held
by those opens, passive placement, and physical continuity questions.
