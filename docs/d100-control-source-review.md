# D100 control-line source review

The native `.009 Э3` sheet-3 photo
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101641055.jpg` (SHA256
`86740a80fb494cdb08f4de3a120cab83e4f6638cf5885d4c83418a4a94c881a7`)
separates D100's two control inputs. D99 section-2 `Q_N`/pin12 runs
downward, turns left, and enters D100 `OE_N`/pin9. D100 `T`/pin11 runs
left to its own quoted sheet-1 continuation. Near source pixels
`x≈915, 975, 1028; y≈2300`, the T line crosses three descending
conductors without junction dots.

The board model puts D100.9 on `D99_Q2N_BOUNDARY` with D99.12 and
keeps D100.11 alone on `D100_CONTROL_SHEET1_BOUNDARY`. The remote sheet-1
source of T is still unread. Original-board D99.12↔D100.9 continuity and
D100.11's remote source need direct measurement. The nearby D96.13/D99.10
branch bears a similar quoted `1` arrow but has no local junction to T;
check D99.10↔D100.11 on the target rather than equating the arrow labels.
Native crop `(700,2050)–(1450,2650)` shows D100 T's continuation marked
with a large `1`, a raised character resembling Cyrillic `п`, and two separate
lower-left strokes. The D99.10/D96.13 arrow near `(1400,1940)` repeats this
style. Neither mark identifies decimal pin `11`, and matching typography
does not join the separately drawn conductors or identify their remote source.

## Physical probe locations

In solder image `PXL_20260710_200522685.jpg`, crop
`(950,490)–(1540,1020)`, D99.10/B2 is near `(1290,738)` and
D99.12/Q2_N near `(1180,737)`. No continuous B.Cu route from D99.10 to
an identified remote endpoint is visible.

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

## Decision for the next physical check

With the original board unpowered, probe the registered IC legs below and
record each result. Photo coordinates locate the legs; they do not establish
continuity. Keep the two source continuations separate pending these readings.

| Probe pair | What the result establishes |
| --- | --- |
| D100.11 T ↔ D99.10 B2 | Continuity would join the two similarly annotated sheet-3 continuations on the physical board. An open reading leaves their source arrows independent. |
| D100.11 T ↔ D100.9 OE_N | Checks isolation between the separate control inputs. The exact sheet-3 drawing has no local junction here, so any continuity needs a separate physical path to explain it. |
| D100.9 OE_N ↔ D99.12 Q2_N | Checks the drawn local connection independently of T. |
| D99.10 B2 ↔ D96.13 CLR2_N | Checks the other drawn local junction before following its sheet-1 continuation. |

Neither a matching-looking arrow annotation nor an open reading at one probe
pair identifies D100.11's remote driver. Trace that driver from D100.11 only
after recording these four pair results.

## Model guard and routing status

Run from the repository root with Python 3 (standard library only):

```sh
python3 kicad/check_d99_source_paths.py
```

This guard checks canonical JSON endpoints, selected placement metadata, and
literal structural HDL connection markers, including the separation of
D100.9 and D100.11. It does not compile or simulate HDL, measure the original
board, or validate routed copper. Runnable HDL holds the unidentified T
continuation high; that fallback does not establish its physical driver.
Current routing and fabrication
holds are recorded in [factory-wire fidelity](factory-wire-route-fidelity.md)
and [the routed audit](routed-refresh-audit.md).
