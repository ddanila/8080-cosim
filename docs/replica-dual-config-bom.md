# Replica dual-config BOM

Source: `kicad/juku.board.json`
CSV: `docs/replica-dual-config-bom.csv`
Sourcing gate: `docs/replica-sourcing-readiness.md`

This is the current sourcing BOM split: an authentic Soviet
part column and a functional substitute column. It is generated from the
current KiCad board source and keeps the .009 populated-vs-expansion-socket
distinction explicit.

Run `python3 kicad/report_replica_sourcing_readiness.py` after regenerating this
BOM to refresh the source-early, programming-gated, and review-before-buying
readiness report.

## Summary

- Board component positions: 315
- Populate for current functional .009 build: 251
- Do not populate now (empty/DNP/pending): 64
- Unique BOM lines: 111

## Action Totals

| Action | Count basis |
| --- | ---: |
| circuit-review | 30 |
| leave-empty | 64 |
| mechanical-review | 17 |
| program/dump | 6 |
| source-now | 204 |

## BOM Lines

| Action | Type | Authentic part | Functional substitute | Positions | Populate now | Empty | Refs | Notes |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| circuit-review | AP2 | К170АП2 | RS-232/line-driver substitute required; verify +/-12 V interface | 2 | 2 | 0 | D14, D32 | - |
| circuit-review | C_ELEC | radial electrolytic | modern radial electrolytic with matching value/voltage/polarity | 3 | 3 | 0 | C31, C32, C33 | - |
| circuit-review | C_KM | КМ ceramic capacitor | modern ceramic capacitor with matching value/voltage/lead spacing | 8 | 8 | 0 | C9, C10, C11, C12, C15, C16, C19, C34 | - |
| circuit-review | C_KM 0,047 | КМ ceramic capacitor 0,047 | modern ceramic capacitor with matching value/voltage/lead spacing | 4 | 4 | 0 | C38, C42, C46, C50 | Factory placement/population is closed, but exact target capacitance, tolerance, and voltage remain unread; do not source the final part from the functional 0,047 model value. |
| circuit-review | C_KM 0,047 | КМ ceramic capacitor 0,047 | modern ceramic capacitor with matching value/voltage/lead spacing | 6 | 0 | 6 | C51, C52, C53, C70, C71, C72 | Target placement, population, capacitance, tolerance, and voltage remain unresolved; do not fabricate or source this position from the retired fit-to-space coordinate or functional 0,047 model value. |
| circuit-review | C_KM 1,5 нФ | КМ ceramic capacitor 1,5 нФ | modern ceramic capacitor with matching value/voltage/lead spacing | 2 | 2 | 0 | C20, C22 | Capacitance is source-closed, but tolerance and voltage rating remain unread; do not source the final part from value alone. |
| circuit-review | D_DIODE | Soviet diode/zener per value | modern diode/zener matching value and power | 1 | 1 | 0 | VD4 | - |
| circuit-review | Q_KT13 | КТ315 | modern E-C-B transistor selected for the video role and KT-13 pad row | 1 | 1 | 0 | VT2 | - |
| circuit-review | Q_KT27 | КТ972 | modern E-C-B TO-126 transistor selected for the beeper role | 1 | 1 | 0 | VT1 | - |
| circuit-review | R_AXIAL | axial resistor | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R67 | - |
| circuit-review | UP2 | К170УП2 | RS-232/line-receiver substitute required; verify +/-12 V interface | 1 | 1 | 0 | D104 | - |
| leave-empty | C_KM 0,047 | КМ ceramic capacitor 0,047 | modern ceramic capacitor with matching value/voltage/lead spacing | 28 | 0 | 28 | C35, C36, C37, C39, C40, C41, C43, C44, C45, C47, C48, C49, C54, C55, C56, C57, C58, C59, ... (+10) | Target-assembly DNP; retain schematic intent and the fabricated footprint, but do not fit the part. |
| leave-empty | EPROM8K | К573РФ6 | 2764 / 27C64 / M2764 EPROM, programmed per ROM split | 1 | 0 | 1 | D19 | Only D15/D16 are populated in the .009 functional build; D17-D22 are expansion/empty sockets. |
| leave-empty | RU5 | К565РУ5Г / 565РУ5Г | 4164-family 64Kx1 DRAM candidate; verify pinout, refresh, speed, and rails | 24 | 0 | 24 | D60, D61, D62, D63, D64, D65, D66, D67, D68, D69, D70, D71, D72, D73, D74, D75, D76, D77, ... (+6) | D84-D91 are populated for the 64 KB .158/.009 target; D60-D83 are empty expansion sockets. Compatibility remains a procurement-time electrical check. |
| mechanical-review | EXPANSION_CONN | СНП59-96 Р-20-2-В | select exact substitute after circuit review | 1 | 1 | 0 | X1 | - |
| mechanical-review | JUMPER2 | wire/link | select exact substitute after circuit review | 1 | 1 | 0 | E5 | - |
| mechanical-review | JUMPER3 | wire/link | select exact substitute after circuit review | 4 | 4 | 0 | E1, E2, E3, E4 | - |
| mechanical-review | JUMPER4 | wire/link | select exact substitute after circuit review | 2 | 2 | 0 | E13, E14 | - |
| mechanical-review | KBD_CONN | keyboard connector | select exact substitute after circuit review | 1 | 1 | 0 | X9 | - |
| mechanical-review | PAR_CONN | parallel/interface connector | select exact substitute after circuit review | 1 | 1 | 0 | X2 | - |
| mechanical-review | POWER_CONN | СНО51-30/56х9В-23 power connector | select exact substitute after circuit review | 1 | 1 | 0 | X8 | - |
| mechanical-review | RF_CONN | RF connector | select exact substitute after circuit review | 1 | 1 | 0 | X6 | - |
| mechanical-review | SERIAL_CONN | СНП59-30-23-В / serial connector | select exact substitute after circuit review | 1 | 1 | 0 | X3 | - |
| mechanical-review | SW | switch | select exact substitute after circuit review | 2 | 2 | 0 | S1, S4 | - |
| mechanical-review | SW_DIP6 | DIP switch | select exact substitute after circuit review | 1 | 1 | 0 | S3 | - |
| mechanical-review | VIDEO_CONN | BNC/composite video connector | select exact substitute after circuit review | 1 | 1 | 0 | X7 | - |
| program/dump | DEC_PROM | КР556РТ4А | 74S287/82S129-class 256x4 bipolar PROM, programmed | 1 | 1 | 0 | D6 | Contents remain a PROM-truth item: prefer Baltijets disk files or hardware dump before programming. |
| program/dump | EPROM8K | 2764/M2764-class EPROM in .009 build; К573РФ5 on .006 BOM | 2764 / 27C64 / M2764 EPROM, programmed per ROM split | 7 | 2 | 5 | D15, D16, D17, D18, D20, D21, D22 | Only D15/D16 are populated in the .009 functional build; D17-D22 are expansion/empty sockets. |
| program/dump | RE3_PROM | К155РЕ3 | 74188/82S23-class 32x8 bipolar PROM, programmed | 1 | 1 | 0 | D8 | D8 `.039` content comes from the validated repeated physical table; the former reconstruction is superseded. |
| program/dump | RE3_PROM_092 | К155РЕ3 | 74188/82S23-class 32x8 bipolar PROM, programmed | 1 | 1 | 0 | D94 | D94 `.092` content comes from the validated repeated physical table; complete strobe gating remains continuity-gated. |
| program/dump | WAIT_PROM | КР556РТ4А | 74S287/82S129-class 256x4 bipolar PROM, programmed | 1 | 1 | 0 | D2 | D2 uses the preservation-grade physical `.037` table from three matching reads, including a power-cycled capture. |
| source-now | AG3_ONESHOT | К155АГ3 | 74LS123/74123-class one-shot; verify RC timing | 4 | 4 | 0 | D56, D97, D99, D102 | - |
| source-now | BUF8286 | КР580ВА86 | Intel 8286 / compatible bus transceiver | 3 | 3 | 0 | D4, D29, D107 | - |
| source-now | BUF8287 | КР580ВА87 | Intel 8287 / compatible bus transceiver | 1 | 1 | 0 | D100 | - |
| source-now | CLK_PHASE | К155ЛН5 | 74LS04/74LS14-class inverter; verify phase/timing use | 1 | 1 | 0 | D35 | - |
| source-now | CPU8080 | КР580ИК80А | Intel 8080A / compatible 8080 CPU | 1 | 1 | 0 | D1 | - |
| source-now | CT16_CTR | КР531ИЕ17 | 74F/74S163-class fast counter; verify timing | 1 | 1 | 0 | D40 | - |
| source-now | C_ELEC 47,0 | radial electrolytic 47,0 | modern radial electrolytic with matching value/voltage/polarity | 1 | 1 | 0 | C1 | - |
| source-now | C_KM 15 нФ | КМ ceramic capacitor 15 нФ | modern ceramic capacitor with matching value/voltage/lead spacing | 1 | 1 | 0 | C8 | - |
| source-now | C_KM 160 | КМ ceramic capacitor 160 | modern ceramic capacitor with matching value/voltage/lead spacing | 1 | 1 | 0 | C99 | - |
| source-now | C_KM 24 | КМ ceramic capacitor 24 | modern ceramic capacitor with matching value/voltage/lead spacing | 1 | 1 | 0 | C21 | - |
| source-now | C_KM 56 | КМ ceramic capacitor 56 | modern ceramic capacitor with matching value/voltage/lead spacing | 1 | 1 | 0 | C6 | - |
| source-now | C_KM 560 | КМ ceramic capacitor 560 | modern ceramic capacitor with matching value/voltage/lead spacing | 2 | 2 | 0 | C5, C7 | - |
| source-now | C_KM 680 | КМ ceramic capacitor 680 | modern ceramic capacitor with matching value/voltage/lead spacing | 1 | 1 | 0 | C94 | - |
| source-now | C_TRIM 4/20 | trimmer capacitor 4/20 | modern trimmer capacitor matching footprint/value | 1 | 1 | 0 | C73 | - |
| source-now | D_DIODE КС147 | Soviet diode/zener per value КС147 | modern diode/zener matching value and power | 1 | 1 | 0 | VD5 | - |
| source-now | D_DIODE КС147Г | Soviet diode/zener per value КС147Г | modern diode/zener matching value and power | 1 | 1 | 0 | VD3 | - |
| source-now | FDC_CONN | FDC_CONN | select exact substitute after circuit review | 1 | 1 | 0 | X4 | - |
| source-now | IE10_CTR | К555ИЕ10 | SN74LS161A-compatible synchronous binary counter; D103 /13 behavior guarded | 1 | 1 | 0 | D103 | - |
| source-now | IE7_CTR | К555ИЕ7 | SN74LS193-compatible up/down counter; standard behavior guarded, verify board wiring | 5 | 5 | 0 | D44, D45, D46, D47, D106 | - |
| source-now | IO_DEC138 | К555ИД7 | 74LS138 / 74HCT138 decoder | 1 | 1 | 0 | D9 | - |
| source-now | IR16 | К555ИР16 | 74295/74LS295-class shift register; verify pinout | 3 | 3 | 0 | D41, D42, D43 | - |
| source-now | IR82 | КР580ИР82 | 8282/8283-class latch; verify polarity/package | 1 | 1 | 0 | D58 | - |
| source-now | KP12_MUX | К555КП12 | 74LS253 dual 4:1 three-state multiplexer | 2 | 2 | 0 | D95, D101 | - |
| source-now | KP14_MUX | КР531КП14 | 74LS257/258-class quad 2:1 mux; verify OE/polarity | 4 | 4 | 0 | D48, D49, D50, D51 | - |
| source-now | KP14_MUX | К555КП14 | 74LS257/258-class quad 2:1 mux; verify OE/polarity | 1 | 1 | 0 | D52 | - |
| source-now | LA12_GATE | КР531ЛА12 | SN74S37-compatible high-drive quad 2-input NAND | 1 | 1 | 0 | D36 | - |
| source-now | LA18 | К155ЛА18 | open-collector NAND/driver; verify output topology | 1 | 1 | 0 | D12 | - |
| source-now | LA1_GATE | КР531ЛА1 | 74S/74LS NAND-class gate; verify exact logic section | 1 | 1 | 0 | D38 | - |
| source-now | LA3_GATE | КР1533ЛА3 | 74LS00 / 74ALS00-class NAND | 3 | 3 | 0 | D7, D37, D39 | - |
| source-now | LA3_GATE | К155ЛА3 | 74LS00 / 74ALS00-class NAND | 1 | 1 | 0 | D105 | - |
| source-now | LE4 | К555ЛЕ4 | 74LS02 NOR-class gate | 1 | 1 | 0 | D92 | - |
| source-now | LN1_DUAL | КР531ЛН1 | 74S04/74LS04-class inverter | 1 | 1 | 0 | D33 | - |
| source-now | LN1_OSC | КР531ЛН1 | 74S04/74LS04-class inverter; oscillator section timing matters | 1 | 1 | 0 | D59 | - |
| source-now | LN2 | К561ЛН2 | CD4049/К561ЛН2-class CMOS inverter; verify role | 1 | 1 | 0 | D3 | - |
| source-now | LN3_OC_INV | К155ЛН3 | 7406-class hex open-collector inverter; verify pullups and voltage | 1 | 1 | 0 | D28 | - |
| source-now | LP11_BUF | К155ЛП11 | SN74367 hex three-state buffer | 1 | 1 | 0 | D98 | - |
| source-now | LP5_XOR | К155ЛП5 | 74LS86 XOR-class gate | 1 | 1 | 0 | D34 | - |
| source-now | PIC8259 | КР580ВН59 | 8259A PIC | 1 | 1 | 0 | D10 | - |
| source-now | PIT8253 | КР580ВИ53 | 8253 or 8254 PIT | 3 | 3 | 0 | D54, D55, D57 | - |
| source-now | PPI8255 | КР580ВВ55А | 8255A / 82C55 PPI | 2 | 2 | 0 | D26, D27 | - |
| source-now | RASCAS_DEC | КР531ИД7 | 74S138/74F138-class fast decoder; verify timing | 1 | 1 | 0 | D53 | - |
| source-now | RU5 | К565РУ5Г | 4164-family 64Kx1 DRAM candidate; verify pinout, refresh, speed, and rails | 8 | 8 | 0 | D84, D85, D86, D87, D88, D89, D90, D91 | D84-D91 are populated for the 64 KB .158/.009 target; D60-D83 are empty expansion sockets. Compatibility remains a procurement-time electrical check. |
| source-now | R_AXIAL 1,2к | axial resistor 1,2к | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R32 | - |
| source-now | R_AXIAL 1,3к | axial resistor 1,3к | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R92 | - |
| source-now | R_AXIAL 1,5к | axial resistor 1,5к | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R20 | - |
| source-now | R_AXIAL 100 | axial resistor 100 | modern axial resistor, matching value and power rating | 2 | 2 | 0 | R3, R4 | - |
| source-now | R_AXIAL 120 | axial resistor 120 | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R104 | - |
| source-now | R_AXIAL 12к | axial resistor 12к | modern axial resistor, matching value and power rating | 5 | 5 | 0 | R39, R61, R100, R102, R108 | - |
| source-now | R_AXIAL 13к | axial resistor 13к | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R34 | - |
| source-now | R_AXIAL 15к | axial resistor 15к | modern axial resistor, matching value and power rating | 6 | 6 | 0 | R40, R41, R42, R43, R44, R45 | - |
| source-now | R_AXIAL 1к | axial resistor 1к | modern axial resistor, matching value and power rating | 10 | 10 | 0 | R11, R12, R13, R14, R29, R31, R38, R63, R66, R91 | - |
| source-now | R_AXIAL 20 | axial resistor 20 | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R57 | - |
| source-now | R_AXIAL 200 | axial resistor 200 | modern axial resistor, matching value and power rating | 2 | 2 | 0 | R17, R46 | - |
| source-now | R_AXIAL 20к | axial resistor 20к | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R47 | - |
| source-now | R_AXIAL 220 | axial resistor 220 | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R94 | - |
| source-now | R_AXIAL 2к | axial resistor 2к | modern axial resistor, matching value and power rating | 5 | 5 | 0 | R1, R5, R6, R62, R90 | - |
| source-now | R_AXIAL 33к | axial resistor 33к | modern axial resistor, matching value and power rating | 3 | 3 | 0 | R18, R30, R59 | - |
| source-now | R_AXIAL 4,7к | axial resistor 4,7к | modern axial resistor, matching value and power rating | 2 | 2 | 0 | R86, R99 | - |
| source-now | R_AXIAL 430 | axial resistor 430 | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R65 | - |
| source-now | R_AXIAL 470 | axial resistor 470 | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R19 | - |
| source-now | R_AXIAL 5,1к | axial resistor 5,1к | modern axial resistor, matching value and power rating | 7 | 7 | 0 | R53, R54, R55, R56, R58, R60, R64 | - |
| source-now | R_AXIAL 6,2к | axial resistor 6,2к | modern axial resistor, matching value and power rating | 3 | 3 | 0 | R87, R88, R89 | - |
| source-now | R_AXIAL 620 | axial resistor 620 | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R33 | - |
| source-now | R_AXIAL 75 | axial resistor 75 | modern axial resistor, matching value and power rating | 4 | 4 | 0 | R49, R50, R51, R52 | - |
| source-now | R_AXIAL 8,2 | axial resistor 8,2 | modern axial resistor, matching value and power rating | 1 | 1 | 0 | R48 | - |
| source-now | SYS8238 | КР580ВК38 | 8228/8238-class system controller; verify pinout | 1 | 1 | 0 | D5 | - |
| source-now | TL2 | К555ТЛ2 | 74LS14-class hex Schmitt inverter | 1 | 1 | 0 | D13 | - |
| source-now | TM2_DFF | КМ555ТМ2 | 74LS74 dual D flip-flop | 2 | 2 | 0 | D30, D96 | - |
| source-now | USART8251 | КР580ВВ51А | 8251A / 82C51-class USART | 1 | 1 | 0 | D11 | - |
| source-now | VABUS | КР580ВА87 | Intel 8287 / compatible bus transceiver | 3 | 3 | 0 | D23, D24, D25 | - |
| source-now | VG93_FDC | КР1818ВГ93 | WD1793 pin-compatible candidate; verify clock, rails, and interface timing | 1 | 1 | 0 | D93 | A western WD1793 is a functional-build candidate, not an automatically approved drop-in; verify the selected device against the final D93 circuit. |
| source-now | WIRE_LINK 13.5 cm | factory insulated assembly wire 13.5 cm | insulated hookup wire cut and installed to the documented route length | 1 | 1 | 0 | W10 | Populate as an insulated point-to-point assembly conductor; do not substitute etched PCB copper. |
| source-now | WIRE_LINK ~11.5 cm (held) | factory insulated assembly wire ~11.5 cm (held) | insulated hookup wire cut and installed to the documented route length | 1 | 1 | 0 | W11 | Populate as an insulated point-to-point assembly conductor; do not substitute etched PCB copper. |
| source-now | WIRE_LINK ~19 cm | factory insulated assembly wire ~19 cm | insulated hookup wire cut and installed to the documented route length | 1 | 1 | 0 | W8 | Populate as an insulated point-to-point assembly conductor; do not substitute etched PCB copper. |
| source-now | WIRE_LINK ~23 cm (held) | factory insulated assembly wire ~23 cm (held) | insulated hookup wire cut and installed to the documented route length | 1 | 1 | 0 | W14 | Populate as an insulated point-to-point assembly conductor; do not substitute etched PCB copper. |
| source-now | WIRE_LINK ~24 cm (held) | factory insulated assembly wire ~24 cm (held) | insulated hookup wire cut and installed to the documented route length | 1 | 1 | 0 | W7 | Populate as an insulated point-to-point assembly conductor; do not substitute etched PCB copper. |
| source-now | WIRE_LINK ~6 cm | factory insulated assembly wire ~6 cm | insulated hookup wire cut and installed to the documented route length | 1 | 1 | 0 | W20 | Populate as an insulated point-to-point assembly conductor; do not substitute etched PCB copper. |
| source-now | WIRE_LINK ~9.5 cm | factory insulated assembly wire ~9.5 cm | insulated hookup wire cut and installed to the documented route length | 1 | 1 | 0 | W19 | Populate as an insulated point-to-point assembly conductor; do not substitute etched PCB copper. |
| source-now | WIRE_PAD | WIRE_PAD | select exact substitute after circuit review | 56 | 56 | 0 | A17, A21, A22, A23, A24, A25, A26, A27, A28, A29, A30, A31, A32, A45, A46, A47, A48, A49, ... (+38) | - |
| source-now | XTAL 16 МГц | РК-171 16 MHz crystal 16 МГц | 16 MHz HC-49/metal-can crystal matching footprint/load | 1 | 1 | 0 | Z1 | - |

## Use

- `source-now` and `source-populated-now` rows are planning candidates, not an approved shopping cart.
- `program/dump` rows need firmware/PROM contents before they are build-ready.
- The `Empty` count includes fabricated leave-empty positions and evidence-held positions with no current footprint; the row action/note distinguishes DNP, empty-socket, and placement-pending cases.
- `mechanical-review` and `circuit-review` rows need exact part drawing, footprint, or circuit-role confirmation before order.
