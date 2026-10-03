# VT2 video stage in exact .009 Э3 sheet 2

The archived `.009` electrical drawing itself is the primary source for the populated composite-video stage. The older `.006` drawing is useful for revision history, but is not needed to infer this stage's topology.

| Exact `.009` frame | SHA-256 | Visible evidence |
| --- | --- | --- |
| `ref/photos/dgsh5-109-009-e3/PXL_20260718_101927794.jpg` | `a31896156ad7e1bc35e59ee43223babd3d39f40f2a086152d26f76cf14c71aa9` | D34.8 feeds R62 (2 kΩ); D34.11 feeds R63 (1 kΩ). Their far ends join R64 (5.1 kΩ) and the base of VT2 (КТ315). VT2's collector goes to +5 V; its emitter feeds VIDEO and R65 (430 Ω) to ground. |
| `ref/photos/dgsh5-109-009-e3/PXL_20260718_101932581.jpg` | `9aba327c149b59049c6fdb5ad6d9f13d43df4810765cf8865726d9bf911bd86d` | The VIDEO line continues to output contact 3, numbered connection 601; ground reaches contact 4, numbered connection 602. The crop does not itself label the physical connector; the assembly and system drawings identify display connector X6. |

The same sheet-2 area draws the R66/VD3/R67 branch. The source marks R67 as 2 kΩ and draws its far end to the VT2 base/R62.2/R63.2/R64.1 node. The target body's observed 4.7 kΩ value takes precedence for the recreated populated board. Its upper far lead has a photo-registered solder joint near (869,953) in 200522685 and a continuous B.Cu run to open annulus (1295,958). The annulus’s remote net and the source-drawn VT2-base connection remain continuity boundaries; see [the X6/R67 continuity review](x6-a3-video-source-conflict-review.md).

## VD3 polarity discrepancy

The exact `.009` sheet-2 symbol places VD3's **anode at ground** (left of the symbol) and **cathode at the R66/R67 sound-clamp junction** (right of the symbol). This is also the electrically plausible orientation for a zener fed through R66 from the +12 V `B` rail. The current `juku.board.json` assigns VD3 pin 1 (`K`) to GND and pin 2 (`A`) to SOUND_CLAMP, the reverse of that drawing. The generated KiCad diode symbol inherits those reversed pin names. This is a source/model conflict, not an established target-board polarity.

The July component view `PXL_20260710_200418174.jpg` and independent May
view `PXL_20260519_201927098.jpg` show VD3's red upper and green lower
coatings. Neither establishes a cathode band or a unique lead-to-copper path.
The D102-local projection into solder view `200522685` identifies no matching
VD3 through-hole annulus. The X6 A:3 cable joint is physically separate.
Native crop coordinates, registration calculations, source hashes, and their
limits are preserved in
[the VD3 photo review](../ref/photos/juku-pcb-2/vd3-polarity-photo-review.json).
Confirm the cathode lead and both lead nets together before remapping pads.

Targeted owner check: the original-resolution July view exposes the upper/red VD3 solder pool near `(3420,1740)` and lower/green pool near `(3426,2028)` in `PXL_20260710_200418174.jpg`. These coordinates identify accessible component-side probe points, not cathode or numbered-pad identities. Identify the marked cathode end of VD3, then test it against R66.2/R67.1 and the opposite end against ground. Test X6 A:3 separately against both VD3 ends, VT2 emitter, and R65. Record the results before changing the KiCad footprint orientation or pad numbers.

The model retains `VIDEO_OUT` at VT2.1/R65.1. Assembly and system drawings
identify bracket connector X6 through A:3/A:4; no physical X7 is modeled.
A:3's copper path to the stage remains a target-board continuity hold. See
[the X6/R67 review](x6-a3-video-source-conflict-review.md) for cable identity
and the required measurements.

## Model verification

```sh
python3 scripts/report_video_analog_boundary.py
```

This checks selected JSON endpoints, revision metadata, and evidence-file
availability. The source/photo polarity discrepancy above remains unresolved;
a passing report does not verify VD3's physical lead nets or output voltage.
