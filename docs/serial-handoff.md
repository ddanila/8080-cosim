# Serial handoff

Status: **SERIAL CORE GUARDED / PHYSICAL LEVELS PENDING**

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
| Undrawn D13 inverter sections are explicitly unused | PASS | sheet-1 uses sections 1->2, 3->4, 5->6, and 13->12; only 9->8 and 11->10 are unused |
| D57 baud output reaches D11 TxC/RxC | PASS | native sheet-2 `BAUD R.` handoff and sheet-1 TxC/RxC fork |
| USART TxD fans to line drivers | PASS | `SER_TXD` |
| D3.9->8 pre-inverter drives tied D12 inputs | PASS | `SER_TXD_INV` |
| D3 sections absent from the older sheet are owner-measured into D6 | PASS | chip-removed `.009` continuity: /PC1->D3.3/.4->D6.1 and /PC0->D3.5/.6->D6.2 |
| 8259 SP/EN is strapped high for standalone master mode | PASS | sheet-1 A-rail arrow; `P5V` |
| 8259 cascade outputs are source-proved unused | PASS | full-resolution sheet-1 PIC symbol omits CAS0/CAS1/CAS2 pins 12/13/15 |
| USART ready outputs reach PIC IR2/IR3 | PASS | native sheet-1 direct loops; pinned MAME primary-USART IR2/IR3 mapping |
| Tape-run interrupt preserves the exact-revision stale-sheet boundary | PASS | .009 sheet 1: IR4=(3) TAPE RUN INT; complete .009 sheet 3: no matching continuation |
| Runnable ROMBIOS keeps stale tape IR4 masked | PASS | exact ekta37 event at 0x02D6 writes mask 0xDF: IR4 masked, IR5 enabled |
| USART RTS/DTR reach AP2 driver | PASS | `SER_RTS` / `SER_DTR` |
| USART RxD comes from UP2 receiver | PASS | `SER_RXD` |
| USART CTS/DSR come from the other two UP2 receivers | PASS | `SER_CTS_N` / `SER_DSR_N` |
| UP2 fourth receiver output is owner-closed NC | PASS | D104.7 remains an input boundary; D104.10 is NC by owner continuity and exact-revision drawing |
| S_SOUT reaches X3.9 | PASS | `S_SOUT` |
| S_RTS reaches X3.10 | PASS | `S_RTS` |
| S_DTP reaches X3.11 | PASS | `S_DTP` |
| S_TTL reaches X3.3 | PASS | `S_TTL` |
| S_OC reaches X3.12 | PASS | `S_OC` |
| S_SIN reaches X3.4 | PASS | `S_SIN` |
| S_CTS reaches X3.5 | PASS | `S_CTS` |
| S_DSR reaches X3.6 | PASS | `S_DSR` |
| Factory wire W20 closes D3.10 to the S_TTL connector island | PASS | assembly wire W20; `S_TTL_D3` -> `S_TTL` |
| HDL USART model has guarded Tx/Rx loopback | PASS | `hdl/devices.v`; `hdl/sim/usart_8251_tb.v`; `sync/serial_check.sh` |
| HDL serial connector and drivers are instantiated | PASS | `hdl/juku_top.v` |

## Serial Nets

| Net | Endpoints |
| --- | --- |
| `CS_D11` | `D9.13`, `D11.11` |
| `RESET` | `D13.6`, `D1.12`, `D26.35`, `D27.35`, `D11.21`, `D93.19` |
| `D13_4_D105_2` | `D13.4`, `D105.2`, `D11.20`, `D30.11` |
| `PIT_BAUD` | `D57.10`, `D11.25`, `D11.9` |
| `SER_TXD` | `D11.19`, `D14.3`, `D3.11`, `D3.9`, `R18.2` |
| `SER_TXD_INV` | `D3.8`, `D12.1`, `D12.2` |
| `SER_RTS` | `D11.23`, `D32.3` |
| `SER_DTR` | `D11.24`, `D32.2` |
| `SER_RXD` | `D11.3`, `D104.13` |
| `SER_CTS_N` | `D104.12`, `D11.17` |
| `SER_DSR_N` | `D104.11`, `D11.22` |
| `D104_X4_IN_BOUNDARY` | `D104.7` |
| `USART_RXRDY_IRQ` | `D10.20`, `D11.14` |
| `USART_TXRDY_IRQ` | `D10.21`, `D11.15` |
| `S_SOUT` | `D14.6`, `A29.1`, `X3.9` |
| `S_RTS` | `D32.6`, `A30.1`, `X3.10` |
| `S_DTP` | `D32.7`, `A31.1`, `X3.11` |
| `S_TTL` | `A23.1`, `X3.3`, `W20.1` |
| `S_TTL_D3` | `D3.10`, `W20.2` |
| `S_OC` | `D12.3`, `R18.1`, `R30.1`, `A22.1`, `X3.2`, `A32.1`, `X3.12` |
| `S_SIN` | `A24.1`, `X3.4`, `D104.4` |
| `S_CTS` | `A25.1`, `X3.5`, `D104.5` |
| `S_DSR` | `A26.1`, `X3.6`, `D104.6` |

## Boundary

- D11 is bus-visible at the decoded `0x08..0x0B` USART window, with
  BA0, DB0-DB7, `IORD`, `IOWR`, and `CS_D11` wired.
- Native sheet 2 sends D57 `OUT0` through `BAUD R.`; native sheet 1
  visibly forks that conductor to D11 TxC and RxC. `PIT_BAUD` is
  source-closed rather than retained as an assumed USART-end fork.
- D11 serial-side pins are carried through the modeled D14/D32/D3/D12
  output drivers and D104 receiver to X3 signal pins. D3.10 reaches
  X3.3 through the explicit W20 assembly-wire closure.
- `sync/serial_check.sh` now proves a scoped USART behavior slice:
  mode/command writes, TxRDY/RxRDY/TxEMPTY status, command-driven
  RTS/DTR, and one 8N1 byte through a digital TxD->RxD loopback.
- D104's fourth receiver input pin 7 is separate from D94.13 (~84 kΩ)
  and preserved as `D104_X4_IN_BOUNDARY`; owner continuity on
  2026-07-21 and the exact-revision drawing close output pin 10 as NC.
- D11 auxiliary pins without a net or explicit NC:
  none; all are dispositioned.
- Native sheet 1 directly loops D11 RxRDY pin14 to PIC IR2 pin20 and
  D11 TxRDY pin15 to PIC IR3 pin21. The separately labeled off-sheet
  `(3)` RxRDY/TxRDY arrows enter IR0/IR1 from the alternate interface;
  those two inputs are replaced by КР1818ВГ93 INTRQ/DRQ on `.009`.
- The same `.009` sheet 1 retains `IR4=(3) TAPE RUN INT`, but the
  complete replacement FDC sheet 3 has no matching continuation.
  The board model therefore preserves only D10.22 as a stale-sheet
  continuity boundary. It is not promoted to NC or connected to a
  guessed FDC source. Exact ekta37 code writes PIC mask `0xDF`, keeping
  IR4 masked while enabling only the frame interrupt on IR5; tape is
  outside the current critical path, but physical continuity remains
  Tier-3 historical evidence.
- Full-resolution sheet 1 proves D11.16 `SYNDET` on the lower S4 throw.
  D11.18 `TXEMPTY` is absent from the drawn USART symbol and is now an
  explicit NC rather than an unresolved functional endpoint.
- External X3 loopback, electrical levels, and full 8251 sync/parity
  modes remain Tier-2 bench/software work after that PCB-truth boundary.
