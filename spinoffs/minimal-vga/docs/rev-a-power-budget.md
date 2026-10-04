# Rev A Power Budget

Status: **PLANNING ESTIMATE / DESIGN HOLD**.

This is a +5 V planning allowance for the input fuse and supply path, pending
exact socketed-part selection and measured current. The rows are budgeting
assumptions, not a parts-count audit or measured load. Their 1.812 A sum is
rounded to **1.81 A** for the fuse checks.

## Assumptions

- Supply rail: +5 V only after F1.
- CPU: real DIP Z80, budgeted as an NMOS Z0840004-class part.
- DRAM: eight 4164-compatible 64K x 1 DIP parts.
- ROM: U2 uses the 28C256 pin contract. Any alternate EPROM requires the
  compatibility review described in the [chip map](rev-a-chip-map.md).
- PPI: 82C55/8255-compatible DIP.
- GALs: two GAL22V10-class DIP devices.
- Decode PROMs (when fitted): the two original Juku **bipolar** PROMs — U3
  К556РТ4 (256×4) and U4 К155РЕ3 (32×8). Bipolar fusible-link PROMs draw far
  more than the CMOS parts: budget ~130 mA each. They are socketed and only
  powered whenever inserted, regardless of the decode-mode jumper. The western
  baseline has both sockets empty; a Mode A D8 observation test still adds its
  fitted PROM load.
- Mode-bit inverter: one 74HC04 (U6), negligible CMOS load.
- VGA output: worst case assumes RGB outputs can source current through the
  series resistors into a 75 ohm monitor load.
- LEDs: six diagnostics through 2.2k class resistors, so LED current is small.

## Estimated +5 V Current

| Block | Qty | Budget each | Budget total |
| --- | ---: | ---: | ---: |
| Z80 CPU | 1 | 200 mA | 200 mA |
| 4164 DRAM | 8 | 75 mA | 600 mA |
| U2 ROM (28C256 pin contract; planning allowance) | 1 | 50 mA | 50 mA |
| 82C55/8255 PPI | 1 | 100 mA | 100 mA |
| GAL22V10 | 2 | 90 mA | 180 mA |
| 74HCT/HC glue logic (incl. U6 inverter) | 10 | 10 mA | 100 mA |
| Bipolar decode PROMs U3 РТ4 + U4 РЕ3 (both fitted) | 2 | 130 mA | 260 mA |
| Oscillator | 1 | 25 mA | 25 mA |
| Reset supervisor and pullups | 1 | 5 mA | 5 mA |
| Diagnostic LEDs | 6 | 2 mA | 12 mA |
| VGA RGB load | 3 | 10 mA | 30 mA |
| Margin / sourcing variation | - | - | 250 mA |
| **Total planning budget (both PROMs fitted)** |  |  | **1.81 A** |

## Fuse Choice

Rev A currently uses `F1` as a resettable PTC fuse between `VCC_RAW` and `VCC`.
The assigned candidate is Bourns `MF-RG300-0-14` / JLCPCB `C3761779`, matching
the current Bourns MF-RG300 footprint. Its preserved manufacturer datasheet and
committed fit are guarded by `rev-a-ptc-candidate.md`.

- Maximum voltage: 16 V.
- Hold current: 3.0 A at 23 C.
- Trip current: 5.1 A at 23 C.
- Thermal derating: 2.6 A at 40 C and 2.1 A at 60 C.
- Role on Rev A: gross short / wiring fault protection, not precise load
  limiting.

With both PROMs fitted, the recorded hold-current/budget ratios are 1.66x at
23 C, 1.44x at 40 C and 1.16x at 60 C. With both sockets empty, the planning
budget is about 1.55 A; each fitted PROM adds about 130 mA regardless of Mode A/B.
These ratios do not qualify nuisance-trip behavior or fault clearing. Final IC
loads, source capability, trace/connector ratings and board temperature remain
physical acceptance requirements. Include C26/C27 and socket contacts in the
review before testing the bipolar PROMs.

USB-C is kept as a convenience 5 V input. Without PD/current negotiation, do not
assume it can supply the full planning budget from every host/charger. The screw
terminal / bench supply path remains the safer primary bring-up input.

## Software check

Run from the repository root with KiCad's Python (`pcbnew`):

```sh
. spinoffs/minimal-vga/kicad/revb/env.sh
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/report_rev_a_power_budget.py
```

This writes `fab/minimal-vga/power-budget-readiness.md`. Its `READY` status
checks the fixed 1.81 A allowance and required documentation phrases, F1's BOM
identity and footprint, selected power-entry pad nets, and the room-temperature
hold-current ratio. It does not sum the table, derive part currents from
population/datasheets, solve routed voltage drop or test fuse response.
The separate [PTC candidate guard](rev-a-ptc-candidate.md) checks preserved
part evidence and fit; physical qualification and design release remain open.
