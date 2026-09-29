# Native schematic capacitor values

Status: **5 PLACED VALUES SOURCE-CLOSED / 1 SOURCE NOMINAL HELD OFF PCB / 9 REGISTERED TARGET HOLDS**

The retained native circuits print five registered capacitor values.
This report checksum-guards the source scans and requires the board JSON
and source PCB to preserve those literals.
C29 has a source nominal but no registered footprint or owner-board value.
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

## Deliberate holds

| Ref | Why it remains unvalued |
| --- | --- |
| `C9` | the .009 target reuses this .006 RF-option refdes in the FDC quadrant; exact .009 sheet 1 proves a +5 V/GND bypass pair, while the value, physical pad polarity, and cable-hidden population remain open |
| `C10` | the .009 target reuses this .006 RF-option refdes in the FDC quadrant; exact .009 sheet 1 proves a +5 V/GND bypass pair, while the value and physical pad polarity remain open |
| `C11` | the .009 target reuses this .006 RF-option refdes in the FDC quadrant; exact .009 sheet 1 proves a +5 V/GND bypass pair, while the value, physical pad polarity, and body population remain open |
| `C12` | the .009 target refdes replaces the .006 trimmer identity; exact .009 sheet 1 proves a +5 V/GND bypass pair, while the value and physical pad polarity remain open |
| `C15` | the .009 target reuses this .006 RF-option refdes in the FDC quadrant; exact .009 sheet 1 proves a +5 V/GND bypass pair, while the value and cable-obscured pad polarity remain open |
| `C16` | target body reads bare 27 without a unit or decimal letter, which is incomplete under GOST 11076-69 |
| `C19` | target body reads bare 22 without a unit or decimal letter, which is incomplete under GOST 11076-69 |
| `C34` | the native sheet proves the rail endpoints but prints no value |
| `C94` | the former 680 value was a misread of adjacent three-lead VT2 marked Б/8901; exact .009 sheet 1 proves C94 is a separate +5 V/GND bypass, while its physical population, value, and pad polarity remain unresolved |

## Evidence boundary

- Exact `.009` sheet 2 prints bare `560` beside C5 and bare `56` beside C6;
  the native-sheet convention interprets these as pF values.
- C7 and C8 are the already traced D56 one-shot timing capacitors; this
  closes their sourcing metadata without changing their endpoints.
- C99's `160` label and grounded far plate are both shown on exact `.009`
  sheet 1. Its physical population and pad identity still need inspection.
- The nine registered holds are target-revision, obscured-body, or incomplete-marking cases. Values
  from the superseded `.006` RF option are deliberately not copied into them.
