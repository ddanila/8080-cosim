# R49-R56 RAS resistor bank

Status: **PLACEMENT / VALUES CLOSED**

The `.006` assembly drawing fixes the bank/refdes order. Registered target-board
component views show the same eight populated vertical bodies, while the reflected
solder panorama corroborates the drilled column. The red bodies directly read `75Ω`
and the tan bodies directly read `5K1`. The source model encodes R49-R52
as 75 Ω and R53-R56 as 5.1 kΩ.

## Command

Run from the repository root with Python 3 (standard library only).
The command replaces this report with the registered-evidence check results,
then exits nonzero if any check fails.

```sh
python3 scripts/report_ras_resistor_bank.py
```

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| All registered sources match SHA256 | PASS | 6 drawing/photo artifacts |
| Drawing refdes order matches the target photo column | PASS | R56/R52, R55/R51, R54/R50, R53/R49 |
| Registered geometry is the vertical 10.16 mm bank | PASS | x=221.0 mm; eight independently recorded centres |
| Target case markings are encoded as values | PASS | R49-R52=75 Ω; R53-R56=5.1 kΩ |
| Board provenance cites the target-board registration | PASS | all eight board-JSON components |
| PCB generator text contains the registered placements and footprint | PASS | registered footprint name and coordinates |

## Registered top-to-bottom order

| Order | Ref | Centre (mm) | Orientation | Lead span | Marking | Encoded value | Role |
| ---: | --- | --- | ---: | ---: | --- | --- | --- |
| 1 | R56 | 221.0, 135.2 | 90° | 10.16 mm | 5K1 | 5,1к | RAS termination to GND |
| 2 | R52 | 221.0, 150.0 | 90° | 10.16 mm | 75Ω | 75 | D53 series output |
| 3 | R55 | 221.0, 162.2 | 90° | 10.16 mm | 5K1 | 5,1к | RAS termination to GND |
| 4 | R51 | 221.0, 175.2 | 90° | 10.16 mm | 75Ω | 75 | D53 series output |
| 5 | R54 | 221.0, 189.0 | 90° | 10.16 mm | 5K1 | 5,1к | RAS termination to GND |
| 6 | R50 | 221.0, 201.5 | 90° | 10.16 mm | 75Ω | 75 | D53 series output |
| 7 | R53 | 221.0, 215.2 | 90° | 10.16 mm | 5K1 | 5,1к | RAS termination to GND |
| 8 | R49 | 221.0, 229.7 | 90° | 10.16 mm | 75Ω | 75 | D53 series output |

## Scope

This guard validates the registered source hashes, recorded order/geometry,
board values and provenance markers, and selected PCB-generator text.
It does not rerun image registration, inspect PCB output, execute DRC or
measure resistor values and loaded RAS timing. The table's circuit roles
come from the sheet-2 ladder. The [memory timing report](memory-timing-boundary.md)
checks D53-to-R49–R52 endpoint pairs, rather than every bank connection.

The separate source-PCB check requires KiCad's `pcbnew` Python module:

```sh
/usr/bin/python3 kicad/check_ras_resistor_bank.py
```

Use the Python interpreter that provides `pcbnew` on your installation.
This checks the eight centres, orientation, lead span, values and pad widths,
plus C69 pad widths; it does not inspect routed copper or run DRC.

Source record: [bank registration](../ref/photos/juku-pcb-2/ras-resistor-bank-registration.json).
