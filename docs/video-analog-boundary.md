# Video analog boundary

Status date: 2026-07-13.

Status: **.009 COMPOSITE HANDOFF GUARDED / .006 RF OPTION DNP**

Exact `.009` Э3 sheet 2 draws the populated VT2 composite-video stage and
the VIDEO output contacts. The older `.006` electrical sheet is historical
corroboration; its dashed VT3/VT4 RF modulator is not a valid `.009` population source.
The complete `.009` factory placement views label only VT1/VT2, and the complete owner
component-side tile set corroborates that absence. The archived group BOM independently
assigns the extra RF transistors and the 4.7 kΩ adjustable trimmer to `.006`.

C9/C10/C11/C12/C15 are not removed: `.009` reuses those reference numbers around
D93-D102. Exact `.009` sheet-1 supply detail makes each a +5 V-to-ground
bypass, but their physical pin-to-rail assignments remain explicit continuity
boundaries instead of inheriting superseded `.006` RF nets. The same source
proves C94's +5 V/GND pair while its body and pad mapping stay open. X6 is instead
bracket-mounted: A:3/X6.1 is isolated pending continuity and A:4/X6.2 reaches GND.

## Command

```sh
python3 scripts/report_video_analog_boundary.py
```

## Revision checks

| Check | Result | Evidence |
| --- | --- | --- |
| All cross-revision evidence files are local | PASS | 24 schematic/BOM/factory/owner artifacts |
| Legacy .006 RF-only population is absent from the .009 board model | PASS | C13, C14, L1, R68, R69, R70, R71, R72, R73, R74, R75, R76, R77, VT3, VT4 |
| Legacy RF net names are retired | PASS | HF_OUT, RF_RAIL, RF_TANK, RF_TAP, SND_MIX, VT3_BASE, VT3_E, VT4_B, VT4_C, VT4_E |
| Factory-reused C9/C10/C11/C12/C15 remain generic capacitors | PASS | physical .009 identities retained; .006 RF assignments not carried across |
| Exact .009 source proves reused capacitors' +5 V/GND pair while pad polarity stays open | PASS | sheet-1 C9...C12/C15 bypass group; physical pad mapping pending |
| `D34_SYNC` has exactly the target endpoints | PASS | D34.8, R62.1 |
| `D34_SIG` has exactly the target endpoints | PASS | D34.11, R63.1 |
| `VT2_BASE` has exactly the target endpoints | PASS | R62.2, R63.2, R64.1, VT2.3 |
| `VIDEO_OUT` has exactly the target endpoints | PASS | R65.1, VT2.1 |
| `SOUND_CLAMP` has exactly the target endpoints | PASS | R66.2, R67.1, VD3.2 |
| `X6_A3_BOUNDARY` has exactly the target endpoints | PASS | AX603.1, X6.1 |
| `R67_2_BOUNDARY` has exactly the target endpoints | PASS | R67.2 |
| `C94_1_BOUNDARY` has exactly the target endpoints | PASS | C94.1 |
| `C94_2_BOUNDARY` has exactly the target endpoints | PASS | C94.2 |
| `C9_1_BOUNDARY` has exactly the target endpoints | PASS | C9.1 |
| `C9_2_BOUNDARY` has exactly the target endpoints | PASS | C9.2 |
| `C10_1_BOUNDARY` has exactly the target endpoints | PASS | C10.1 |
| `C10_2_BOUNDARY` has exactly the target endpoints | PASS | C10.2 |
| `C11_1_BOUNDARY` has exactly the target endpoints | PASS | C11.1 |
| `C11_2_BOUNDARY` has exactly the target endpoints | PASS | C11.2 |
| `C12_1_BOUNDARY` has exactly the target endpoints | PASS | C12.1 |
| `C12_2_BOUNDARY` has exactly the target endpoints | PASS | C12.2 |
| `C15_1_BOUNDARY` has exactly the target endpoints | PASS | C15.1 |
| `C15_2_BOUNDARY` has exactly the target endpoints | PASS | C15.2 |
| VT2 composite-video emitter follower is retained | PASS | exact .009 E3 sheet 2 draws R62/R63/R64, VT2, R65 and the VIDEO output; .006 is historical corroboration |
| R66 clamp input remains on the source-proved +12 V rail | PASS | sheet-2 B arrow is +12 V |
| Unsupported physical X7 is absent; VT2/R65 video node is retained | PASS | VIDEO_OUT is VT2.1/R65.1; X6 A:3 remains a target-board continuity boundary |
| Bracket X6 A:3 signal is isolated pending continuity; A:4 is ground | PASS | A:3/X6.1 electrical net open / A:4/X6.2 GND; no PCB X6 body |
| VT2/C94 owner-photo misidentification remains corrected | PASS | yellow three-lead body is VT2; separately drawn C94 retains two measurement boundaries |

## Retained target nets and boundaries

