# Serial handoff

Status: **SERIAL CORE GUARDED / PHYSICAL LEVELS PENDING**

This generated report separates the serial-port facts already guarded by
the board JSON and HDL from the remaining functional serial boundary.
It covers the D11 8251 host bus path, the D57 baud-clock handoff, and
the X3 line-driver/receiver wiring. It checks code markers for a minimal
bus-visible 8251-style async Tx/Rx slice with separate transmit holding
and shift stages; it does not claim
external X3 loopback or full protocol-mode coverage.

## Command

Run from the repository root with Python 3. The generator overwrites
`docs/serial-handoff.md`, including when a checked invariant fails.

```sh
python3 scripts/report_serial_handoff.py
```

The generator checks JSON endpoint and provenance invariants, selected HDL
and test-source markers, and recorded diagnostic evidence. It does not
run the USART simulation, perform LVS, inspect PCB copper, or measure
line levels. For device behavior, run the guard from the repository root
with Bash, Python 3, and Icarus Verilog (`iverilog` and `vvp`):

```sh
sync/serial_check.sh
```

The guard uses temporary simulation files and regenerates this report
after the USART simulation passes.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| D11 is the board USART | PASS | board JSON |
| D11 complete auxiliary pin contract is exposed | PASS | КР580ВВ51А/8251 datasheet contract |
| D11 TXEMPTY is source-proved NC | PASS | full-resolution sheet-1 omits pin 18 from the drawn USART symbol |
| D11 power-pin endpoints are modeled | PASS | D11.4 GND / D11.26 +5V |
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
| D13 reset inverter is assigned and only section 11->10 remains unused | PASS | sheet-1 plus owner continuity use sections 1->2, 3->4, 5->6, 9->8, and 13->12; only 11->10 is unused |
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
| UP2 fourth receiver output is owner-closed NC | PASS | D104.7 reaches R30 lower on visible front copper; source assigns that pad to GND, pending owner-board rail measurement; D104.10 is NC |
| S_SOUT reaches X3.9 | PASS | `S_SOUT` |
| S_RTS reaches X3.10 | PASS | `S_RTS` |
| S_DTP reaches X3.11 | PASS | `S_DTP` |
| S_TTL reaches X3.3 | PASS | `S_TTL` |
| S_OC reaches X3.12 | PASS | `S_OC` |
| S_SIN reaches X3.4 | PASS | `S_SIN` |
| S_CTS reaches X3.5 | PASS | `S_CTS` |
| S_DSR reaches X3.6 | PASS | `S_DSR` |
| X3.7 is signal ground on CS00015 | PASS | owner continuity, 2026-08-01 |
| Factory wire W20 closes D3.10 to the S_TTL connector island | PASS | assembly wire W20; `S_TTL_D3` -> `S_TTL` |
| USART model and loopback test contain required code markers | PASS | `hdl/devices.v`; `hdl/sim/usart_8251_tb.v`; `sync/serial_check.sh` |
| HDL serial connector and drivers are instantiated | PASS | `hdl/juku_top.v` |

## Serial Nets

| Net | Endpoints |
| --- | --- |
| `CS_D11` | `D9.13`, `D11.11` |
| `RESET` | `D13.6`, `D1.12`, `D26.35`, `D27.35`, `D11.21`, `D13.9` |
| `D13_4_D105_2` | `D13.4`, `D105.2`, `D11.20`, `D30.11` |
| `PIT_BAUD` | `D57.10`, `D11.25`, `D11.9` |
| `SER_TXD` | `D11.19`, `D14.3`, `D3.11`, `D3.9`, `R18.2` |
| `SER_TXD_INV` | `D3.8`, `D12.1`, `D12.2` |
| `SER_RTS` | `D11.23`, `D32.3` |
| `SER_DTR` | `D11.24`, `D32.2` |
| `SER_RXD` | `D11.3`, `D104.13` |
| `SER_CTS_N` | `D104.12`, `D11.17` |
| `SER_DSR_N` | `D104.11`, `D11.22` |
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
- Owner continuity on Arvutimuuseum machine `CS00015` identifies X3 pin 7 as
  signal ground.  This closes the ground contact for the current diagnostic
  cable; it does not silently rewrite the still-separate generic A27 harness
  boundary in the reconstructed PCB without a corresponding board-side chase.
