# Native schematic capacitor values

Status: **3 VALUES SOURCE-CLOSED / 8 TARGET HOLDS**

The retained native circuits print three capacitor values that were blank in
the machine-readable board model. This report checksum-guards the source scans
and requires the board JSON and generated source PCB to preserve those literals.

## Command

```sh
python3 scripts/report_native_capacitor_values.py
```

## Closed values

| Ref | Board literal | Normalized | Sheet | Circuit |
| --- | ---: | ---: | ---: | --- |
| `C7` | `560` | 560 pF | 2 | D56 section-2 one-shot timing |
| `C8` | `15 нФ` | 15 nF | 2 | D56 section-1 one-shot timing |
| `C99` | `160` | 160 pF | 1 | D7/D9 decode RC path |

## Deliberate holds

| Ref | Why it remains unvalued |
| --- | --- |
| `C9` | the .009 target reuses this .006 RF-option refdes in the FDC quadrant; target value and endpoints are unread |
| `C10` | the .009 target reuses this .006 RF-option refdes in the FDC quadrant; target value and endpoints are unread |
| `C11` | the .009 target reuses this .006 RF-option refdes in the FDC quadrant; target value and endpoints are unread |
| `C12` | the .009 target refdes replaces the .006 trimmer identity; target value and endpoints are unread |
| `C15` | the .009 target reuses this .006 RF-option refdes in the FDC quadrant; target value and endpoints are unread |
| `C16` | target body reads bare 27 without a unit or decimal letter, which is incomplete under GOST 11076-69 |
| `C19` | target body reads bare 22 without a unit or decimal letter, which is incomplete under GOST 11076-69 |
| `C34` | the native sheet proves the rail endpoints but prints no value |

## Evidence boundary

- C7 and C8 are the already traced D56 one-shot timing capacitors; this
  closes their sourcing metadata without changing their endpoints.
- C99's `160` label is independent of its unresolved far plate. The value
  is promoted while `C99_FAR` remains a continuity ask.
- The eight holds are target-revision or incomplete-marking cases. Values
  from the superseded `.006` RF option are deliberately not copied into them.
