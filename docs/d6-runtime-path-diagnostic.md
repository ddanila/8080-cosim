# D6 runnable-path diagnostic

Status: **ALL PHYSICAL MODES EXHAUSTED AT THE RAM GATE BOUNDARY**

This generated diagnostic preserves the exact combinational failure found
while testing whether the runnable boot could use D6 `.038` directly. It is
not a replacement memory decoder and does not bless the compatibility oracle.
It exhaustively proves that changing the three D6 mode inputs cannot repair
the observed RAM-read failure at the first checkpoint call target.

## Reproduction

```sh
python3 scripts/report_d6_runtime_path.py
```

The test reads the validated D6 table through `decode_prom`, then follows
D6.9 through the modeled D13 Schmitt inverter and D37 NAND into D58 OE.
It also samples `decode_prom_functional` only to state the established
runnable behavior at the same addresses. The test then evaluates all eight
PC4..PC2 combinations at `B37A` against the raw four-bit PROM word.

## Result

```text
D6-RUNTIME-LOW-ROM ba=0484 mode=000 join_n=0 roe_n=1 d58_oe_n=1
D6-RUNTIME-RAM ba=b37a mode=000 join_n=0 rev=0 roe_n=1 ram_out_en=0 d58_oe_n=1 oracle_ram_n=0 oracle_d58_oe_n=0
D6-RUNTIME-ALL-MODES ba=b37a mode=000 word=8 d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=001 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=010 word=8 d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=011 word=8 d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=100 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=101 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=110 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=111 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-DISABLED ba=b37a word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-PATH: BOUNDARY REPRODUCED (all physical modes block D58 at B37A)
hdl/sim/d6_runtime_path_tb.v:160: $finish called at 11000 (1ps)
```

At low-ROM address `0484`, physical word `8` correctly leaves D58 released
while the joined D6 conductor enables the D8 pager. At RAM call target
`B37A`, mode `000` emits word `8`. Exhaustive evaluation shows words `8`
or `F` in every possible mode; both leave physical D6.9 high. Disabling the
PROM would also release pin 9 high. The currently traced D13/D37 polarity
therefore keeps D58 OE high regardless of PC2/PC3/PC4 or the unresolved V1/V2
feed. The checkpoint-resume
experiment consequently consumed `FF` at the RAM call and never reached the
PIC/keyboard boundary. Restoring the explicit oracle returned the guard to
`PASS` at 25,744 resumed machine cycles.

## Evidence boundary

- The RT4 reader wiring and repeated table are guarded independently; this
  result is not evidence to reorder or complement the dump.
- The `.006` sheet shows separate D6 ROM/RAM outputs. Direct owner continuity
  on the `.009` board instead reported D6.11, D6.12, and D13.12 joined and
  found no D8/D9 continuation. The source model currently retains older-sheet
  D8/D92 branches on that joined net, so this cross-revision contradiction
  must be resolved before the oracle can be retired.
- Mode selection and the D6 enable feed are now excluded as explanations for
  the `B37A` D6.9 level: no physical row can pull pin 9 low there. The remaining
  contradiction is in endpoint assignment, downstream polarity/function, or
  the assumption that this RAM read reaches DB through D58.
- The decisive hardware check is an isolated, powered-off resistance map with
  D6 and D13 removed: verify D6.9-D13.1, D13.2-D37.4, and D37.6-D58.9
  independently, as well as D6.11/.12 against D13.12, D8.15, D92.5, R11.2,
  and R12.2. Then record live D6.9, D13.2, D37.6, D58.9, and D58.11 during
  the known `B37A` RAM read. Do not infer a new net merely to make boot pass.
