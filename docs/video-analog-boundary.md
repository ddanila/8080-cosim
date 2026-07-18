# Video analog boundary

Status date: 2026-07-13.

Status: **.009 COMPOSITE HANDOFF GUARDED / .006 RF OPTION DNP**

The older `.006` electrical sheet remains useful for the populated VT2 composite-video
stage, but its dashed VT3/VT4 RF modulator is not a valid `.009` population source.
The complete `.009` factory placement views label only VT1/VT2, and the complete owner
component-side tile set corroborates that absence. The archived group BOM independently
assigns the extra RF transistors and the 4.7 kΩ adjustable trimmer to `.006`.

C9/C10/C11/C12/C15 are not removed: `.009` reuses those reference numbers around
D93-D102. Their factory positions remain on the PCB, but every pin is an explicit
continuity boundary instead of inheriting the superseded `.006` RF nets. X6 is instead
bracket-mounted: A:3/X6.1 is photo-closed to SOUND_CLAMP and A:4/X6.2 to GND.

## Command

```sh
python3 scripts/report_video_analog_boundary.py
```

## Revision checks

| Check | Result | Evidence |
| --- | --- | --- |
| All cross-revision evidence files are local | PASS | 23 schematic/BOM/factory/owner artifacts |
| Legacy .006 RF-only population is absent from the .009 board model | PASS | C13, C14, L1, R68, R69, R70, R71, R72, R73, R74, R75, R76, R77, VT3, VT4 |
| Legacy RF net names are retired | PASS | HF_OUT, RF_RAIL, RF_TANK, RF_TAP, SND_MIX, VT3_BASE, VT3_E, VT4_B, VT4_C, VT4_E |
| Factory-reused C9/C10/C11/C12/C15 remain generic capacitors | PASS | physical .009 identities retained; .006 RF assignments not carried across |
| `D34_SYNC` has exactly the target endpoints | PASS | D34.8, R62.1 |
| `D34_SIG` has exactly the target endpoints | PASS | D34.11, R63.1 |
| `VT2_BASE` has exactly the target endpoints | PASS | R62.2, R63.2, R64.1, VT2.3 |
| `VIDEO_OUT` has exactly the target endpoints | PASS | R65.1, VT2.1, X7.1 |
| `SOUND_CLAMP` has exactly the target endpoints | PASS | AX603.1, R66.2, R67.1, VD3.2, X6.1 |
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
| VT2 composite-video emitter follower is retained | PASS | the non-RF .006 path remains the closest electrical evidence for the populated .009 VT2 stage |
| R66 clamp input remains on the source-proved +12 V rail | PASS | sheet-2 B arrow is +12 V |
| X7 composite connector retains signal and ground | PASS | X7.1 VIDEO_OUT / X7.2 GND |
| Bracket X6 uses photographed A:3/A:4 cable landings | PASS | A:3/X6.1 SOUND_CLAMP / A:4/X6.2 GND; no PCB X6 body |
| VT2/C94 owner-photo misidentification remains corrected | PASS | yellow three-lead body is VT2; separately drawn C94 retains two measurement boundaries |

## Retained target nets and boundaries

| Net | Endpoints | Source note |
| --- | --- | --- |
| `D34_SYNC` | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out |
| `D34_SIG` | `D34.11, R63.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out |
| `VT2_BASE` | `R62.2, R63.2, R64.1, VT2.3` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `VIDEO_OUT` | `R65.1, VT2.1, X7.1` | scan sheet-2 analog corner plus registered target-board photos: the upper owner-visible VT2 lead/pin1 shares R65.1's composite-output landing |
| `SOUND_CLAMP` | `AX603.1, R66.2, R67.1, VD3.2, X6.1` | scan sheet-2 analog corner plus registered X6 cable joint: R66.2 joins VD3.2/R67.1; printed A:3 and its bracket X6 conductor lap-solder directly at the same VD3.2 landing |
| `R67_2_BOUNDARY` | `R67.2` | .009 factory identity and owner population retain R67, but the .006 continuation into the DNP VT3/VT4 RF option is revision-superseded. Registered July and May component views expose the R67.2 joint without onward copper; a D102-local cross-side fit projects it onto a bare backside trace corner with no via in two solder views, so the target endpoint is photo-exhausted and requires continuity |
| `C94_1_BOUNDARY` | `C94.1` | .009 factory assembly drawing identifies C94 immediately right of VT2, but the owner views do not uniquely expose its body or either lead; the previously assigned yellow body and joint belong to three-lead VT2, so C94.1 requires direct continuity |
| `C94_2_BOUNDARY` | `C94.2` | .009 factory assembly drawing identifies C94 immediately right of VT2, but the owner views do not uniquely expose its body or either lead; the previous C94.2/VIDEO_OUT promotion is retracted because that visible joint is VT2.1/R65.1 |
| `C9_1_BOUNDARY` | `C9.1` | .009 factory placement between D100 and D98; target electrical destination unread and the .006 RF ground assignment is revision-superseded |
| `C9_2_BOUNDARY` | `C9.2` | .009 factory placement between D100 and D98; target electrical destination unread and the .006 RF_RAIL assignment is revision-superseded |
| `C10_1_BOUNDARY` | `C10.1` | .009 factory placement immediately right of D93; target electrical destination unread and the .006 RF_RAIL assignment is revision-superseded |
| `C10_2_BOUNDARY` | `C10.2` | .009 factory placement immediately right of D93; target electrical destination unread and the .006 VT4-base assignment is revision-superseded |
| `C11_1_BOUNDARY` | `C11.1` | .009 factory placement between D95 and D99; target electrical destination unread and the .006 RF_RAIL assignment is revision-superseded |
| `C11_2_BOUNDARY` | `C11.2` | .009 factory placement between D95 and D99; target electrical destination unread and the .006 RF tank assignment is revision-superseded |
| `C12_1_BOUNDARY` | `C12.1` | .009 factory placement between D94 and D100; target electrical destination and value unread, and the .006 RF trimmer identity is revision-superseded |
| `C12_2_BOUNDARY` | `C12.2` | .009 factory placement between D94 and D100; target electrical destination and value unread, and the .006 RF trimmer identity is revision-superseded |
| `C15_1_BOUNDARY` | `C15.1` | .009 factory placement between D97 and D102; target electrical destination unread and the .006 VT4-collector assignment is revision-superseded |
| `C15_2_BOUNDARY` | `C15.2` | .009 factory placement between D97 and D102; target electrical destination unread and the .006 VT4-emitter assignment is revision-superseded |

## Interpretation

- The `.009` PCB no longer carries fifteen physically contradicted `.006` RF-only parts
  or the ten false pad-collision pairs they caused.
- VT2/R62-R67/VD3/X7 remain the populated target analog handoff. Two overlapping
  July views plus an independent May angle identify the yellow three-lead body as
  VT2 marked `Б / 8901`; its emitter shares R65.1/VIDEO_OUT. The separately drawn
  C94 is obscured, so its population, value, and both endpoints require inspection.
- X6 is not evidence for the removed VT3/VT4 RF network. Its target bracket cable
  instead closes directly to the retained SOUND_CLAMP/GND handoff.
- Machine-readable source and population evidence is in
  `ref/photos/dgsh5-109-009-sb/rf-option-disposition.json`.
