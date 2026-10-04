# X6 A:3 cable and VD3 registration conflict

Exact `.009` assembly wire table `ref/schematics/dgsh5_109_009_sb_sheets2-6.pdf`, PDF page 2 / drawing sheet 3, item 151, assigns conductor 1 from board point A:3 to X6 and conductor 2 from A:4 to X6's marked return terminal. Both are 12 cm. This proves connector and cable identity, not A:3's electrical net.

## Photo registration and model

The current [cable registration](../ref/photos/juku-pcb-2/x6-cable-registration.json)
places A:3 at July component pixel `(3036,1816)` in `200418174`, beside
VT2/R65. VD3 is a distinct glass body about 400 pixels to the right; the
registration does not support identifying the A:3 joint as a VD3 lead.
That spatial separation does not rule out a remote electrical connection;
A:3-to-SOUND_CLAMP continuity remains unmeasured. The May view
`201927098` corroborates the body separation. A:4 at `(3154,1788)` appears on
a separate wide ground strip.

The D102-local transform in
[c94-endpoint-registration.json](../ref/photos/juku-pcb-2/c94-endpoint-registration.json)
places the surface joints at A:3 `(280.233,123.791)` mm and A:4
`(285.606,122.617)` mm. The source PCB represents them as AX603.1 on
`X6_A3_BOUNDARY` and AX604.1 on GND. X6 is off-board; no physical X7 is modeled.
The local VT2.1/R65.1 net remains `VIDEO_OUT`, separate from A:3 until measured.
Current routing holds and DRC totals belong in
[factory-wire fidelity](factory-wire-route-fidelity.md).

Exact `.009` Э3 sheet 2 `PXL_20260718_101927794.jpg` independently draws R67 (printed 2 kΩ) from the R66/VD3 junction to the **VT2 base / R62.2 / R63.2 / R64.1** junction. The current target model leaves R67.2 as a physical continuity boundary because its photo-supported local trace ends at an open annulus whose front-side counterpart and remote net remain unproved. The fitted body reads 4.7 kΩ rather than the printed 2 kΩ; that value difference is separate from the continuity hold.

The sheet-2 output continuation in `PXL_20260718_101932581.jpg` labels VIDEO at contact 3 / connection 601 and ground at contact 4 / connection 602. The assembly table connects A:3/A:4 to X6, and the independent system cable map (`ДГШ3.031.011 Э6`, transcribed in `ref/schematics/system-bus-connector-map.md`) identifies X6 as the two-conductor connection to display A5 МС6105.09. Together these establish X6's display-video role and make A:3 the documented video conductor and A:4 its return. They do not show the exact copper path from the photographed A:3 joint to VT2/R65. Keep A:3's target-board continuity open.

Next physical checks: A:3 to VT2 emitter, R65's two ends, VD3's two ends, and X6 center contact; A:4 to ground and X6 return. Separately confirm R67’s upper far lead at front (3365,1730) to solder joint (869,953) and the east open annulus (1295,958), then test that local route to the VT2 base/R62.2/R63.2/R64.1 junction. Keep the signal and return measurements distinct.

## Model guard

Run from the repository root with KiCad’s `pcbnew` available to Python.
The command below uses the system Python; adjust its path for your installation.

```sh
/usr/bin/python3 kicad/check_x6_offboard_landings.py
```

The guard checks source-PCB pad centres, nets, surface-pad attributes, JSON
cable endpoints, and registration mapping metadata. It does not inspect
photos, check routed variants or DRC, or measure cable continuity.
