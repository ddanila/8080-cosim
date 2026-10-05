# Exact .009 sheet-1 IC power-table audit

Source: `ref/photos/dgsh5-109-009-e3/PXL_20260718_101827714.jpg`; original pixels `(0,2050)-(2350,3150)`.

Result: **PASS** for the table's populated cells — 30 ICs, 87 audited rail endpoints, 0 missing model endpoints. D104.16 is a separate device-contract conflict outside this pass.

## Command

Run from the repository root with Python 3 (standard library only).
The command overwrites this report.

```sh
python3 scripts/check_sheet1_power_table.py
```

| Ref | Model type | Table pin:rail entries | Model |
| --- | --- | --- | --- |
| `D1` | `CPU8080` | `20:P5V, 28:P12V, 2:GND` | PASS |
| `D4` | `BUF8286` | `20:P5V, 10:GND` | PASS |
| `D107` | `BUF8286` | `20:P5V, 10:GND` | PASS |
| `D5` | `SYS8238` | `28:P5V, 14:GND` | PASS |
| `D6` | `DEC_PROM` | `16:P5V, 8:GND` | PASS |
| `D15` | `EPROM8K` | `1:P5V, 26:P5V, 27:P5V, 28:P5V, 14:GND` | PASS |
| `D16` | `EPROM8K` | `1:P5V, 26:P5V, 27:P5V, 28:P5V, 14:GND` | PASS |
| `D26` | `PPI8255` | `26:P5V, 7:GND` | PASS |
| `D27` | `PPI8255` | `26:P5V, 7:GND` | PASS |
| `D11` | `USART8251` | `26:P5V, 4:GND` | PASS |
| `D10` | `PIC8259` | `28:P5V, 14:GND` | PASS |
| `D9` | `IO_DEC138` | `16:P5V, 8:GND` | PASS |
| `D29` | `BUF8286` | `20:P5V, 10:GND` | PASS |
| `D24` | `VABUS` | `20:P5V, 10:GND` | PASS |
| `D23` | `VABUS` | `20:P5V, 10:GND` | PASS |
| `D25` | `VABUS` | `20:P5V, 10:GND` | PASS |
| `D17` | `EPROM8K` | `1:P5V, 26:P5V, 27:P5V, 28:P5V, 14:GND` | PASS |
| `D18` | `EPROM8K` | `1:P5V, 26:P5V, 27:P5V, 28:P5V, 14:GND` | PASS |
| `D19` | `EPROM8K` | `1:P5V, 26:P5V, 27:P5V, 28:P5V, 14:GND` | PASS |
| `D20` | `EPROM8K` | `1:P5V, 26:P5V, 27:P5V, 28:P5V, 14:GND` | PASS |
| `D21` | `EPROM8K` | `1:P5V, 26:P5V, 27:P5V, 28:P5V, 14:GND` | PASS |
| `D22` | `EPROM8K` | `1:P5V, 26:P5V, 27:P5V, 28:P5V, 14:GND` | PASS |
| `D14` | `AP2` | `8:P12V, 5:M12V, 4:GND` | PASS |
| `D32` | `AP2` | `8:P12V, 5:M12V, 4:GND` | PASS |
| `D12` | `LA18` | `8:P5V, 4:GND` | PASS |
| `D104` | `UP2` | `15:P5V, 8:GND` | PASS |
| `D8` | `RE3_PROM` | `16:P5V, 8:GND` | PASS |
| `D2` | `WAIT_PROM` | `16:P5V, 8:GND` | PASS |
| `D94` | `RE3_PROM_092` | `16:P5V, 8:GND` | PASS |
| `D100` | `BUF8287` | `20:P5V, 10:GND` | PASS |

## Scope boundary

The script compares hard-coded table transcriptions with board JSON nodes
for every chip whose model type is listed in its `PIN_RAILS` map. It does
not enforce a fixed reference census: a removed chip or an unmapped type
can disappear from the report without causing failure. Physical population
is not checked.
The source image is cited for the transcription; this script neither
reads its pixels nor checks its hash.

The table's 170АП2 column gives +12 V pin8, −12 V pin5, and ground pin4. The separate УП2 column gives +5 V pin15 and ground pin8 but leaves its +12 V cell blank. The preserved К170УП2 device sheet calls D104.16 a +12 V supply. That physical rail remains open in `ref/schematics/d104-pin16-rail-conflict.json`; this table check does not assign it. These results check logical node names, not copper connectivity, PPI footprint orientation, or the rest of the .009 sheets.
