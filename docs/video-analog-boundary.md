# Video analog boundary

Status: **.009 COMPOSITE HANDOFF GUARDED / .006 RF OPTION DNP**

Exact `.009` Э3 sheet 2 records the VT2 composite-video stage. Its
factory placement and owner-photo evidence omit the older `.006` VT3/VT4
RF option. C9/C10/C11/C12/C15 are reused `.009` bypass identities;
their physical pad-to-rail assignments remain open. C94 has a source-proved
+5 V/GND pair with body and pad mapping unresolved.

D37.11–D34.12 is source-traced and photo-supported; owner electrical
continuity remains unmeasured. Its image controls are preserved in the
[D34 via review](../ref/photos/juku-pcb-2/d34-pin12-video-via-review.json).

## Command

Run from the repository root with Python 3 (standard library only).
The writer reads `kicad/juku.board.json`,
[the revision disposition](../ref/photos/dgsh5-109-009-sb/rf-option-disposition.json)
and [the C94/VT2 registration](../ref/photos/juku-pcb-2/c94-endpoint-registration.json).
The disposition lists the schematic, BOM, assembly and owner files
whose paths must exist. The command replaces this report with its check results
and exits with status 1 if any listed check fails.

```sh
python3 scripts/report_video_analog_boundary.py
```

## Revision checks

| Check | Result | Evidence |
| --- | --- | --- |
| All listed cross-revision evidence paths exist | PASS | 24 schematic/BOM/factory/owner artifacts |
| Legacy .006 RF-only population is absent from the .009 board model | PASS | C13, C14, L1, R68, R69, R70, R71, R72, R73, R74, R75, R76, R77, VT3, VT4 |
| Legacy RF net names are retired | PASS | HF_OUT, RF_RAIL, RF_TANK, RF_TAP, SND_MIX, VT3_BASE, VT3_E, VT4_B, VT4_C, VT4_E |
| Factory-reused C9/C10/C11/C12/C15 remain generic capacitors | PASS | physical .009 identities retained; .006 RF assignments not carried across |
| Exact .009 source proves reused capacitors' +5 V/GND pair while pad polarity stays open | PASS | sheet-1 C9...C12/C15 bypass group; physical pad mapping pending |
| `VID_MIX1` has exactly the target endpoints | PASS | D34.12, D37.11 |
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
| VT2 photo registration and unresolved C94 model remain distinct | PASS | yellow three-lead body is VT2; separately drawn C94 retains two measurement boundaries |

Per-net provenance is retained in [the board model](../kicad/juku.board.json).

## Interpretation

- This guard checks source-model endpoints, revision/population metadata
  and evidence-path existence. It does not hash or inspect those images,
  validate routed copper, simulate loaded output voltage or measure hardware.
- VT2/R62-R67/VD3 form the retained analog handoff. The
  [VT2 source review](vt2-009-source-review.md) records body identification,
  values, pin mapping and electrical limits.
- Bracket X6 connects through A:3/A:4. A:4 is ground; A:3 remains isolated
  pending its target-board connection to VIDEO_OUT. See the
  [X6 review](x6-a3-video-source-conflict-review.md).
- VD3's schematic cathode is at SOUND_CLAMP and its anode at ground.
  The board-model diode pin names are reversed; photos do not establish
  the cathode-band lead sufficiently to remap physical pads. This remains
  an electrical-use boundary.
- C94 population, value and pad joins remain open. R67.2's target-board
  continuation and the reused bypass pad mappings also require confirmation.
- [Revision evidence](../ref/photos/dgsh5-109-009-sb/rf-option-disposition.json)
  preserves source identities and the `.006` RF population exclusion.
