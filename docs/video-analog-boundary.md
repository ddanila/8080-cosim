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
continuity boundary instead of inheriting the superseded `.006` RF nets. X6 likewise
remains physically present with grounded return and an unresolved signal contact.

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
| `VT2_BASE` has exactly the target endpoints | PASS | R62.2, R63.2, R64.1, VT2.2 |
| `VIDEO_OUT` has exactly the target endpoints | PASS | R65.1, VT2.1, X7.1 |
| `SOUND_CLAMP` has exactly the target endpoints | PASS | R66.2, R67.1, VD3.2 |
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
| `X6_1_BOUNDARY` has exactly the target endpoints | PASS | X6.1 |
| VT2 composite-video emitter follower is retained | PASS | the non-RF .006 path remains the closest electrical evidence for the populated .009 VT2 stage |
| R66 clamp input remains on the source-proved +12 V rail | PASS | sheet-2 B arrow is +12 V |
| X7 composite connector retains signal and ground | PASS | X7.1 VIDEO_OUT / X7.2 GND |
| X6 physical connector is retained without invented RF drive | PASS | X6.1 continuity boundary / X6.2 GND |
| Target C94 680 pF body remains modeled | PASS | .009 factory identity plus populated owner-photo 680п marking |

## Retained target nets and boundaries

| Net | Endpoints | Source note |
| --- | --- | --- |
| `D34_SYNC` | `D34.8, R62.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(9,10->8) = SYNC XOR out |
| `D34_SIG` | `D34.11, R63.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: D34 sect(12,13->11) = SIG (pixel^REV?) out |
| `VT2_BASE` | `R62.2, R63.2, R64.1, VT2.2` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible |
| `VIDEO_OUT` | `R65.1, VT2.1, X7.1` | scan sheet-2 analog corner (crops an_*); analog boundary, sim-invisible: emitter-follower composite -> contact 601; conn = X7 per СБ assembly drawing (es101_emaplaat.pdf, board 7.102.100; .158 delta possible) |
| `SOUND_CLAMP` | `R66.2, R67.1, VD3.2` | scan sheet-2 analog corner: R66.2 joins VD3.2/R67.1; R66.1 is separately source-proved on power rail B(+12); VD3 is КС147Г clamp |
| `R67_2_BOUNDARY` | `R67.2` | .009 factory identity and owner population retain R67, but the .006 continuation into the DNP VT3/VT4 RF option is revision-superseded; target endpoint requires continuity |
| `C94_1_BOUNDARY` | `C94.1` | .009 factory assembly drawing plus registered owner component photo prove populated C94 (680п) in the analog/FDC area below D102; lead 1 remains an explicit continuity boundary because its destination is not readable through the component/fanout cluster |
| `C94_2_BOUNDARY` | `C94.2` | .009 factory assembly drawing plus registered owner component photo prove populated C94 (680п) in the analog/FDC area below D102; lead 2 remains an explicit continuity boundary because its destination is not readable through the component/fanout cluster |
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
| `X6_1_BOUNDARY` | `X6.1` | .009 factory assembly and owner photo retain physical X6/contact 701, but the .006 VT3/VT4 RF source is DNP on the target; signal destination requires target continuity |

## Interpretation

- The `.009` PCB no longer carries fifteen physically contradicted `.006` RF-only parts
  or the ten false pad-collision pairs they caused.
- VT2/R62-R67/VD3/C94/X7 remain the populated target analog handoff. Their precise
  amplitudes, values, and unresolved endpoints still require continuity or bench capture.
- No RF behavior is claimed for X6 until target-revision circuitry is proved; preserving
  a physical connector is not evidence for the removed VT3/VT4 network.
- Machine-readable source and population evidence is in
  `ref/photos/dgsh5-109-009-sb/rf-option-disposition.json`.
