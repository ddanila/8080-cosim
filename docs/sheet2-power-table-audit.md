# Exact .009 sheet-2 IC power-table audit

Source: `ref/photos/dgsh5-109-009-e3/PXL_20260718_101927794.jpg`; original pixels `(0,2150)-(3072,3920)`. Row labels also appear in `PXL_20260718_101924004.jpg`.

Result: **PASS** for the unambiguous mapped columns — 54 modeled positions (30 factory-fitted ICs and 24 empty expansion sockets), 108 audited rail endpoints, 0 missing model endpoints. The ИР16 and РУ4 columns remain outside this pass.

| Ref | Population | Model type | Table pin:rail entries | Model |
| --- | --- | --- | --- | --- |
| `D60` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D61` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D62` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D63` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D64` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D65` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D66` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D67` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D54` | factory-fitted | `PIT8253` | `24:P5V, 12:GND` | PASS |
| `D55` | factory-fitted | `PIT8253` | `24:P5V, 12:GND` | PASS |
| `D57` | factory-fitted | `PIT8253` | `24:P5V, 12:GND` | PASS |
| `D35` | factory-fitted | `CLK_PHASE` | `14:P5V, 7:GND` | PASS |
| `D44` | factory-fitted | `IE7_CTR` | `16:P5V, 8:GND` | PASS |
| `D45` | factory-fitted | `IE7_CTR` | `16:P5V, 8:GND` | PASS |
| `D46` | factory-fitted | `IE7_CTR` | `16:P5V, 8:GND` | PASS |
| `D47` | factory-fitted | `IE7_CTR` | `16:P5V, 8:GND` | PASS |
| `D48` | factory-fitted | `KP14_MUX` | `8:GND, 16:P5V` | PASS |
| `D49` | factory-fitted | `KP14_MUX` | `8:GND, 16:P5V` | PASS |
| `D53` | factory-fitted | `RASCAS_DEC` | `8:GND, 16:P5V` | PASS |
| `D56` | factory-fitted | `AG3_ONESHOT` | `16:P5V, 8:GND` | PASS |
| `D103` | factory-fitted | `IE10_CTR` | `16:P5V, 8:GND` | PASS |
| `D36` | factory-fitted | `LA12_GATE` | `7:GND, 14:P5V` | PASS |
| `D58` | factory-fitted | `IR82` | `20:P5V, 10:GND` | PASS |
| `D68` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D69` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D70` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D71` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D72` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D73` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D74` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D75` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D76` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D77` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D78` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D79` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D80` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D81` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D82` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D83` | empty socket | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D84` | factory-fitted | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D85` | factory-fitted | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D86` | factory-fitted | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D87` | factory-fitted | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D88` | factory-fitted | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D89` | factory-fitted | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D90` | factory-fitted | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D91` | factory-fitted | `RU5` | `16:GND, 8:RAIL_G` | PASS |
| `D52` | factory-fitted | `KP14_MUX` | `8:GND, 16:P5V` | PASS |
| `D50` | factory-fitted | `KP14_MUX` | `8:GND, 16:P5V` | PASS |
| `D51` | factory-fitted | `KP14_MUX` | `8:GND, 16:P5V` | PASS |
| `D97` | factory-fitted | `AG3_ONESHOT` | `16:P5V, 8:GND` | PASS |
| `D99` | factory-fitted | `AG3_ONESHOT` | `16:P5V, 8:GND` | PASS |
| `D102` | factory-fitted | `AG3_ONESHOT` | `16:P5V, 8:GND` | PASS |
| `D106` | factory-fitted | `IE7_CTR` | `16:P5V, 8:GND` | PASS |

## Scope boundary

Only unambiguous table columns with a direct model-type mapping are checked. The photographed table's `К581РУ4` column lists pin 9 on A and pin 1 on H. No К581РУ4 appears in the guarded .009 factory IC census; the eight fitted owner-bank devices D84–D91 are К565РУ5Г. The RU5 socket pin 9 carries MA7, so the table's RU4 pin-9 supply must not be applied to that bank. This resolves the fitted-bank interpretation of that column, but does not establish why the drawing retained it or whether a rewired RU4 variant existed. The table's G row is a +12/+5 selector, so `RAIL_G` is intentional rather than a fixed +5 V node. This checks JSON node names, not copper connectivity.

The full header in the overlapping original-pixel table tile explicitly prints `555 ИР16` in its +5 pin-16 / ground pin-8 group. The official census calls D41–D43 К555ИР16, the owner D41 photo registration has a seven-contact row, an independent lower-centre owner crop shows marked D42/D43 with seven contacts per side, and the preserved 14-pin device contract assigns supply pins 14/7. This is a confirmed package-width error in the table for those fitted devices. Do not move their supply nets to nonexistent pads 16/8. See `ref/schematics/sheet2-ir16-power-table-conflict.json` for the images and remaining owner continuity check.
