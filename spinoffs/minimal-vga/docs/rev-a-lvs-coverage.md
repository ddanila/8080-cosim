# VJUGA Rev A staged full-board LVS coverage

Status date: 2026-07-23.

Status: **STAGE 1 PASS / WHOLE BOARD INCOMPLETE**.

The first independently authored physical-board LVS slice is now executable:

```sh
spinoffs/minimal-vga/sync/rev_a_power_clock_reset_lvs.sh
```

It compares `hdl/rev_a_power_clock_reset_lvs.v` with
`kicad/rev-a-physical.board.json` through
`sync/rev_a_power_clock_reset_map.json`. Unlike the older eight-instance
logical comparison, this slice models individual physical pads and opts power
rails into `sync/lvs.py`.

## Closed in stage 1

The comparison maps 17 physical references and matches nine connectivity
partitions:

- the complete PCB placement `POWER` block: J1, J3, F1, D1, C50, R6, R30,
  and R31;
- the complete PCB placement `CLOCK_RESET` block: U50, U51, R4, R5, J96, C24,
  and C25;
- the J93 power-debug header; and
- U1 pins 6, 11, 26, and 29 as the external CLK, VCC, RESET_N, and GND
  boundary.

The modeled partitions are VCC_RAW, VCC, GND, USB_CC1, USB_CC2, PWR_OK,
OSC_OE_N, CLK, and RESET_N. Net names do not establish a match; the comparator
checks the partition of mapped instance/pad endpoints. J3's duplicated VBUS,
GND, and shield contacts have unique logical pad names, so one missing or
mis-bound contact cannot hide behind another contact on the same net.

The runner also makes a temporary copy of the board model, moves J3.A9 from
VCC_RAW to GND, and requires LVS to fail. This mutation is the negative control
for both physical-pad sensitivity and the opt-in power-net path. The committed
board is never modified.

## Still open

This is staged progress, not a full-board release disposition. The remaining
physical groups still need independent structural HDL and pin maps:

- CPU bus, ROM, GAL decode, and the full RT4/RE3 socket path;
- DRAM bank, address multiplexing, refresh, arbitration, and U24 timing;
- PPI, keyboard matrix, and I/O decode;
- VGA timing, serializer, connector, and resistor path; and
- diagnostic LEDs and the remaining observation headers/boundaries.

Until those groups are compared and a final all-reference aggregate passes—or
the owner records the explicit compensated-review waiver—the whole-board LVS
bare-board gate remains open. The direct contracts in
`kicad/check_rev_a_physical.py` remain useful guards, but do not substitute for
independently authored structural LVS.
