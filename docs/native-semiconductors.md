# Native semiconductor designations and pinouts

Status: **3 DESIGNATIONS + 2 TRANSISTOR PINOUTS SOURCE-CLOSED / VD4 HELD**

The native sheet names the retained video and beeper semiconductors. This guard
keeps those markings, the physical E-C-B transistor lead order, the KT-27/KT-13
package choices, and every generated PCB pad/net assignment synchronized.

## Command

```sh
python3 scripts/report_native_semiconductors.py
```

## Closed devices

| Ref | Device | Package | Physical pins | PCB nets by pin |
| --- | --- | --- | --- | --- |
| `VT1` | `КТ972` | `TO-126-3_Horizontal_TabDown` | 1=E, 2=C, 3=B | 1=SND_OUT, 2=P5V, 3=SND_BASE |
| `VT2` | `КТ315` | `TO-92_Inline` | 1=E, 2=C, 3=B | 1=VIDEO_OUT, 2=P5V, 3=VT2_BASE |
| `VD3` | `КС147Г` | `D_DO-35_SOD27_P7.62mm_Horizontal` | 1=K, 2=A | 1=GND, 2=SOUND_CLAMP |

## Evidence boundary

- VT1 uses the stock horizontal TO-126 footprint because the КТ972 datasheet
  identifies the КТ-27 case and the factory mounting detail lays that body flat.
- VT2 retains the stock КТ-13 outline but replaces its generic drilled row with
  the three exact owner-photo component-side lap joints. The yellow body is visibly
  marked `Б / 8901`; it was formerly misidentified as C94.
- VD4 remains deliberately blank: neither the retained sheet nor current owner
  imagery closes an exact designation.
