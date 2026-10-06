# D8.16 +5 V route audit

The routed-board D8 PROM has pin 16 at `(92.222,117.118)` mm, named `P5V`
but without a same-net track/via endpoint exactly at its pad center. Both
routed variants share this finding at D8.16 and at the supply pads
`D2.8/.16` and `D52.8/.16`. Exact endpoint absence is a routing warning;
it does not test copper contact elsewhere within a pad or connectivity
through a zone.

The nearest existing P5V track/via endpoint is R12.1 at
`(73.500,104.810)` mm, 22.405 mm away. D2.16 is closer but also lacks an
exact pad-center endpoint, so a D8-to-D2 segment alone would not establish a
verified supply connection. Design the feed together with the remaining D2
supply routing and review nearby signal and ground copper before choosing a
route.

The position, net and nearest-endpoint distance come from
[the routed board](../kicad/juku_routed.kicad_pcb). They identify a routing
review area. Endpoint distance is not the shortest distance
to a copper segment and does not prove that a branch reaches the supply.
Use KiCad connectivity and DRC to verify the replica rail after repair.
These geometric observations do not prove original-board copper. Confirm
owner-board D8.16 and D2.16 to a known +5 V point with power off before
claiming physical continuity.
