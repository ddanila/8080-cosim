# Serial handoff

Status: **SERIAL CORE GUARDED / AUXILIARY PIN CONTINUITY PENDING**

This generated report separates the serial-port facts already guarded by
the board JSON and HDL from the remaining functional serial boundary.
It covers the D11 8251 host bus path, the D57 baud-clock handoff, and
the X3 line-driver/receiver wiring. It now also guards a minimal
bus-visible 8251-style async Tx/Rx loopback slice; it does not claim
external X3 loopback or full protocol-mode coverage.

## Command

```sh
python3 scripts/report_serial_handoff.py
```

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| D11 is the board USART | PASS | board JSON |
| D11 complete auxiliary pin contract is exposed | PASS | КР580ВВ51А/8251 datasheet contract |
| D11 TXEMPTY is source-proved NC | PASS | full-resolution sheet-1 omits pin 18 from the drawn USART symbol |
| D11 power-pin contract is routed | PASS | D11.4 GND / D11.26 +5V |
| D11 chip select is decoded | PASS | `CS_D11` |
| D11 register select BA0 is wired | PASS | `BA0` |
| D11 data bit DB0 is wired | PASS | `DB0` |
| D11 data bit DB1 is wired | PASS | `DB1` |
| D11 data bit DB2 is wired | PASS | `DB2` |
| D11 data bit DB3 is wired | PASS | `DB3` |
| D11 data bit DB4 is wired | PASS | `DB4` |
| D11 data bit DB5 is wired | PASS | `DB5` |
| D11 data bit DB6 is wired | PASS | `DB6` |
| D11 data bit DB7 is wired | PASS | `DB7` |
| D11 read strobe is wired | PASS | `IORD` |
| D11 write strobe is wired | PASS | `IOWR` |
| USART reset follows the system reset inverter | PASS | sheet-1 uninterrupted D13.6 -> D1.12/D11.21 conductor; `RESET` |
| USART main clock reaches D13 inverter output | PASS | sheet-1 uninterrupted D13.4 -> D105.2/D11.20 conductor |
| D57 baud output reaches D11 TxC/RxC | PASS | `PIT_BAUD` |
| USART TxD fans to line drivers | PASS | `SER_TXD` |
| D3.9->8 pre-inverter drives tied D12 inputs | PASS | `SER_TXD_INV` |
| 8259 SP/EN is strapped high for standalone master mode | PASS | sheet-1 A-rail arrow; `P5V` |
| USART RTS/DTR reach AP2 driver | PASS | `SER_RTS` / `SER_DTR` |
| USART RxD comes from UP2 receiver | PASS | `SER_RXD` |
| USART CTS/DSR come from the other two UP2 receivers | PASS | `SER_CTS_N` / `SER_DSR_N` |
| S_SOUT reaches X3.9 | PASS | `S_SOUT` |
| S_RTS reaches X3.10 | PASS | `S_RTS` |
| S_DTP reaches X3.11 | PASS | `S_DTP` |
| S_TTL reaches X3.3 | PASS | `S_TTL` |
| S_OC reaches X3.12 | PASS | `S_OC` |
| S_SIN reaches X3.4 | PASS | `S_SIN` |
| S_CTS reaches X3.5 | PASS | `S_CTS` |
| S_DSR reaches X3.6 | PASS | `S_DSR` |
| HDL USART model has guarded Tx/Rx loopback | PASS | `hdl/devices.v`; `hdl/sim/usart_8251_tb.v`; `sync/serial_check.sh` |
| HDL serial connector and drivers are instantiated | PASS | `hdl/juku_top.v` |

## Serial Nets

| Net | Endpoints |
| --- | --- |
| `CS_D11` | `D9.13`, `D11.11` |
| `RESET` | `D13.6`, `D1.12`, `D26.35`, `D27.35`, `D11.21` |
| `D13_4_D105_2` | `D13.4`, `D105.2`, `D11.20` |
| `PIT_BAUD` | `D57.10`, `D11.25`, `D11.9` |
| `SER_TXD` | `D11.19`, `D14.3`, `D3.11`, `D3.9`, `R18.2` |
| `SER_TXD_INV` | `D3.8`, `D12.1`, `D12.2` |
| `SER_RTS` | `D11.23`, `D32.3` |
| `SER_DTR` | `D11.24`, `D32.2` |
| `SER_RXD` | `D11.3`, `D104.13` |
| `SER_CTS_N` | `D104.12`, `D11.17` |
| `SER_DSR_N` | `D104.11`, `D11.22` |
| `S_SOUT` | `D14.6`, `A29.1`, `X3.9` |
| `S_RTS` | `D32.6`, `A30.1`, `X3.10` |
| `S_DTP` | `D32.7`, `A31.1`, `X3.11` |
| `S_TTL` | `D3.10`, `A23.1`, `X3.3` |
| `S_OC` | `D12.3`, `R18.1`, `R30.1`, `A22.1`, `X3.2`, `A32.1`, `X3.12` |
| `S_SIN` | `A24.1`, `X3.4`, `D104.4` |
| `S_CTS` | `A25.1`, `X3.5`, `D104.5` |
| `S_DSR` | `A26.1`, `X3.6`, `D104.6` |

## Boundary

- D11 is bus-visible at the decoded `0x08..0x0B` USART window, with
  BA0, DB0-DB7, `IORD`, `IOWR`, and `CS_D11` wired.
- D57 `OUT0` reaches both D11 clock inputs through `PIT_BAUD`.
- D11 serial-side pins are carried through the modeled D14/D32/D3/D12
  output drivers and D104 receiver to X3 signal pins.
- `sync/serial_check.sh` now proves a scoped USART behavior slice:
  mode/command writes, TxRDY/RxRDY/TxEMPTY status, command-driven
  RTS/DTR, and one 8N1 byte through a digital TxD->RxD loopback.
- D11 auxiliary pins remain physical-source blockers:
  14:RXRDY, 15:TXRDY.
  Trace each destination or record a source-proved intentional NC before
  treating the USART portion of the PCB as complete.
- The `.006` sheet explicitly draws D11 RxRDY/TxRDY to PIC IR0/IR1,
  but `.009` uses those PIC inputs for КР1818ВГ93 INTRQ/DRQ; preserving
  the FDC-era target therefore requires `.009` continuity rather than
  copying the older conductors.
- Full-resolution sheet 1 proves D11.16 `SYNDET` on the lower S4 throw.
  D11.18 `TXEMPTY` is absent from the drawn USART symbol and is now an
  explicit NC rather than an unresolved functional endpoint.
- External X3 loopback, electrical levels, and full 8251 sync/parity
  modes remain Tier-2 bench/software work after that PCB-truth boundary.
