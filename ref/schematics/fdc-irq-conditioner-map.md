# FDC DRQ/INTRQ conditioner map

Full-resolution `ДГШ5.109.009 Э3` sheet 3 draws the previously omitted
fifth and sixth D28 open-collector inverters and the second half of D96.
The unambiguous local circuit is:

| Function | Exact sheet-3 endpoints |
| --- | --- |
| raw DRQ | D93.38 → D28.11 |
| raw INTRQ | D93.39 → D28.13 and R93.1; R93 `10к` to +5 V |
| wired conditioner | D28.10 + D28.12 → D96.10 `/PRE2` + D96.12 `D2` and R95.1; R95 `2к` to +5 V |
| downstream timing | D96.11 `CLK2` leaves through a sheet-1 continuation |
| conditioned output | D96.9 `Q2` leaves through a different sheet-1 continuation |
| unused pin | D96.13 `/CLR2` is drawn without a connection |

The electrical drawing labels a second `10к` pull-up on raw DRQ as `R94`.
That branch is not imported: registered target-board imagery and continuity
prove physical R94 is the separate `220`-ohm part on D98.3. This is another
internal electrical-drawing reference conflict, not permission to duplicate
R94 or overwrite target-board evidence.

The earlier direct D93.38/.39-to-D10.19/.18 assignment came from MAME and is
now retired. D10 IR0/IR1 and the two D96 sheet-1 continuations remain explicit
boundaries until sheet 1 or owner continuity identifies their actual joins.

The `(1)`/`"1"` annotations at continuation arrows mean “sheet 1.” They do not
mean logic high and do not join unrelated arrows carrying the same annotation.

Guard:

```sh
python3 kicad/check_d93_irq_conditioner.py
```
