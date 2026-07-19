# D6 runnable-path diagnostic

Status: **CORRECTED TABLE MATCHES MEASURED MODE PATH**

This generated diagnostic guards the corrected 2026-07-19 D6 channel order
through the exact D6/D8 and D13/D37/D58 combinational paths. It retains the
former functional decoder only as a comparison at the RAM target.

## Reproduction

```sh
python3 scripts/report_d6_runtime_path.py
```

The test reads the validated D6 table through `decode_prom`, then follows
D6.9 through the modeled D13 Schmitt inverter and D37 NAND into D58 OE.
It also samples `decode_prom_functional` only at `B37A`. The measured
A6/A5=`/PC1,/PC0` mapping makes Port C `80` supply suffix `11`; with the
temporarily forced-low unresolved A7, the runnable row is `011`.

## Result

```text
D6-RUNTIME-LOW-ROM ba=0484 mode=011 select_and_n=0 roe_n=1 d58_oe_n=1
D6-RUNTIME-RAM ba=b37a mode=011 select_and_n=0 rev=0 roe_n=0 ram_out_en=1 d58_oe_n=0 oracle_ram_n=0 oracle_d58_oe_n=0
D6-RUNTIME-ALL-MODES ba=b37a mode=000 word=1 d6_9=0 d13_2=1 d58_9=0
D6-RUNTIME-ALL-MODES ba=b37a mode=001 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=010 word=1 d6_9=0 d13_2=1 d58_9=0
D6-RUNTIME-ALL-MODES ba=b37a mode=011 word=1 d6_9=0 d13_2=1 d58_9=0
D6-RUNTIME-ALL-MODES ba=b37a mode=100 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=101 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=110 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-ALL-MODES ba=b37a mode=111 word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-DISABLED ba=b37a word=f d6_9=1 d13_2=0 d58_9=1
D6-RUNTIME-QUALIFIER mode=011 low_ba=0484 low_word=8 low_d8=ef ram_ba=b37a ram_word=1 ram_d8=ff
D6-RUNTIME-PATH: CORRECTED TABLE MATCHES MEASURED MODE PATH
hdl/sim/d6_runtime_path_tb.v:181: $finish called at 13000 (1ps)
```

At low-ROM address `0484`, measured mode `011` emits word `8`: D6.12 sinks
and enables the D8 pager. At RAM target `B37A`, the same mode emits word `1`:
ROM releases, RAM and ROE sink, D13 output rises, and D37 enables D58. This
matches the comparison oracle without any per-output inversion. D8 is `EF`
at `0484` and `FF` at `B37A`.

## Evidence boundary

- Reader-3 socket continuity fixes D0..D3 as pins 12,11,10,9; three
  identical D6 captures include a separate power cycle.
- Chip-removed `.009` continuity proves the `.006` sheet's separate D6
  ROM/RAM outputs are real: D6.12 reaches D8.15; D6.11 does not, and the
  two socket pads are isolated. D6.11 instead reaches D2.15/-WREQ. The
  earlier installed-PROM D6.11/D6.12 joined reading is invalidated. Follow-up
  continuity proves D6.11 also reaches D92.5/R12.2 on the same -WREQ net.
- The former all-mode failure was an artifact of the old reversed channel
  packing. The corrected mode-011 row closes the observed runnable path.
- Powered-off owner continuity now confirms the entire endpoint chain:
  D6.9-D13.1, D13.2-D37.4, and D37.6-D58.9.
  The second D37 NAND input is independently source-closed by the native
  sheet-2 MEMR-D33.3/D33.4-D37.5 route; it is not a remaining probe ask.
  Live probes remain useful corroboration but no longer gate D6 adoption.
