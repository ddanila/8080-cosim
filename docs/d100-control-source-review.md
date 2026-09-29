# D100 control-line source review

The native `.009 Э3` sheet-3 photo
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101641055.jpg` (SHA256
`86740a80fb494cdb08f4de3a120cab83e4f6638cf5885d4c83418a4a94c881a7`)
separates D100's two control inputs. D99 section-2 `Q_N`/pin12 runs
downward, turns left, and enters D100 `OE_N`/pin9. D100 `T`/pin11 runs
left to its own quoted sheet-1 continuation. Near source pixels
`x≈915, 975, 1028; y≈2300`, the T line crosses three descending
conductors without junction dots. The earlier transcription that joined
D100.9 to D100.11 was wrong.

The board model now puts D100.9 on `D99_Q2N_BOUNDARY` with D99.12 and
keeps D100.11 alone on `D100_CONTROL_SHEET1_BOUNDARY`. The remote sheet-1
source of T is still unread. Original-board D99.12↔D100.9 continuity and
D100.11's remote source need direct measurement. The nearby D96.13/D99.10
branch bears a similar quoted `1` arrow but has no local junction to T;
check D99.10↔D100.11 on the target rather than equating the arrow labels.
An original-pixel reread of `(700,2050)–(1450,2650)` shows the T arrow
annotated with a large `1`, a small raised character resembling Cyrillic `п`,
and two separate strokes to the lower left that can look like `11` or Roman
`II`. These are continuation markings, not a junction to any of the three
crossing vertical conductors. In particular, the two strokes are not a
confirmed decimal `11` or an identified sheet-1 device pin; searching sheet
1 for literal `11` alone cannot resolve this continuation.
The D99.10/D96.13 downward arrow on the same original frame, near
`(1400,1940)`, repeats the same two-stroke / large-`1` / raised-mark pattern.
The matching annotation style does not join those two conductors: their
separate arrowheads terminate different drawn lines, and no common local
junction is drawn. It does rule out treating either two-stroke mark as a
unique D100 pin-11 identifier.
An OCR-assisted search of the native sheet-1 tiles found two prominent `11`
readings in `PXL_20260718_101813438.jpg`, near `(1511,1583)` and
`(1518,3551)`. Original-pixel crops show those are the printed pin-11 labels
of the separate D23 and D29 `T` buffer sections, each pointing to the `A`
rail. They are not matching continuation marks for D100.11. The
sheet-1 remote-source identification therefore remains open.

A native owner-solder recheck also leaves the proposed join unproved. In
`PXL_20260710_200522685.jpg`, crop `(950,490)–(1540,1020)`, the
registered D99.10/B2 joint is near `(1290,738)`; D99.12/Q2_N is a
different joint near `(1180,737)`. This crop does not show an identifiable
continuous B.Cu route from D99.10 to a registered remote endpoint.
D100.11's independently registered joint near `(1135,1322)` is in the
separate `PXL_20260710_200506061.jpg` tile. The two photos cannot turn
the matching-looking continuation typography into D99.10–D100.11
continuity; test the two physical pins directly with power removed.

The owner photo registration identifies the physical D100.11 contact at
approximately `(2707,1379)` in component image
`PXL_20260710_200402344.jpg` and `(1135,1322)` in solder image
`PXL_20260710_200506061.jpg` (`ref/photos/juku-pcb-2/endpoints.csv`). The
notch-left 20-pin fit identifies it as the upper-right component contact; a
native solder crop `(850,1070)–(1500,1570)` shows no unambiguous B.Cu departure
from that registered joint. The component-side conductor is obscured by the
wire/tape bundle. These views locate the meter probe but do not establish a
remote net. Probe this joint separately from D100.9, whose photographed
contact is at approximately `(2652,1545)` component and `(1182,1165)` solder.

The routed replica previously had eleven track segments on the false
D100.9/.11 common net. Those segments were removed from the routed and
candidate PCBs when the pads were split; retaining them would preserve
the wrong join. KiCad DRC now reports a D99.12-to-D100.9 open and no new
short. Routing and fabrication remain on hold.
