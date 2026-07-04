# Rev A Sourcing Plan

Goal: make the Rev A board orderable as a JLCPCB factory-assembled board where
practical, while keeping vintage or programmable ICs socketed.

## Assembly Policy

- Target JLCPCB factory assembly for passives, protection parts, connectors,
  sockets, oscillator/reset parts, and any currently available logic parts.
- Use socketed ICs for Z80, ROM, DRAM, 8255, GAL/PAL, and DIP 74HCT logic.
- Prefer factory-installed DIP sockets over factory-installed vintage ICs.
- Treat vintage/NOS ICs as owner-supplied post-assembly insertion unless a
  reliable JLCPCB/LCSC source exists at order time.
- Keep the BOM explicit about `Factory`, `Socketed`, `Manual`, and `NOS`
  responsibilities.

## JLCPCB/LCSC Work Items

JLCPCB's assembly flow uses in-stock parts from its assembly parts library and
supports through-hole/manual or wave-soldered assembly for suitable parts. Use
current JLCPCB/LCSC stock as order-time evidence; do not freeze stock-sensitive
part numbers without rechecking them.

Immediate SKU targets:

- DIP sockets:
  - DIP-40 wide for Z80/8255.
  - DIP-28 wide for 27C256 ROM.
  - DIP-24 wide for GAL22V10 devices.
  - DIP-20 narrow for 74HCT245/573.
  - DIP-16 narrow for 4164 DRAM, 74HCT157/148/166.
  - DIP-14 narrow for 74HCT393/00 and oscillator footprint if socketed.
- Passives:
  - 100 nF decoupling capacitors.
  - 47 uF bulk capacitor.
  - 470 ohm VGA series resistors.
  - 220 ohm keyboard column series resistors.
  - 10k pullups.
  - 0 ohm configuration link.
- Protection and power:
  - +5V resettable PTC fuse.
  - +5V TVS clamp.
  - ATX power connector or adapter header.
  - PS_ON jumper/header and power debug header.
- Clock/reset:
  - 5V oscillator.
  - 5V reset supervisor with verified pinout.
- Connectors:
  - VGA connector or header.
  - Original-keyboard-compatible connector once the pinout/mechanics are locked.
  - Logic analyzer/debug headers.

## External/NOS Work Items

Source these separately unless a current assembly-library option is confirmed:

- Z80 DIP-40 CPU: western Z84C0008/Z84C0020 or compatible real Z80.
- ROM: 27C256-class DIP-28 EPROM; 28C256-compatible EEPROM remains useful for
  development if pin-compatible in the programmed address range.
- DRAM: western 4164-compatible 64K x 1 DIP-16, 150 ns or faster. Initial search
  targets include common 4164 family markings such as 4164-15, KM4164B,
  TMS4164, MCM6665, HYB4164, and equivalent 5V-only parts.
- PPI: 82C55/8255-compatible DIP-40.
- GAL/PAL: GAL22V10-class DIP-24 devices and a programming workflow.

## Current Evidence Notes

- JLCPCB's parts library lists DIP IC sockets as assembly-library parts, so
  factory-installed sockets are plausible for Rev A.
- JLCPCB documentation describes through-hole assembly support for suitable
  parts, including manual or wave-soldered handling.
- DRAM availability is stock-sensitive and should be checked again immediately
  before purchasing; do not rely on stale marketplace listings.

Source links to re-check before ordering:

- JLCPCB parts library: https://jlcpcb.com/parts
- JLCPCB IC/transistor socket category:
  https://jlcpcb.com/parts/2nd/Connectors/IC__Transistor_Socket_2943
- JLCPCB PCB assembly FAQ:
  https://jlcpcb.com/help/article/pcb-assembly-faqs
