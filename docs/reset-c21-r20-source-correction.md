# Reset C21/R20 source and owner correction

The exact `.009` sheet-1 reset detail in
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101801729.jpg`, native crop
`(780,1740)–(1850,2600)`, draws **C21=24 in series with R20=1,5к**. A filled
junction after R4 feeds D13.5 and one plate of C21. The other C21 plate joins
R20; R20's far lead descends to a remote continuation. The former model put
R20 directly between RESIN and +5 V and C21 directly between RESIN and ground.
Those two parallel branches contradicted the exact drawing.

The assembly `PXL_20260711_114604420.jpg` labels vertical C21 below R20 and
left of **D52**. The July owner component image `PXL_20260710_200450127.jpg`
shows the matching green C21 body beside the marked К555КП14 D52. The owner
solder image `PXL_20260710_200537608.jpg` shows D52's two eight-contact rows.
The D52-local reflected fit maps C21's lower physical lead near front
`(1740,1530)` to solder `(2381,1447)`, within about 8 pixels of the joint
`(2380,1440)` on the separate R4-right trace. The upper C21 lead visibly joins
the lower lead of the R20-position red body on front copper. This matches the
source series branch. R4-right-to-D13.5 remote continuity and the far R20
return remain to be checked on the board.

The source model and unrouted source PCB now carry `RESIN` at R4.2/C21.1/D13.5,
`C21_R20_SERIES` at C21.2/R20.1, and a one-pad
`R20_RETURN_SOURCE_HOLD` at R20.2. The last name marks an unresolved source
continuation; it is not a claim that the original board has an open resistor.
The generated connectivity schematic uses the same three nets.

The routed and candidate PCBs still have the former C21 and R20 pad nets and
tracks built for the parallel interpretation. They require a copper-aware
correction and fresh DRC before fabrication. Relabelling those pads alone
would leave the old copper attached to ground, +5 V, and RESIN. The fitted C21
value and physical hole spacing also remain unmeasured.

Photo coordinates, hashes, fit anchors, and contact limits are in
`ref/photos/juku-pcb-2/c21-r4-crossview-review.json`.
