# D96.13 to D99.10 sheet-3 junction

Primary source: exact `.009 Э3` sheet-3 photo `ref/photos/dgsh5-109-009-e3/PXL_20260718_101641055.jpg` (SHA256 `86740a80fb494cdb08f4de3a120cab83e4f6638cf5885d4c83418a4a94c881a7`). At native resolution, the D96 section-2 `/CLR2` lead is numbered `13`. Its stroke runs right to the filled junction on the line entering D99 section-2 `B`/pin `10` (approximately source pixel `(1400,1830)`). A downward arrow from that same junction is annotated `1`, denoting continuation to sheet 1. The nearby D96.9 Q2 outgoing path crosses separately and has no junction dot at the `/CLR2` stroke. The full sheet-3 overview separately traces that Q2 path to D101 A0–A3; see [the D101 input review](d101-section-a-input-source-review.md).

The board model places D96.13 and D99.10 on `D99_B2_SHEET1_BOUNDARY`; the common remote source remains unread. An overview survey of the eight available sheet-1 detail tiles finds several separate `(3)` continuations, including labeled `RES`, `-WREQ`, `MOTOR EN`, `FM/MFM`, and `S.SEL`, but does not identify a uniquely matching mate for the quoted `1` arrow beneath the D96/D99 junction. None of those named signals is promoted onto this line by label similarity or circuit expectation.

The same native sheet-3 frame also puts a similar quoted `1` at the left end
of D100 T/pin11. Those arrows are on different local conductors: D99.10's
branch points downward below D99, while D100.11's branch runs left below it.
No junction joins them in the photographed region. The repeated annotation
pattern (two strokes, a large `1`, and a small raised mark) does not establish
a shared remote node; the two strokes cannot securely be read as a numeric
`11`. Check D99.10↔D100.11 directly on
the target, alongside D96.13↔D99.10, before merging any remote continuation.

This connection gives the D96 half a possible asynchronous clear path, while the actual source, timing, and any further endpoints still require continuity and powered capture. Current routing holds are recorded in [factory-wire fidelity](factory-wire-route-fidelity.md); the source connection does not prove copper completion.

The registered owner photos provide probe targets without proving physical continuity. D96.13 is recorded near `(3307,2128)` in component tile `PXL_20260710_200402344.jpg` and `(626,1903)` in solder tile `PXL_20260710_200506061.jpg`; D99.10 is near `(2909,1231)` in component tile `PXL_20260710_200418174.jpg` and `(1290,738)` in solder tile `PXL_20260710_200522685.jpg`. Enlarged solder crops show separate nearby traces and annuli, but no unbroken visible B.Cu path between these distant joints. With power removed, check D96.13↔D99.10 directly in both meter polarities, then trace the common conductor to its source. A failed join would indicate a board/drawing difference or a registration error and must not be hidden by the source model.

The registered pin spacing also identifies a separate front-copper probe landing for D99.10. Native component crop `(2750,1160)-(3350,1760)` shows an exposed vertical trace from D99.10 near `(2909,1231)` to a circular landing near `(2908,1288)`. D99.11, about one pitch to the right, descends to a different circular landing near `(2964,1340)`; the two front traces do not visibly join. Reflecting the D99.10 landing through the independently fitted D99 package corners predicts about `(1293,681)` on solder photo `200522685`, where native crop `(1180,570)-(1430,800)` shows bare substrate, without a drilled annulus. Treat the D99.10 circle as a one-sided front probe point, not a layer handoff or proof of the upstream source. Probe that circle against D99.10 and D96.13 with power removed; keep the D99.11/MOTOR EN circle separate.

## Model guard

```sh
python3 kicad/check_d99_source_paths.py
```

The guard checks the D96.13/D99.10 JSON junction and its separation from
D100.11 in JSON and structural HDL. The remote source remains unidentified;
the runnable HDL uses an inactive high default for this continuation.
