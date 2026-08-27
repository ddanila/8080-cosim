# VJUGA rev B — TTL serial console contract

Status: **R5.S2 electrical boundary implemented and desk-verified 2026-08-27**.

The I/O card's 8251 is the only UART. Its TX/RX signals travel on base-bus pins
35/36 to a protected, board-relative four-pin header on the backplane. This is a
bidirectional 8N1 TTL console for an ordinary USB-UART adapter. It is not an
RS-232 electrical interface and must never be connected to a DB9 RS-232 port.

## Header, jumper and host wiring

| `J_TTL` pin | Board signal | Connect to USB-UART | Rule |
|---:|---|---|---|
| 1 | `VCC_SENSE` | normally leave open | Output/reference only through 10 kΩ + blocking diode; never power VJUGA here |
| 2 | `BOARD_TX` | adapter RX | VJUGA output, divided to the 3.3 V domain |
| 3 | `BOARD_RX` | adapter TX | VJUGA input, 3.3 V and 5 V TTL accepted |
| 4 | GND | adapter GND | Common reference |

`JP_S5` takes two shunts. Fit 1–2 to connect bus TX to the protected board-TX
channel, and 3–4 to connect the protected board-RX channel to bus RX. Remove both
to isolate the external connector. With both fitted, a temporary `J_TTL` 2–3
link is an 8251 external loopback; remove power before changing shunts.

`JP_BAUD` is on the I/O card:

| Shunt | 8251 TxC/RxC | Console setting |
|---|---:|---|
| 1–2 (default) | 307.2 kHz | 19,200 baud, 8N1, x16 clock |
| 2–3 | 153.6 kHz | 9,600 baud, 8N1, x16 clock |

## Exact circuit

- `U3`: ECS `ECS-2200B-049`, 4.9152 MHz, 5 V, half-size DIP-8 can. `U7`
  (`SN74HC393N`) divides it by 16 and 32. The arithmetic is exact:
  4,915,200 / 16 / 16 = 19,200 and 4,915,200 / 32 / 16 = 9,600.
- `U_CON`: `SN74HCT125N`, 5 V PDIP-14. Channel 1 buffers 8251 TX; channel 2
  receives adapter TX. Its TTL-compatible input guarantees high at 2.0 V and low
  at 0.8 V, so a conservative 3.0/0.4 V 3.3 V adapter output has margin. The two
  unused channels are disabled and their inputs are tied low.
- Board TX uses 1.0 kΩ top / 1.8 kΩ bottom. From the HCT guaranteed 3.7 V high
  through the 5.5 V rail maximum, the connector high range is 2.379–3.536 V.
  That exceeds a conservative 2.31 V 3.3 V-CMOS receive threshold without
  exceeding a 3.6 V input limit. Divider current is at most 1.964 mA, below the
  HCT output rating.
- Board RX passes through 1.0 kΩ to the HCT input and has a 10 kΩ pull-up, so a
  disconnected adapter leaves the 8251 idle-high. The series part limits fault
  and contention current.
- Pin 1 receives board 5 V only through 10 kΩ and a `1N4148` oriented from the
  board toward the header. An adapter voltage therefore reverse-biases the diode
  instead of back-powering VJUGA. Treat the pin as sense-only.
- `C_CON` and the I/O card's new counter capacitor provide 100 nF at each added
  IC. The I/O card now carries one 100 nF capacitor per fitted-or-DNP IC.

Exact order identities for this circuit are `SN74HCT125N`, `SN74HC393N`,
`ECS-2200B-049`, Vishay `1N4148-TAP`, and Yageo DIN0207
`MFR-25FBF52-1K`, `MFR-25FBF52-1K8`, and `MFR-25FBF52-10K`. Headers are
Samtec `TSW-104-07-G-S` (`J_TTL`), `TSW-103-07-G-S` (`JP_BAUD`) and
`TSW-102-07-G-D` (`JP_S5`) with `SNT-100-BK-G` shunts. R5.V4/J3 must
reconfirm availability before package release; substituting a footprint-critical
part requires rerunning the physical-contract gate.

The numeric contract is machine-readable in `kicad/revb/serial-electrical.json`
and checked with `check_revb_serial_electrical.py`.

## Primary sources

- [TI SN74HCT125 product and datasheet](https://www.ti.com/product/SN74HCT125)
- [TI SN74HC393 product and datasheet](https://www.ti.com/product/SN74HC393)
- [ECS-2200X oscillator family](https://ecsxtal.com/products/oscillators/through-hole-oscillators/ecs-2200x/)
- [Vishay 1N4148 datasheet](https://www.vishay.com/docs/81857/1n4148.pdf)

## Acceptance commands

```sh
python3 spinoffs/minimal-vga/kicad/revb/gen_revb_boards.py
python3 spinoffs/minimal-vga/kicad/revb/check_revb_serial_contract.py
python3 spinoffs/minimal-vga/kicad/revb/check_revb_serial_electrical.py
python3 scripts/check_revb_boards.py --completeness
```
