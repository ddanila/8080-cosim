# `М75` capacitor marking at C22

The [May owner photograph](../photos/juku-pcb-2/PXL_20260519_201927098.jpg)
clearly shows `М75` on the outer C22 body (native pixel box
`[3540, 380, 3700, 700]`). The body marking is confirmed; its exact part type
and electrical performance have not been measured. The photo registration and hash are in
[the placement registration](../photos/dgsh5-109-009-sb/fdc-lower-placement-registration.json).

ГОСТ 28883-90, appendix 1, table 13 lists `М75` among the older letter codes
for ceramic capacitor *capacitance temperature-stability groups*. ГОСТ
27778-88, section 2.4.2.1, includes a nominal temperature coefficient of
`−75 × 10⁻⁶ / °C` for type-1 ceramic capacitors when specified by their
particular technical conditions. Taken together, these support interpreting a
`М75` body mark as the negative 75 ppm/°C group. The 1990 marking
standard is retrospective; it is not evidence of the board's manufacture date.

Neither standard makes `М75` a capacitance value. The May face does not resolve
the bare `22` on the later July faces into an installed unit, and it does not
establish rated voltage or measured capacitance. Keep those fields open until
a part marking or measurement closes them. For a replica, check the required
temperature coefficient when sourcing C22 after its capacitance is confirmed.

Primary sources:

- [ГОСТ 28883-90, appendix 1, table 13](https://meganorm.ru/Data2/1/4294825/4294825838.pdf)
- [ГОСТ 27778-88, section 2.4.2.1](https://files.stroyinf.ru/Data/116/11629.pdf)
