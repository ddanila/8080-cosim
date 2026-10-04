# Official .009 IC census

Status: **OFFICIAL .009 IC CENSUS GUARDED**

This report compares a retained transcription of both pages of
`ДГШ5.109.009 ПЭЗ` with the board model. Factory markings and registered
owner overrides are displayed separately. The effective marking uses the registered
owner override when present and the factory marking otherwise; it does not
assert an observed owner marking for every row. D60-D83 are the only modeled
numeric IC positions absent from the ПЭЗ; they are retained as explicit
empty DRAM expansion sockets, not claimed as factory-populated parts.

## Command

```sh
python3 scripts/report_official_009_ic_census.py
```

The guard verifies the source PDF hash, reference coverage, effective
logic-family mappings, selected exact markings, and programming labels.
It does not reread PDF or photo text, inspect installed socket population,
verify firmware bytes, or establish pinout and electrical compatibility
between substitutions. Those require their owning evidence and guards.

## Guard checks

| Check | Result |
| --- | --- |
| Factory PDF checksum matches the registered source hash | PASS |
| Every factory-listed IC refdes exists in the board model | PASS |
| The transcription has no duplicate refdes | PASS |
| Every effective census marking maps to the modeled logic family | PASS |
| Selected exact markings match board JSON | PASS |
| Board-only numeric IC refs are only D60-D83 expansion sockets | PASS |
| Factory programming identities match .037/.038/.039/.041-.043/.087-.092 | PASS |

## Factory census

