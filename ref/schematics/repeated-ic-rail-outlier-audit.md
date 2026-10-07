# Repeated-IC rail outliers in the .009 reconstruction

The cohort comparison found four instances whose pin was on a
power net for several same-type peers but not for the instance listed here.
This is a screening result only: functional inputs may legitimately be held
high or low. The physical package supply pins must be checked separately.

| Instance and screened pin | Drawing/model reading | Disposition |
| --- | --- | --- |
| D52.8, D52.16 | The exact .009 sheet-2 microcircuit power table gives К531КП14 pin 8 to ground and pin 16 to +5 V. D48–D51 already have those assignments. | Package supplies modeled in `kicad/juku.board.json` and PCB pad nets; routed track endpoints remain absent. See [d52-supply-pin-correction.json](d52-supply-pin-correction.json). |
| D25.11 | The VABUS turnaround `T` signal belongs to `D25_T`; sheet reconstruction traces its D7.6 branch. Other VABUS instances may tie this functional input high. | Do not add D25.11 to +5 V. |
| D106.5 | `UP` input of the IE7 counter; exact FDC recovery-counter reconstruction groups it with R78.1 and preset-high inputs on `D106_PRESET_HIGH`. Other counters may directly tie their `UP` input high. | Do not merge D106.5 with +5 V without proving the resistor topology. |
| D99.3 | `/CLR1` functional input of the AG3 one-shot. Registered owner component copper ties it to D96.7 ground; its `GND` net assignment is already present. Other AG3 clear inputs differ. | No missing supply pin; keep D99.3 on GND. |

References: [exact sheet-2 power table](../photos/dgsh5-109-009-e3/PXL_20260718_101927794.jpg),
[board fidelity ledger](../../docs/board-fidelity-gap-ledger.md),
[FDC recovery counter](fdc-recovery-counter-map.md),
[D99 constraints](../../docs/d99-reconstruction-constraints.md), and
[D41 supply review](../photos/juku-pcb-2/d41-supply-pin-review.json) for the
separate D41 package-supply omission.

## Single-instance and one-rail follow-up

D8, D92, D2, and D34 have their package-supply nodes modeled in JSON
and labeled in the PCB. The supporting records are
[d8-d92-supply-pin-correction.json](d8-d92-supply-pin-correction.json), [d2-package-supply-correction.json](d2-package-supply-correction.json),
and [d34-package-supply-correction.json](d34-package-supply-correction.json); the latter cites the exact-device
PDF for D34 К555ЛП5 pins 7/14. None of these
eight pads has a touching power track in the unrouted source PCB. The other one-rail classes
from this screen have explicit
different arrangements: the 32 РУ5 DRAM packages use `RAIL_G`/`RAIL_H`
for their supply options as well as GND, while D14/D32 АП2 use ±12 V and
GND. This is an inventory screen, not a complete chip-by-chip power-table
certification.

D104 illustrates the limit: it already has +5 V and GND modeled, yet the
preserved К170УП2 contract calls pin16 a +12 V supply while the exact .009
power table leaves its +12 V cell blank. The owner connection is still open;
see [d104-pin16-rail-conflict.json](d104-pin16-rail-conflict.json). Do not add that rail from a generic
pinout until the target hardware or a stronger factory source resolves it.

## Source-PCB package-pad screen

The checker selects numeric-D footprints with 14 or 16 distinct pad numbers
and checks positions 7/14 or 8/16 respectively. These positions have net
names in the source PCB except `D104.16`.
This screen checks pad ownership, not supply voltage, actual copper,
or whether these generic positions are the supply pins on every device.
The exact sheet-1 and sheet-2 power-table audits check the represented
device-specific rail assignments separately. D104.16 remains the one
unassigned package pad identified by this screen, with its source conflict
and owner-continuity requirement above.

The checker also looks for a same-net track endpoint exactly at each pad
centre in both routed variants. Each variant has five named supply pads without
such an endpoint: both pins of D2 and D52, plus D8.16.
This is an endpoint screen, not a geometric proof of all copper connectivity;
KiCad DRC still holds the boards for other gaps.

Run from the repository root with KiCad’s `pcbnew` available to Python.
The system Python below provides it on the documented Linux setup; adjust
the interpreter path for your KiCad installation:

```sh
/usr/bin/python3 kicad/check_package_rail_pad_coverage.py
```

The command is read-only and exits 0 when the unassigned-pad and
missing-endpoint sets match the recorded holds, or 1 when they differ.
The printed 14/16-pad footprint counts are informational, not fixed-count gates. A passing result means those sets match; it does not mean all power
connections are complete. Vias, zones, tracks passing through a pad, and
pad-edge connections are outside this endpoint test.
