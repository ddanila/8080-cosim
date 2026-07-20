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
Owner inspection and continuity on 2026-07-20 confirm that drawing: physical
R94 is immediately above D28, with one side on D28.11/D93.38 and the other on
+5 V. Its body may be hidden by the video cable. The previously photographed
`220`-ohm body below-left of D98 is therefore not R94; its identity and both
endpoints remain unassigned, and its retained photo record is explicitly
marked superseded rather than discarded. The current board JSON/KiCad source
still carries the old 220-ohm/D98 assignment; correct it together with the
routed refresh rather than treating that generated net as owner evidence.

The earlier direct D93.38/.39-to-D10.19/.18 assignment came from MAME and is
now retired. D10 IR0/IR1 and the two D96 continuations remain explicit
boundaries until owner continuity identifies their actual joins. Registered
component and solder views fix the D96.9/.11 pad locations and show that
neither pad departs on B.Cu; the visible F.Cu is package/component-obscured.
That exhausted photo chase is recorded in
`ref/photos/juku-pcb-2/d96-irq-photo-exhaustion.json`.

The nearby continuation annotations include distinct plain/primed variants.
They are drawing cross-references, not logic-high labels, and repeated-looking
marks do not justify joining unrelated arrows. The recovered sheet-1 views do
not expose a unique pair for these two conductors, so no net is promoted from
the annotations alone.

Guard:

```sh
python3 kicad/check_d93_irq_conditioner.py
```