- `sync/serial_check.sh` tests a scoped USART behavior slice:
  mode/command writes, the `TxRDY=0,TxEMPTY=0` holding-full state,
  the `TxRDY=1,TxEMPTY=0` holding-to-shift transition, final
  `TxEMPTY=1`, RxRDY, command-driven RTS/DTR, and one 8N1 byte
  through a digital TxD->RxD loopback with active-low CTS asserted.
  PTY attachment likewise represents an attached harness with CTS
  active; on hardware the Nano/level-shifter must drive X3 CTS low
  before reset because an open MC1489-class input yields inactive CTS.
  This follows the [Intel 8251A datasheet](https://community.intel.com/cipcp26785/attachments/cipcp26785/programmable-devices/89914/1/P8251A.pdf)
  CTS gating and the [TI MC1489 datasheet](https://www.ti.com/lit/ds/symlink/mc1489a.pdf)
  open-input output guarantee.
- D104's fourth receiver input pin 7 is separate from D94.13 (~84 kΩ).
  The marked notch-down package has an uninterrupted front copper path
  from pin 7 to R30's lower pad. The exact-source model assigns that
  pad to ground; owner-board rail polarity still needs a meter check.
  Exact `.009` sheet 1 draws only
  sections 4→13, 5→12, and 6→11, omitting the fourth 7→10 section; direct
  owner continuity on 2026-07-21 closes output pin 10 as NC. A D11-local fit
  photo-registers its package but does not prove pin 7's rail. The ground
  assignment uses component copper and R30's source endpoint.
- D11 auxiliary pins without a net or explicit NC:
  none; all are dispositioned.
- Native sheet 1 directly loops D11 RxRDY pin14 to PIC IR2 pin20 and
  D11 TxRDY pin15 to PIC IR3 pin21. The separately labeled off-sheet
  `(3)` RxRDY/TxRDY arrows belong to the alternate interface. Exact `.009`
  sheet 1 source-closes IR0 to X2.214 and IR1 to X2.218/D27 PB7.
  They are separate from the sheet-3 FDC conditioner; direct FDC-to-PIC
  assignments must not be inferred from the older behavioral model.
- The same `.009` sheet 1 retains `IR4=(3) TAPE RUN INT`, but the
  complete replacement FDC sheet 3 has no matching continuation.
  D10.22 remains an unmatched endpoint, not an NC or inferred FDC input.
  Its front route is obscured by cable/adhesive and no solder-side departure
  is exposed. With power removed, probe pin 22 near `(2456,1305)` in `200415237` or
  `(3438,1028)` in `200522685`; image identities and row anchors are in the
  [D10 photo registration](../ref/photos/juku-pcb-2/local-package-registration.json).
  The recorded ekta37 mask `0xDF` enables only frame IR5 and masks IR4;
  it does not resolve the physical continuation.
- Wired USART ready signals do not establish interrupt service in the
  runnable HDL: its PIC is a register stub, and the separate `intr_ctl`
  helper services the synthetic frame tick only. Cosim services USART
  IR2/IR3 as well; see [interrupt behavior](hardware-map.md#interrupt-and-keyboard-behavior).
- Full-resolution sheet 1 proves D11.16 `SYNDET` on the lower S4 throw.
  D11.18 `TXEMPTY` is absent from the drawn USART symbol and modeled NC.
- External X3 loopback, electrical levels, and full 8251 sync/parity
  modes remain Tier-2 bench/software work after that PCB-truth boundary.
