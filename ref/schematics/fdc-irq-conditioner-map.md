# FDC DRQ/INTRQ conditioner map

Full-resolution `ДГШ5.109.009 Э3` sheet 3 draws the
fifth and sixth D28 open-collector inverters and the second half of D96.
The unambiguous local circuit is:

| Function | Exact sheet-3 endpoints |
| --- | --- |
| raw DRQ | D93.38 → D28.11 |
| raw INTRQ | D93.39 → D28.13 and R93.1; R93 `10к` to +5 V |
| wired conditioner | D28.10 + D28.12 → D96.10 `/PRE2` + D96.12 `D2` and R95.1; R95 `2к` to +5 V |
| downstream timing | Full sheet-3 overview joins D96.11 `CLK2` to D94.2/D99.9/R89.1; physical D96.11 continuity pending |
| conditioned output | D96.9 `Q2` runs to the common D101 A0–A3 input conductor in the full sheet-3 overview; target continuity pending |
| section-2 clear | D96.13 `/CLR2` joins D99.10 `B2` at a marked junction and continues to sheet 1; remote source unresolved |

The electrical drawing labels a second `10к` pull-up on raw DRQ as `R94`.
Owner inspection and continuity on 2026-07-20 confirm that drawing: physical
R94 is immediately above D28, with one side on D28.11/D93.38 and the other on
+5 V. Its body may be hidden by the video cable. The previously photographed
`220`-ohm body below-left of D98 is therefore not R94; its identity and both
endpoints remain unassigned, and its retained photo record is explicitly
marked superseded rather than discarded. The board JSON, KiCad source, HDL,
and routed PCB now carry the corrected 10k R94 pull-up plus a
separate `RUNK1` 220-ohm physical placeholder with two measurement boundaries.

The earlier direct D93.38/.39-to-D10.19/.18 assignment came from MAME and is
now retired. D10 IR0/IR1 remain explicit boundaries until owner continuity
identifies their actual joins. Registered component and solder views fix the
D96.9/.11 pad locations and show that
D96.9 has no exposed local B.Cu departure. A later D96.11 solder review
finds a conditional route toward D28.11/DRQ, conflicting with the separate
source nets; direct continuity must resolve it before either net is changed.
That exhausted photo chase is recorded in
`ref/photos/juku-pcb-2/d96-irq-photo-exhaustion.json`.

The nearby continuation annotations include distinct plain/primed variants.
They are drawing cross-references, not logic-high labels, and repeated-looking
marks do not justify joining unrelated arrows. The overview supplies a
continuous drawn path from D96.9 to D101 A0, independent of those annotations;
D96.11's drawn source is D94.2, while its target-board continuity remains
unmeasured. See `docs/d96-clock2-source-review.md`.

## Device-logic contradiction

The primary SN74LS74A truth table does not support calling the locally drawn
D96 half a complete conditioner. Because D96.10 `/PRE2` and D96.12 D2 share
the same node, a low node asynchronously sets Q2 and a rising CLK2 edge while
the node is high samples D2=1. Once set, Q2 cannot return low through either
documented input. Only `/CLR2` can clear it. Sheet 3 joins pin13 to D99.10,
but their remote clear source is unread. Direct continuity of pins9, 11,
and 13 plus a powered capture of
pins8-13 is therefore required. The exact board transcription remains intact;
no missing clear net is inferred from the functional contradiction.

Guard:

```sh
python3 kicad/check_d93_irq_conditioner.py
sync/d96_check.sh
```
