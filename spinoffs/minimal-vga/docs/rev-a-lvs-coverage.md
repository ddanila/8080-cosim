# VJUGA Rev A staged full-board LVS coverage

Status date: 2026-07-23.

Status: **STAGE 5 PASS / WHOLE BOARD INCOMPLETE**.

Five independently authored physical-board LVS slices are executable:

```sh
spinoffs/minimal-vga/sync/rev_a_power_clock_reset_lvs.sh
spinoffs/minimal-vga/sync/rev_a_decode_lvs.sh
spinoffs/minimal-vga/sync/rev_a_cpu_rom_lvs.sh
spinoffs/minimal-vga/sync/rev_a_dram_bank_lvs.sh
spinoffs/minimal-vga/sync/rev_a_dram_mux_lvs.sh
```

They compare their structural HDL with `kicad/rev-a-physical.board.json`
through independent maps. Unlike the older eight-instance logical comparison,
these slices model individual physical pads, opt power rails into `sync/lvs.py`,
compare declared no-connect pads, and identify complete (non-boundary)
instances whose every physical pin must remain mapped and owned.
Maps may also name endpoint-closed board nets; every physical endpoint on those
nets must then be present in the projection.

## Closed in stage 1

The comparison maps 17 physical references, marks 16 of them complete, and
matches nine connectivity partitions:

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

## Closed in stage 2

`rev_a_decode_lvs.sh` closes the complete decode PROM/socket/glue group:

- U3 RT4 and U4 RE3 sockets, U5 decode GAL, and U6 mode-bit inverter;
- J94 mode jumper and J95 decode observation header;
- R32-R43 output pull-ups, R44 mode pull-down, and C26-C28 decoupling; and
- every non-power external endpoint those parts touch on U1, U2, U24, U30,
  J97, and J98.

The comparison maps 28 references: 22 completeness-checked decode parts and
six boundary projections. It matches 37 connectivity partitions plus all five
intentional no-connect pads (U5.23 and U6.6/.8/.10/.12). The boundary
projections do not claim full coverage of U1, U2, U24, U30, J97, or J98; they
make the decode nets exact while those devices await their owning stages.
All 35 non-power decode nets are endpoint-closed.

Two temporary mutations are required to fail: moving U3.12 from DEC_ROM_N to
DEC_RAM_N, and deleting the U6.6 no-connect declaration. These prove both
routed-connectivity and intentional-NC sensitivity.

## Closed in stage 3

`rev_a_cpu_rom_lvs.sh` makes U1 Z80, U2 ROM, and their C1/C2 decouplers complete
owned instances. It maps all 40 CPU pins and all 28 ROM pins, including the
CPU's VCC-tied INT_N, NMI_N, and BUSRQ_N inputs and its explicit HALT_N/BUSACK_N
no-connect pads.

The comparison maps 35 references: four complete core parts and 31 exact
boundary projections. It matches 38 connectivity partitions, both intentional
CPU NC pads, and proves all 36 non-power core nets endpoint-closed: A0-A15,
D0-D7, CPU controls, clock/reset/wait, and the three ROM control nets.

Three temporary mutations must fail: moving U1.30 from A0 to A1, deleting the
U1.18 no-connect declaration, and adding an otherwise-unmapped U23.3 endpoint
to A0. The last control proves that endpoint closure rejects a newly introduced
consumer even when the mapped partition itself would otherwise be unchanged.

## Closed in stage 4

`rev_a_dram_bank_lvs.sh` makes U10-U17 and their C6-C13 decouplers complete
owned instances. It maps every pad on all eight 4164-class packages, including
both DIN and DOUT pads on each data bit and the eight explicit pin-1
no-connects used by the selected 4164/РУ5-compatible population.

The comparison maps 25 references: 16 complete bank parts and nine exact
boundary projections. It matches 21 connectivity partitions, all eight NC
pads, and proves all 19 non-power bank nets endpoint-closed: D0-D7,
DRAM_A0-DRAM_A7, RAS_N, CAS_N, and DRAM_WE_N.

Three temporary mutations must fail: moving U10.2 from D0 to D1, deleting the
U10.1 no-connect declaration, and adding an otherwise-unmapped U23.3 endpoint
to DRAM_A0.

## Closed in stage 5

`rev_a_dram_mux_lvs.sh` makes both 74HCT157 address muxes U20/U21 and their
C14/C15 decouplers complete owned instances. It maps every mux pad, including
pin 15 on each device as a second GND endpoint so the corrected active-low
enable cannot return to a floating island. Its endpoint-closed
`REFRESH_ROW3` boundary includes both U22.6 and U22.13, guarding the corrected
low-half-to-high-half refresh-counter cascade.

The comparison maps 19 references: four complete mux parts and 15 exact
boundary projections. It matches 27 connectivity partitions and proves all 25
non-power mux nets endpoint-closed: A0-A7, DRAM_A0-DRAM_A7, ADDRMUX_SEL, and
REFRESH_ROW0-REFRESH_ROW7.

Four temporary mutations must fail: moving U20.2 from A0 to A1, moving U21.4
from DRAM_A4 to DRAM_A5, restoring the former floating U20.15/U21.15
ADDRMUX_OE_N island, and adding an otherwise-unmapped U23.3 endpoint to
ADDRMUX_SEL. Together they prove input, output, corrected-enable power, and
endpoint-closure sensitivity.

## Still open

This is staged progress, not a full-board release disposition. The remaining
physical groups still need independent structural HDL and pin maps:

- U22's static cascade/reset source and route are guarded, but its independent
  complete-instance Stage 6 structural slice, the remaining refresh
  arbitration, and U24 timing are still open;
- the remaining PPI pins, keyboard matrix, and keyboard connector;
- VGA timing, serializer, connector, and resistor path; and
- diagnostic LEDs and the remaining observation headers/boundaries.

Until those groups are compared and a final all-reference aggregate passes—or
the owner records the explicit compensated-review waiver—the whole-board LVS
bare-board gate remains open. The direct contracts in
`kicad/check_rev_a_physical.py` remain useful guards, but do not substitute for
independently authored structural LVS.
