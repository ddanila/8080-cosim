# Native semiconductor designations and pinouts

Status: **6 DESIGNATIONS / 5 PIN-NET MAPS GUARDED / VD3 POLARITY HOLD**

The native sheets and registered target bodies name the retained reset, power,
video, and beeper semiconductors. The guard checks registered designations and
pin names against the board JSON, then checks footprint names, values, and
pad/net assignments in the source PCB. All six model maps are checked; five
are source-closed and VD3 retains the explicit conflict below.
VD3's current pad numbering conflicts with the source-drawn diode polarity and
is guarded as a hold rather than claimed source-closed. The older `.006`
sheet supports designations; exact `.009 Э3` sheet 2 controls the VD3
polarity reading and is separately hash-checked.

## Command

Run from the repository root with Python 3 (standard library only).
The command overwrites this report.

```sh
python3 scripts/report_native_semiconductors.py
```

## Source-closed designations and pin maps

| Ref | Device | Package | Physical pins | PCB nets by pin |
| --- | --- | --- | --- | --- |
| `VD1` | `КД521В` | `D_DO-35_SOD27_P7.62mm_Horizontal` | 1=K, 2=A | 1=P5V, 2=RES_RC |
| `VT1` | `КТ972` | `TO-126-3_Horizontal_TabDown` | 1=E, 2=C, 3=B | 1=SND_OUT, 2=P5V, 3=SND_BASE |
| `VT2` | `КТ315` | `TO-92_Inline` | 1=E, 2=C, 3=B | 1=VIDEO_OUT, 2=P5V, 3=VT2_BASE |
| `VD4` | `КД521В` | `D_DO-35_SOD27_P7.62mm_Horizontal` | 1=K, 2=A | 1=SND_CLAMP, 2=SND_BASE |
| `VD5` | `КС147` | `D_DO-35_SOD27_P7.62mm_Horizontal` | 1=K, 2=A | 1=GND, 2=M5V_DERIVED |

## Held polarity

| Ref | Device | Current model pins | Current PCB nets | Source conflict |
| --- | --- | --- | --- | --- |
| `VD3` | `КС147Г` | 1=K, 2=A | 1=GND, 2=SOUND_CLAMP | Exact `.009 Э3` sheet 2 draws K at SOUND_CLAMP and A at GND; owner photos do not close physical pad polarity. |

## Evidence boundary

The guard verifies scan/photo hashes and selected registration metadata.
It does not reread image markings, validate footprint geometry or mounting
coordinates, measure physical continuity, or run PCB DRC.

- VT1 uses the stock horizontal TO-126 footprint because the КТ972 datasheet
  identifies the КТ-27 case and the factory mounting detail lays that body flat.
- VT2 retains the stock КТ-13 outline but replaces its generic drilled row with
  the three exact owner-photo component-side lap joints. The yellow body is visibly
  marked `Б / 8901`.
- Sheet 1 fixes VD1's cathode on +5 V
  and anode on the reset-RC junction; the May target view directly reads `КД521В`,
  with independent July coverage of the populated body.
- VD4 is independently target-photo closed as `КД521В`; the older sheet remains
  the polarity/connectivity source because it draws the clamp but omits a value.
- VD5 retains the sheet-1 `КС147` designation and derived -5 V clamp polarity.

Detailed source observations and package evidence are retained in
[the semiconductor registration](../ref/schematics/native-semiconductor-registration.json).