| Net | Endpoints | Source note |
| --- | --- | --- |
| `D34_SYNC` | `D34.8, R62.1` | exact .009 E3 sheet-2 frame PXL_20260718_101927794.jpg; analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out |
| `D34_SIG` | `D34.11, R63.1` | exact .009 E3 sheet-2 frame PXL_20260718_101927794.jpg; analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out |
| `VT2_BASE` | `R62.2, R63.2, R64.1, VT2.3` | exact .009 E3 sheet-2 frame PXL_20260718_101927794.jpg; analog boundary, sim-invisible |
| `VIDEO_OUT` | `R65.1, VT2.1` | exact .009 E3 sheet-2 frame PXL_20260718_101927794.jpg plus registered target-board photos: the upper owner-visible VT2 lead/pin1 shares R65.1's composite-output landing |
| `SOUND_CLAMP` | `R66.2, R67.1, VD3.2` | exact .009 E3 sheet-2 frame PXL_20260718_101927794.jpg: R66.2 joins the VD3 and R67.1 branch; physical VD3 polarity and R67.2 continuation remain open |
| `X6_A3_BOUNDARY` | `AX603.1, X6.1` | Factory .009 assembly wire table item 151 proves A:3 to bracket X6.1; independent system drawing ДГШ3.031.011 Э6 identifies X6 as the display cable; exact .009 Э3 sheet 2 labels output contact 3 VIDEO. Owner July photo PXL_20260710_200418174.jpg places A:3 braided-cable joint beside VT2/R65, separate from VD3; prior SOUND_CLAMP promotion retracted. Exact target-board copper join to VT2.1/R65.1 remains unmeasured. |
| `R67_2_BOUNDARY` | `R67.2` | .009 factory identity and owner population retain R67, but the .006 continuation into the DNP VT3/VT4 RF option is revision-superseded. Exact .009 E3 sheet-2 frame PXL_20260718_101927794.jpg draws R67.2 to VT2_BASE/R62.2/R63.2/R64.1; the target body is directly marked 4K7, differing from the exact .009 printed 2k branch. Registered July and May component views expose the R67.2 joint without onward copper; a D102-local cross-side fit projects it onto a bare backside trace corner with no via in two solder views, so the target endpoint is photo-exhausted and requires continuity |
| `C94_1_BOUNDARY` | `C94.1` | .009 sheet-1 supply detail proves C94 is a +5 V/GND bypass pair; May and July owner views show bare board at its locally projected centre, but actual C94 holes and pin1 rail remain unidentified; the previously assigned yellow body and joint belong to three-lead VT2 |
| `C94_2_BOUNDARY` | `C94.2` | .009 sheet-1 supply detail proves C94 is a +5 V/GND bypass pair; May and July owner views show bare board at its locally projected centre, but actual C94 holes and pin2 rail remain unidentified; previous C94.2/VIDEO_OUT promotion is retracted because that visible joint is VT2.1/R65.1 |
| `C9_1_BOUNDARY` | `C9.1` | .009 C9 bypass has source-proved +5 V/GND pair; pin1 rail and physical copper pending; .006 RF ground assignment revision-superseded |
| `C9_2_BOUNDARY` | `C9.2` | .009 C9 bypass has source-proved +5 V/GND pair; pin2 rail and physical copper pending; .006 RF_RAIL assignment revision-superseded |
| `C10_1_BOUNDARY` | `C10.1` | .009 C10 bypass has source-proved +5 V/GND pair; pin1 rail and physical copper pending; .006 RF_RAIL assignment revision-superseded |
| `C10_2_BOUNDARY` | `C10.2` | .009 C10 bypass has source-proved +5 V/GND pair; pin2 rail and physical copper pending; .006 VT4-base assignment revision-superseded |
| `C11_1_BOUNDARY` | `C11.1` | .009 C11 bypass has source-proved +5 V/GND pair; pin1 rail and physical copper pending; .006 RF_RAIL assignment revision-superseded |
| `C11_2_BOUNDARY` | `C11.2` | .009 C11 bypass has source-proved +5 V/GND pair; pin2 rail and physical copper pending; .006 RF tank assignment revision-superseded |
| `C12_1_BOUNDARY` | `C12.1` | .009 C12 bypass has source-proved +5 V/GND pair; pin1 rail, physical copper, and value pending; .006 RF trimmer identity revision-superseded |
| `C12_2_BOUNDARY` | `C12.2` | .009 C12 bypass has source-proved +5 V/GND pair; pin2 rail, physical copper, and value pending; .006 RF trimmer identity revision-superseded |
| `C15_1_BOUNDARY` | `C15.1` | .009 C15 bypass has source-proved +5 V/GND pair; pin1 rail and physical copper pending; .006 VT4-collector assignment revision-superseded |
| `C15_2_BOUNDARY` | `C15.2` | .009 C15 bypass has source-proved +5 V/GND pair; pin2 rail and physical copper pending; .006 VT4-emitter assignment revision-superseded |

## Interpretation

- The `.009` PCB no longer carries fifteen physically contradicted `.006` RF-only parts
  or the ten false pad-collision pairs they caused.
- VT2/R62-R67/VD3 remain the populated target analog handoff. Exact `.009`
  source frames and their limits are recorded in `docs/vt2-009-source-review.md`.
  Two overlapping July views plus an independent May angle identify the yellow
  three-lead body as
  VT2 marked `Б / 8901`; its emitter shares R65.1/VIDEO_OUT. The separately drawn
  C94 is obscured: its schematic +5 V/GND pair is proved, while its
  population, value, and individual physical pad joins require inspection.
- X6 is not evidence for the removed VT3/VT4 RF network. Its bracket cable
  reaches A:3/A:4, but A:3's prior VD3/SOUND_CLAMP photo attribution was
  rejected by the original-resolution reread. See
  `docs/x6-a3-video-source-conflict-review.md`.
- Exact `.009` sheet 2 draws VD3's cathode at SOUND_CLAMP and anode at ground.
  The current board-model diode pin names are reversed; the archived photos do
  not yet establish the cathode-band lead well enough to remap physical pads.
  See `docs/vt2-009-source-review.md` before electrical use of the sound clamp.
- Machine-readable source and population evidence is in
  `ref/photos/dgsh5-109-009-sb/rf-option-disposition.json`.