| Ref | PDF page | Factory marking | Effective census marking | Model type | Result | Disposition |
| --- | ---: | --- | --- | --- | --- | --- |
| D1 | 2 | КР580ИК80А | КР580ИК80А | CPU8080 | PASS | factory |
| D2 | 2 | КР556РТ4 | КР556РТ4А | WAIT_PROM | PASS | owner-observed substitution |
| D3 | 2 | К561ЛН2 | К561ЛН2 | LN2 | PASS | factory |
| D4 | 2 | КР580ВА86 | КР580ВА86 | BUF8286 | PASS | factory |
| D5 | 2 | КР580ВК38 | КР580ВК38 | SYS8238 | PASS | factory |
| D6 | 2 | КР556РТ4 | КР556РТ4 | DEC_PROM | PASS | factory |
| D7 | 2 | К555ЛА3 | КР1533ЛА3 | LA3_GATE | PASS | owner-observed substitution |
| D8 | 2 | К155РЕ3 | К155РЕ3 | RE3_PROM | PASS | factory |
| D9 | 2 | К555ИД7 | К555ИД7 | IO_DEC138 | PASS | factory |
| D10 | 2 | КР580ВН59 | КР580ВН59 | PIC8259 | PASS | factory |
| D11 | 2 | КР580ВВ51А | КР580ВВ51А | USART8251 | PASS | factory |
| D12 | 2 | К155ЛА18 | К155ЛА18 | LA18 | PASS | factory |
| D13 | 2 | К555ТЛ2 | К555ТЛ2 | TL2 | PASS | factory |
| D14 | 2 | К170АП2 | К170АП2 | AP2 | PASS | factory |
| D15 | 2 | К573РФ5 | К573РФ5 | EPROM8K | PASS | factory |
| D16 | 2 | К573РФ5 | К573РФ5 | EPROM8K | PASS | factory |
| D17 | 2 | К573РФ5 | К573РФ5 | EPROM8K | PASS | factory |
| D18 | 2 | К573РФ5 | К573РФ5 | EPROM8K | PASS | factory |
| D19 | 2 | К573РФ6 | К573РФ6 | EPROM8K | PASS | factory |
| D20 | 2 | К573РФ5 | К573РФ5 | EPROM8K | PASS | factory |
| D21 | 2 | К573РФ5 | К573РФ5 | EPROM8K | PASS | factory |
| D22 | 2 | К573РФ5 | К573РФ5 | EPROM8K | PASS | factory |
| D23 | 2 | КР580ВА87 | КР580ВА87 | VABUS | PASS | factory |
| D24 | 2 | КР580ВА87 | КР580ВА87 | VABUS | PASS | factory |
| D25 | 2 | КР580ВА87 | КР580ВА87 | VABUS | PASS | factory |
| D26 | 2 | КР580ВВ55А | КР580ВВ55А | PPI8255 | PASS | factory |
| D27 | 2 | КР580ВВ55А | КР580ВВ55А | PPI8255 | PASS | factory |
| D28 | 2 | К155ЛН3 | К155ЛН3 | LN3_OC_INV | PASS | factory |
| D29 | 2 | КР580ВА86 | КР580ВА86 | BUF8286 | PASS | factory |
| D30 | 2 | КМ555ТМ2 | КМ555ТМ2 | TM2_DFF | PASS | factory |
| D32 | 2 | К170АП2 | К170АП2 | AP2 | PASS | factory |
| D33 | 2 | КР531ЛН1 | КР531ЛН1 | LN1_DUAL | PASS | factory |
| D34 | 2 | К555ЛП5 | К555ЛП5 | LP5_XOR | PASS | factory |
| D35 | 2 | К155ЛН5 | К155ЛН5 | CLK_PHASE | PASS | factory |
| D36 | 3 | КР531ЛА12 | КР531ЛА12 | LA12_GATE | PASS | factory |
| D37 | 3 | К555ЛА3 | КР1533ЛА3 | LA3_GATE | PASS | owner-observed substitution |
| D38 | 3 | КР531ЛА1 | КР531ЛА1 | LA1_GATE | PASS | factory |
| D39 | 3 | К555ЛА3 | КР1533ЛА3 | LA3_GATE | PASS | owner-observed substitution |
| D40 | 3 | КР531ИЕ17 | КР531ИЕ17 | CT16_CTR | PASS | factory |
| D41 | 3 | К555ИР16 | К555ИР16 | IR16 | PASS | factory |
| D42 | 3 | К555ИР16 | К555ИР16 | IR16 | PASS | factory |
| D43 | 3 | К555ИР16 | К555ИР16 | IR16 | PASS | factory |
| D44 | 3 | К555ИЕ7 | К555ИЕ7 | IE7_CTR | PASS | factory |
| D45 | 3 | К555ИЕ7 | К555ИЕ7 | IE7_CTR | PASS | factory |
| D46 | 3 | К555ИЕ7 | К555ИЕ7 | IE7_CTR | PASS | factory |
| D47 | 3 | К555ИЕ7 | К555ИЕ7 | IE7_CTR | PASS | factory |
| D48 | 3 | КР531КП14 | КР531КП14 | KP14_MUX | PASS | factory |
| D49 | 3 | КР531КП14 | КР531КП14 | KP14_MUX | PASS | factory |
| D50 | 3 | КР531КП14 | КР531КП14 | KP14_MUX | PASS | factory |
| D51 | 3 | КР531КП14 | КР531КП14 | KP14_MUX | PASS | factory |
| D52 | 3 | К555КП14 | К555КП14 | KP14_MUX | PASS | factory |
| D53 | 3 | КР531ИД7 | КР531ИД7 | RASCAS_DEC | PASS | factory |
| D54 | 3 | КР580ВИ53 | КР580ВИ53 | PIT8253 | PASS | factory |
| D55 | 3 | КР580ВИ53 | КР580ВИ53 | PIT8253 | PASS | factory |
| D56 | 3 | КМ555АГ3 | К155АГ3 | AG3_ONESHOT | PASS | owner-observed substitution |
| D57 | 3 | КР580ВИ53 | КР580ВИ53 | PIT8253 | PASS | factory |
| D58 | 3 | КР580ИР82 | КР580ИР82 | IR82 | PASS | factory |
| D59 | 3 | КР531ЛН1 | КР531ЛН1 | LN1_OSC | PASS | factory |
| D84 | 3 | К565РУ5Г | К565РУ5Г | RU5 | PASS | factory |
| D85 | 3 | К565РУ5Г | К565РУ5Г | RU5 | PASS | factory |
| D86 | 3 | К565РУ5Г | К565РУ5Г | RU5 | PASS | factory |
| D87 | 3 | К565РУ5Г | К565РУ5Г | RU5 | PASS | factory |
| D88 | 3 | К565РУ5Г | К565РУ5Г | RU5 | PASS | factory |
| D89 | 3 | К565РУ5Г | К565РУ5Г | RU5 | PASS | factory |
| D90 | 3 | К565РУ5Г | К565РУ5Г | RU5 | PASS | factory |
| D91 | 3 | К565РУ5Г | К565РУ5Г | RU5 | PASS | factory |
| D92 | 3 | К555ЛЕ4 | К555ЛЕ4 | LE4 | PASS | factory |
| D93 | 3 | КР1818ВГ93 | КР1818ВГ93 | VG93_FDC | PASS | factory |
| D94 | 3 | К155РЕ3 | К155РЕ3 | RE3_PROM_092 | PASS | factory |
| D95 | 3 | К555КП12 | К555КП12 | KP12_MUX | PASS | factory |
| D96 | 3 | КМ555ТМ2 | КМ555ТМ2 | TM2_DFF | PASS | factory |
| D97 | 3 | КМ555АГ3 | К155АГ3 | AG3_ONESHOT | PASS | owner-observed substitution |
| D98 | 3 | К155ЛП11 | К155ЛП11 | LP11_BUF | PASS | factory |
| D99 | 3 | КМ555АГ3 | К155АГ3 | AG3_ONESHOT | PASS | owner-observed substitution |
| D100 | 3 | КР580ВА87 | КР580ВА87 | BUF8287 | PASS | factory |
| D101 | 3 | К555КП12 | К555КП12 | KP12_MUX | PASS | factory |
| D102 | 3 | КМ555АГ3 | К155АГ3 | AG3_ONESHOT | PASS | owner-observed substitution |
| D103 | 3 | К555ИЕ10 | К555ИЕ10 | IE10_CTR | PASS | factory |
| D104 | 3 | К170УП2 | К170УП2 | UP2 | PASS | factory |
| D105 | 3 | К155ЛА3 | К155ЛА3 | LA3_GATE | PASS | factory |
| D106 | 3 | К555ИЕ7 | К555ИЕ7 | IE7_CTR | PASS | factory |
| D107 | 3 | КР580ВА86 | КР580ВА86 | BUF8286 | PASS | factory |

## Programmed positions

| Ref | Factory program |
| --- | --- |
| D2 | ДГШ5.106.037 |
| D6 | ДГШ5.106.038 |
| D8 | ДГШ5.106.039 |
| D15 | ДГШ5.106.087 |
| D16 | ДГШ5.106.041 |
| D17 | ДГШ5.106.042 |
| D18 | ДГШ5.106.043 |
| D19 | ДГШ5.106.088 |
| D20 | ДГШ5.106.089 |
| D21 | ДГШ5.106.090 |
| D22 | ДГШ5.106.091 |
| D94 | ДГШ5.106.092 |

## Source

- `ref/Juku_official_chip_BOM.pdf`
- SHA256 `b8c36e1320db9c35fbd9bc0b600d660c8cc1c753edd705d809ae4a1e67a9b85d`
- Machine-readable transcription: `ref/juku-official-009-ic-census.json`
