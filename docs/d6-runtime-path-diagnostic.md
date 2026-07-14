# D6 runnable-path diagnostic

Status: **ALL RAW A7..A5 ROWS EXHAUSTED AT THE RAM GATE BOUNDARY**

This generated diagnostic preserves the exact combinational failure found
while testing whether the runnable boot could use D6 `.038` directly. It is
not a replacement memory decoder and does not bless the compatibility oracle.
It exhaustively proves that changing the three D6 mode inputs cannot repair
the observed RAM-read failure at the first checkpoint call target, then
identifies the first address-sensitive physical distinction downstream.

## Reproduction

```sh
python3 scripts/report_d6_runtime_path.py
```

The test reads the validated D6 table through `decode_prom`, then follows
D6.9 through the modeled D13 Schmitt inverter and D37 NAND into D58 OE.
It also samples `decode_prom_functional` only to state the established
runnable behavior at the same addresses. The test then evaluates all eight
raw D6 A7..A5 combinations at `B37A` against the four-bit PROM word. The
raw row `000` is retained as a table-coordinate regression. New `.009`
continuity proves A6/A5=`/PC1,/PC0`, so Port C `80` supplies suffix `11`;
A7 remains unknown. The exhaustive B37A result, not row `000` alone, is
the applicable checkpoint guard.

## Result

```text
D6-RUNTIME-LOW-ROM ba=0484 mode=000 select_and_n=0 roe_n=1 d58_oe_n=1
D6-RUNTIME-RAM ba=b37a mode=000 select_and_n=0 rev=0 roe_n=1 ram_out_en=0 d58_oe_n=1 oracle_ram_n=0 oracle_d58_oe_n=0
D6-RUNTIME-ALL-MODES ba=b37a mode=000 word=8 d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=001 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=010 word=8 d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=011 word=8 d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=100 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=101 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=110 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=111 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-DISABLED ba=b37a word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-QUALIFIER mode=000 low_ba=0484 low_word=8 low_d8=ef ram_ba=b37a ram_word=8 ram_d8=ff
D6-RUNTIME-PATH: BOUNDARY REPRODUCED (all physical modes block D58 at B37A)
hdl/sim/d6_runtime_path_tb.v:188: $finish called at 13000 (1ps)
```

At low-ROM address `0484`, raw row `000` emits word `8`, leaving D58
released while the separate D6.12 ROM output enables the D8 pager. At RAM call target
`B37A`, mode `000` emits word `8`. Exhaustive evaluation shows words `8`
or `F` in every possible mode; both leave physical D6.9 high. Disabling the
PROM would also release pin 9 high. The currently traced D13/D37 polarity
therefore keeps D58 OE high regardless of A5/A6/A7 or the unresolved V1/V2
feed. The checkpoint-resume
experiment consequently consumed `FF` at the RAM call and never reached the
PIC/keyboard boundary. Restoring the explicit oracle returned the guard to
`PASS` at 25,744 resumed machine cycles.

The earlier row-`000` comparison is no longer an inferred checkpoint mode:
the measured D3 routes place the checkpoint on suffix `11`, with A7 still
unknown. D8 remains `EF` at `0484` and `FF` at `B37A`, but that distinction
must not be used to invent a feedback branch. Every D8 output currently has
exactly one modeled peer, its corresponding D15-D22 socket CE.

## Evidence boundary

- The RT4 reader wiring and repeated table are guarded independently; this
  result is not evidence to reorder or complement the dump.
- Chip-removed `.009` continuity proves the `.006` sheet's separate D6
  ROM/RAM outputs are real: D6.12 reaches D8.15; D6.11 does not, and the
  two socket pads are isolated. D6.11 instead reaches D2.15/-WREQ. The
  earlier installed-PROM joined reading is invalidated; the older-sheet
  D92.5/R12.2 RAM branch now requires its actual target-board driver.
- Mode selection and the D6 enable feed are now excluded as explanations for
  the `B37A` D6.9 level: no physical row can pull pin 9 low there. The remaining
  contradiction is in endpoint assignment, downstream polarity/function, or
  the assumption that this RAM read reaches DB through D58.
- Raw row `000` emits word `8` at both `0484` and `B37A`, but it is not
  identified as the checkpoint row after the measured D3 correction. The
  actual suffix is `11`; both possible A7 rows still leave D6.9 high at
  `B37A`, so the RAM-gate failure remains valid while A7 is unresolved.
- Powered-off owner continuity now confirms D6.9-D13.1 and D13.2-D37.4.
  The decisive remaining downstream check is D37.6-D58.9; also find the
  target-board driver for D92.5/R12.2. Then record live D6.9, D13.2, D37.6, D58.9, and D58.11 during
  the known `B37A` RAM read. Do not infer a new net merely to make boot pass.
