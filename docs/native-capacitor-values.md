# Native schematic capacitor values

Status: **5 PLACED VALUES SOURCE-CLOSED / 5 ADDITIONAL SOURCE NOMINALS / 11 REGISTERED TARGET HOLDS**

The retained native circuits print five registered capacitor values.
This report checksum-guards the source scans and requires the board JSON
and source PCB to preserve those literals.
C29 has a source nominal but no registered footprint or owner-board value.
Sheet 3 also supplies C16/C19/C20/C22 nominals; their installed values remain held.
Its hold list covers only the registered cases below; other unvalued capacitors
in the expanded board model are tracked in the board-fidelity ledger.

## Command

```sh
python3 scripts/report_native_capacitor_values.py
```

## Closed values

| Ref | Board literal | Normalized | Sheet | Circuit |
| --- | ---: | ---: | ---: | --- |
| `C5` | `560` | 560 pF | 2 | D34 counter-load pulse shaper |
| `C6` | `56` | 56 pF | 2 | D33 clock-gate input |
| `C7` | `560` | 560 pF | 2 | D56 section-2 one-shot timing |
| `C8` | `15 нФ` | 15 nF | 2 | D56 section-1 one-shot timing |
| `C99` | `160` | 160 pF | 1 | D7/D9 decode RC path |

## Source nominal awaiting physical registration

| Ref | Board literal | Normalized source nominal | Why the footprint is held |
| --- | ---: | ---: | --- |
| `C29` | `56` | 56 pF | Owner-board population, pad pair, and physical value unproved |

## Sheet 3 nominals with installed values held

| Ref | Sheet literal | Source nominal | Why the installed value remains held |
| --- | ---: | ---: | --- |
| `C16` | `27` | 27 pF | sheet 3 prints 27 at C16 and the owner body shows 27, but the body lacks a complete GOST unit code |
| `C19` | `22` | 22 pF | sheet 3 prints 22 at C19 and two owner angles show 22, but the body lacks a complete GOST unit code |
| `C20` | `22` | 22 pF | sheet 3 and two later owner angles both show bare 22; the former 1Н5 reading is unsupported and the installed unit remains unverified |
| `C22` | `22` | 22 pF | sheet 3 and two later owner angles both show bare 22; the former 1Н5 reading is unsupported and the installed unit remains unverified |

The former C20/C22 `1Н5` (1.5 nF) installed-value claim is retracted:
two later owner angles show bare `22` on both bodies, matching the
sheet numerals without independently proving their capacitance unit.

## Deliberate holds

| Ref | Why it remains unvalued |
| --- | --- |
| `C9` | the .009 target reuses this .006 RF-option refdes in the FDC quadrant; exact .009 sheet 1 proves a +5 V/GND bypass pair and later July owner photo 202708344 shows a green body between D100/D98 beside the cable. Its value, individual lead rails, and replica pad mapping remain open |
| `C10` | the .009 target reuses this .006 RF-option refdes in the FDC quadrant; exact .009 sheet 1 proves a +5 V/GND bypass pair and later July owner photo 202708344 shows a green body beside D93/over D106. Its value, individual lead rails, and replica pad mapping remain open |
| `C11` | the .009 target reuses this .006 RF-option refdes in the FDC quadrant; exact .009 sheet 1 proves a +5 V/GND bypass pair and later July owner photo 202708344 shows a green body between D95/D99 under the cable edge. Its value, individual lead rails, and replica pad mapping remain open |
| `C12` | the .009 target refdes replaces the .006 trimmer identity; exact .009 sheet 1 proves a +5 V/GND bypass pair. May and early July owner views show the drawn site bare, but later July photo 202708344 shows a green axial body there with visible leads to D100.20/+5 V and D94.8/GND. Its value, insertion history, and mapping to the replica's numbered through-hole pads remain open |
| `C15` | the .009 target reuses this .006 RF-option refdes in the FDC quadrant; exact .009 sheet 1 proves a +5 V/GND bypass pair and two later July views show a green body edge between D97/D102 at the factory site. The cable hides most of the body and second lead; two-lead identity, value, individual rail joins, and replica pad mapping remain open |
| `C16` | exact .009 sheet 3 specifies 27 pF nominal and the target body reads 27, but its incomplete GOST body code leaves actual installed value unproved |
| `C19` | exact .009 sheet 3 specifies 22 pF nominal and the target body reads 22, but its incomplete GOST body code leaves actual installed value unproved |
| `C20` | exact .009 sheet 3 and later owner angles both show bare 22, but no complete unit code or measurement proves installed capacitance |
| `C22` | exact .009 sheet 3 and later owner angles both show bare 22, but no complete unit code or measurement proves installed capacitance |
| `C34` | the native sheet proves the rail endpoints but prints no value |
| `C94` | the former 680 value was a misread of adjacent three-lead VT2 marked Б/8901; exact .009 sheet 1 proves C94 is a separate +5 V/GND bypass, while its physical population, value, and pad polarity remain unresolved |

## Evidence boundary

- Exact `.009` sheet 2 prints bare `560` beside C5 and bare `56` beside C6;
  the native-sheet convention interprets these as pF values.
- C7 and C8 are the already traced D56 one-shot timing capacitors; this
  closes their sourcing metadata without changing their endpoints.
- C99's `160` label and grounded far plate are both shown on exact `.009`
  sheet 1. Its physical population and pad identity still need inspection.
- Exact `.009` sheet 3 prints C16=`27` and C19/C20/C22=`22`; its bare
  values follow the native picofarad convention. Installed values need
  independent measurement or complete body markings.
- The eleven registered holds are target-revision, obscured-body, or incomplete-marking cases. Values
  from the superseded `.006` RF option are deliberately not copied into them.
