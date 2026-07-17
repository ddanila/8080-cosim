# R49-R56 RAS resistor bank

Status: **PLACEMENT / VALUES CLOSED**

The `.006` assembly drawing fixes the bank/refdes order. Registered target-board
component views show the same eight populated vertical bodies, while the reflected
solder panorama corroborates the drilled column. The red bodies directly read `75Ω`
and the tan bodies directly read `5K1`; this supersedes the earlier unvalued/100-ohm
working note. Connectivity is unchanged and remains source-closed by the sheet-2
D53-to-RAS ladder.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| All registered sources match SHA256 | PASS | 5 drawing/photo artifacts |
| Drawing refdes order matches the target photo column | PASS | R56/R52, R55/R51, R54/R50, R53/R49 |
| Registered geometry is the vertical 10.16 mm bank | PASS | x=221.0 mm; eight independently recorded centres |
| Target case markings are encoded as values | PASS | R49-R52=75 Ω; R53-R56=5.1 kΩ |
| Board provenance cites the target-board registration | PASS | all eight board-JSON components |
| PCB generator carries the fitted placements without annulus waivers | PASS | normal 1.6 mm pads; C69 workaround retired |

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

## Disposition

- R49-R52 are 75 Ω series resistors, not the earlier 100 Ω working value.
- R53-R56 are 5.1 kΩ RAS-to-ground terminations.
- Moving the bank to its photo-fitted column removes the fictional C69/R52 close pass;
  both footprints use their normal pad geometry and source-PCB electrical DRC remains clean.
- The source model's electrical nets do not change in this placement/value closure.

Source record: `ref/photos/juku-pcb-2/ras-resistor-bank-registration.json`.
