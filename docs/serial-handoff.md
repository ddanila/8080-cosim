# Serial handoff

Status: **SERIAL BUS-SIDE HANDOFF READY / PROTOCOL BOUNDARY**

This generated report separates the serial-port facts already guarded by
the board JSON and HDL from the remaining functional serial boundary.
It covers the D11 8251 host bus path, the D57 baud-clock handoff, and
the X3 line-driver/receiver wiring. It does not claim a complete 8251
protocol engine or an external loopback proof.

## Command

```sh
python3 scripts/report_serial_handoff.py
```

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| D11 is the board USART | PASS | board JSON |
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
| D57 baud output reaches D11 TxC/RxC | PASS | `PIT_BAUD` |
| USART TxD fans to line drivers | PASS | `SER_TXD` |
| USART RTS/DTR reach AP2 driver | PASS | `SER_RTS` / `SER_DTR` |
| USART RxD comes from UP2 receiver | PASS | `SER_RXD` |
| S_SOUT reaches X3.29 | PASS | `S_SOUT` |
| S_RTS reaches X3.30 | PASS | `S_RTS` |
| S_DTP reaches X3.51 | PASS | `S_DTP` |
| S_TTL reaches X3.23 | PASS | `S_TTL` |
| S_OC reaches X3.32 | PASS | `S_OC` |
| S_SIN reaches X3.33 | PASS | `S_SIN` |
| HDL USART shell exposes idle serial outputs | PASS | `hdl/devices.v` |
| HDL serial connector and drivers are instantiated | PASS | `hdl/juku_top.v` |

## Serial Nets

| Net | Endpoints |
| --- | --- |
| `CS_D11` | `D9.13`, `D11.11` |
| `PIT_BAUD` | `D57.10`, `D11.25`, `D11.9` |
| `SER_TXD` | `D11.19`, `D14.3`, `D3.11`, `D12.1` |
| `SER_RTS` | `D11.23`, `D32.3` |
| `SER_DTR` | `D11.24`, `D32.2` |
| `SER_RXD` | `D11.3`, `D104.2` |
| `S_SOUT` | `D14.6`, `X3.29` |
| `S_RTS` | `D32.6`, `X3.30` |
| `S_DTP` | `D32.7`, `X3.51` |
| `S_TTL` | `D3.10`, `X3.23` |
| `S_OC` | `D12.3`, `X3.32` |
| `S_SIN` | `X3.33`, `D104.1` |

## Boundary

- D11 is bus-visible at the decoded `0x08..0x0B` USART window, with
  BA0, DB0-DB7, `IORD`, `IOWR`, and `CS_D11` wired.
- D57 `OUT0` reaches both D11 clock inputs through `PIT_BAUD`.
- D11 serial-side pins are carried through the modeled D14/D32/D3/D12
  output drivers and D104 receiver to X3 signal pins.
- The current HDL USART shell is intentionally boot-safe: bus registers
  latch and read back, while serial-side outputs idle. A real 8251
  transmit/receive engine and external loopback remain future Tier-2
  functional work, not PCB-truth blockers.
