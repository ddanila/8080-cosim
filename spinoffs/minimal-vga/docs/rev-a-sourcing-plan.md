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
- For the assembly BOM, do not include Z80, ROM, DRAM, 8255, GAL/PAL, or other
  socketed ICs as factory-populated IC parts. Include sockets only; insert the
  ICs manually later.
- Keep the BOM explicit about `Factory`, `Socketed`, `Manual`, and `NOS`
  responsibilities.
- Generate the JLCPCB upload BOM/CPL from the PCB with
  `spinoffs/minimal-vga/kicad/export_jlcpcb_assembly.py`; do not upload the
  engineering BOM directly.
- In the generated JLCPCB BOM, socketed `U*` designators mean "mount this
  socket here". The matching `post-assembly-insertion.csv` file records which
  owner-supplied IC goes into each socket after factory assembly.

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
  - DIP-16 narrow for 4164 DRAM, 74HCT157/148/166.
  - DIP-14 narrow for 74HCT393/00 and oscillator footprint if socketed.
- Passives:
  - 100 nF decoupling capacitors.
  - 47 uF bulk capacitor.
  - 470 ohm VGA series resistors.
  - 220 ohm keyboard column series resistors.
  - 10k pullups.
  - 0 ohm configuration link.
  - 2.2k diagnostic LED resistors.
  - 3 mm diagnostic LEDs.
- Protection and power:
  - +5V resettable PTC fuse.
  - +5V TVS clamp.
  - 2-pin +5V/GND terminal/header.
  - Power-only USB-C receptacle with 5.1k CC pulldowns.
  - Power debug header.
- Clock/reset:
  - 5V oscillator.
  - 5V reset supervisor with verified pinout.
- Connectors:
  - 1x06 VGA bring-up header; HD-15 adapter is external for Rev A.
  - Original-keyboard-compatible connector once the pinout/mechanics are locked.
  - Logic analyzer/debug headers.

## Current Candidate Assignments

These are order-time candidates, not a blanket approval to upload without a
final JLC/LCSC stock and footprint check.

- DIP sockets:
  - DIP-14 narrow: `C2325`.
  - DIP-16 narrow: `C2326`.
  - DIP-24 wide: `C72120`.
  - DIP-28 wide: `C72121`.
  - DIP-40 wide: `C2332`.
- Power/connectors:
  - USB-C power-only receptacle: HRO `TYPE-C-31-M-17`, JLC/LCSC `C283540`.
  - +5V terminal candidate: KANGNEX `WJ2EDGR-5.08-02P-14-00A`, `C8383`.
    The PCB footprint is nominally 5.00 mm, so verify 5.08 mm fit before
    upload.
- Passives and indicators:
  - 100 nF P=5 mm ceramic decoupler: SHM `DCS104Z26Y5VF6BL5A0`, `C2896070`.
  - 10k axial pullup: TyoHM `RN1/4W10KFT/BA1`, `C410695`.
  - 220 ohm axial series resistor: TyoHM `RN 1/4W 220R F T/B A1`, `C410657`.
  - 470 ohm VGA resistor candidate: VO `CR1/4W-470R` class, `C2896817`.
  - 2.2k LED resistor candidate: YAGEO `MFR-25FBF52-2K2`, `C3454390`.
  - 5.1k USB-C CC pulldown candidate: TyoHM `RN 1/8W 5K1 F T/B A1`,
    `C433473`. This is electrically fine but mechanically smaller than the
    current DIN0207 footprint.
  - 3 mm red diagnostic LED baseline: EVERLIGHT `204-10SURD/S530-A3`,
    `C99772`.
- Protection/reset:
  - Resettable fuse candidate: Littelfuse `RXEF300`, `C14397`; 3 A hold,
    6 A trip. Verify lead spacing and final +5V load before order.
  - Reset supervisor candidate: Microchip `MCP130-460DI/TO`, `C621481`;
    verify TO-92 D-bondout pin order against the KiCad footprint before order.

Rows deliberately left manual in the Rev A draft assembly package:

- `C50`: exact 47 uF radial part for `CP_Radial_D5.0mm_P2.00mm` still needs
  order-time selection or a footprint change.
- `D1`: 5 V TVS for current DO-35/SOD27 footprint. Available 5 V candidates
  are easier in DO-15 or SMA, so this likely needs a footprint decision before
  factory assembly.
- `J30`, `J40`, `J90-J93`, `U40`: exact 2.54 mm vertical header CPNs still
  need selection. These are safe to hand-install for Rev A bring-up.
- `R6`, `R15`: exact axial 0 ohm jumpers still need selection. These can be
  hand-installed for Rev A if no factory 0R axial part is chosen.
- `U50`: DIP-14 5 V oscillator, or a deliberate PCB change to a common SMD
  oscillator footprint. Manual oscillator install is acceptable for Rev A
  bring-up.

## External/NOS Work Items

Source these separately unless a current assembly-library option is confirmed:

- Z80 DIP-40 CPU: ordered `Z0840004PSC`, 4 MHz, owner-supplied insertion after
  socket assembly.
- ROM: 27C256-class DIP-28 EPROM; 28C256-compatible EEPROM remains useful for
  development if pin-compatible in the programmed address range.
- DRAM: ordered Samsung `KM4164B-10`, western 4164-compatible 64K x 1 DIP-16,
  100 ns, +5V-only, owner-supplied insertion after socket assembly.
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
- USB-C `TYPE-C-31-M-17` candidate:
  https://jlcpcb.com/partdetail/Korean_HropartsElec-TYPE_C_31_M17/C283540
- KANGNEX 5.08 mm 2-pin terminal candidate:
  https://www.lcsc.com/product-detail/C8383.html
- Through-hole resistor category:
  https://www.lcsc.com/category/1203.html
- Through-hole ceramic capacitor candidate:
  https://jlcpcb.com/partdetail/SHM-DCS104Z26Y5VF6BL5A0/C2896070
- 3 mm LED candidate:
  https://www.lcsc.com/product-detail/C99772.html
- Resettable fuse category:
  https://jlcpcb.com/parts/2nd/Circuit_Protection/Resettable_Fuses_3294
- Reset supervisor category:
  https://jlcpcb.com/parts/2nd/Power_Management_%28PMIC%29/Supervisor_and_Reset_ICs_3202
- JLCPCB IC/transistor socket category:
  https://jlcpcb.com/parts/2nd/Connectors/IC__Transistor_Socket_2943
- JLCPCB PCB assembly FAQ:
  https://jlcpcb.com/help/article/pcb-assembly-faqs
- JLCPCB BOM file guide:
  https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly
- JLCPCB BOM/CPL preparation advice:
  https://jlcpcb.com/help/article/advice-for-bom-and-cpl-files-preparation
- JLCPCB KiCad BOM/CPL export guide:
  https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad
