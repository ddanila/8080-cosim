# Repeated-IC rail outliers in the .009 reconstruction

The cohort comparison found four instances whose pin was on a
power net for several same-type peers but not for the instance listed here.
This is a screening result only: functional inputs may legitimately be held
high or low. The physical package supply pins must be checked separately.

| Instance and screened pin | Drawing/model reading | Disposition |
| --- | --- | --- |
| D52.8, D52.16 | The exact .009 sheet-2 microcircuit power table gives К531КП14 pin 8 to ground and pin 16 to +5 V. D48–D51 already have those assignments. | Genuine omitted package supply nets. Modeled in `kicad/juku.board.json` and PCB pad nets; routed track endpoints remain absent. See `d52-supply-pin-correction.json`. |
| D25.11 | The VABUS turnaround `T` signal belongs to `D25_T`; sheet reconstruction traces its D7.6 branch. Other VABUS instances may tie this functional input high. | Do not add D25.11 to +5 V. |
| D106.5 | `UP` input of the IE7 counter; exact FDC recovery-counter reconstruction groups it with R78.1 and preset-high inputs on `D106_PRESET_HIGH`. Other counters may directly tie their `UP` input high. | Do not merge D106.5 with +5 V without proving the resistor topology. |
| D99.3 | `/CLR1` functional input of the AG3 one-shot. Registered owner component copper ties it to D96.7 ground; its `GND` net assignment is already present. Other AG3 clear inputs differ. | No missing supply pin; keep D99.3 on GND. |

References: `PXL_20260718_101927794.jpg` in
`ref/photos/dgsh5-109-009-e3/`; `docs/board-fidelity-gap-ledger.md`;
`ref/schematics/fdc-recovery-counter-map.md`;
`docs/d99-reconstruction-constraints.md`; and
`ref/photos/juku-pcb-2/d41-supply-pin-review.json` for the separate D41
package-supply omission.

## Single-instance and one-rail follow-up

The same net inventory exposed D8 and D92 with no package-supply nodes,
and D2 with only two grounded chip-enable inputs. Their missing package
pins are now modeled and PCB pad-labeled; see
`d8-d92-supply-pin-correction.json` and
`d2-package-supply-correction.json`. A follow-up canonical-pin check found
D34 К555ЛП5 with logic-input rail ties but no package pin7/14 supply;
the exact-device PDF confirms the omission, now corrected in the model
and PCB pad labels (`d34-package-supply-correction.json`). None of these
eight pads has a touching power track in the unrouted source PCB. The other one-rail classes
from this screen have explicit
different arrangements: the 32 РУ5 DRAM packages use `RAIL_G`/`RAIL_H`
for their supply options as well as GND, while D14/D32 АП2 use ±12 V and
GND. This is an inventory screen, not a complete chip-by-chip power-table
certification.

D104 illustrates the limit: it already has +5 V and GND modeled, yet the
preserved К170УП2 contract calls pin16 a +12 V supply while the exact .009
power table leaves its +12 V cell blank. The owner connection is still open;
see `d104-pin16-rail-conflict.json`. Do not add that rail from a generic
pinout until the target hardware or a stronger factory source resolves it.

## Source-PCB package-pad screen

The current source PCB has 19 numeric-D footprints
with 14 pads and 58 with 16 pads. For the 14-pad group, both pads 7/14 have
net names; for the 16-pad group, both pads 8/16 have net names except
`D104.16`. This screen checks pad ownership, not supply voltage, actual copper,
or whether these generic positions are the supply pins on every device.
The exact sheet-1 and sheet-2 power-table audits check the represented
device-specific rail assignments separately. D104.16 remains the one
unassigned package pad identified by this screen, with its source conflict
and owner-continuity requirement above.

The checker also looks for a same-net track endpoint exactly at each pad
centre in both routed variants. Each variant has five named supply pads without
such an endpoint: both pins of D2 and D52, plus D8.16. The source PCB
remains unrouted at the newly connected routed-board pads too.
This is an endpoint screen, not a geometric proof of all copper connectivity;
KiCad DRC still holds the boards for other gaps.

Run from the repository root with KiCad’s `pcbnew` available to Python.
The system Python below provides it on the documented Linux setup; adjust
the interpreter path for your KiCad installation:

```sh
/usr/bin/python3 kicad/check_package_rail_pad_coverage.py
```

It compares the unassigned pad and missing-endpoint sets with the recorded
holds. A passing result means those sets match; it does not mean all power
connections are complete. Vias, zones, tracks passing through a pad, and
pad-edge connections are outside this endpoint test.
