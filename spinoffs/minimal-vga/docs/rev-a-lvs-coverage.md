# VJUGA Rev A structural LVS coverage

Status: **NINE SLICES PASS / WHOLE BOARD INCOMPLETE**.

The slices compare independently authored structural HDL with
`kicad/rev-a-physical.board.json` through explicit pin maps. They check model
connectivity, including power nets and declared no-connect pads. They do not
read the routed PCB or establish copper continuity.

## Coverage and commands

Run the listed scripts from the repository root. Each lives under
`spinoffs/minimal-vga/sync/`; its matching `rev_a_<name>_map.json` defines exact
pins and boundary projections, and `hdl/rev_a_<name>_lvs.v` defines the structural
model. A runner returns `SKIP` with exit zero when Yosys is unavailable; verify
that the comparison actually ran.

| Slice / runner | Complete physical instances |
| --- | --- |
| [Power, clock and reset](../sync/rev_a_power_clock_reset_lvs.sh) | J1, J3, F1, D1, C50, R6, R30/R31; U50/U51, R4/R5, J96, C24/C25; J93 |
| [Decode](../sync/rev_a_decode_lvs.sh) | U3/U4 PROM sockets, U5 GAL, U6 inverter, J94/J95, R32–R44, C26–C28 |
| [CPU and ROM](../sync/rev_a_cpu_rom_lvs.sh) | U1/U2, C1/C2 |
| [DRAM bank](../sync/rev_a_dram_bank_lvs.sh) | U10–U17, C6–C13 |
| [DRAM address muxes](../sync/rev_a_dram_mux_lvs.sh) | U20/U21, C14/C15 |
| [Refresh counter](../sync/rev_a_refresh_counter_lvs.sh) | U22, C16 |
| [Empty spare socket](../sync/rev_a_spare_socket_lvs.sh) | U23 (DNP), C17 |
| [DRAM timing](../sync/rev_a_dram_timing_lvs.sh) | U24, C18 |
| [PPI](../sync/rev_a_ppi_lvs.sh) | U30, C19 |

“Complete” requires every physical pin of that instance to be mapped and owned.
Other mapped instances are partial boundary projections. All slices except
power/clock/reset also require every endpoint on the non-power nets touched by
their complete instances to be in the map. The comparator checks partitions of
instance/pad endpoints, so matching net names alone cannot satisfy LVS.

The runners test temporary defective board models and require mismatches:
miswired pads, incorrect no-connect declarations and, where endpoint closure is
required, added unmapped consumers. Exact mutations and expected diagnostics
live in the scripts; the committed board model is not modified.

## Important physical-model constraints

- J3's duplicated VBUS, GND and shield contacts have unique pad identities.
- U1's INT_N, NMI_N and BUSRQ_N inputs are tied to VCC; HALT_N and BUSACK_N
  are explicitly NC. Each DRAM package has separate DIN/DOUT pads and an NC
  pin 1 for the selected 4164/РУ5-compatible population.
- U20/U21 active-low enables (pin 15) and U22 active-high reset inputs
  (pins 2/12) are grounded. U22.6 clocks U22.13 for the refresh cascade.
- The unpopulated U23 socket retains CLK on pin 1, grounded pins 2/7/12/13,
  VCC on pin 14 and eight NC outputs.
- U24 pin 13 is `DECODE_WAIT_N`; pins 21–23 are state-feedback macrocells
  declared PCB NC. Its behavior and timing have a separate guard:
  `spinoffs/minimal-vga/sim/u24_dram_timing_check.sh`.
- U30's column-driver boundary ends at R16–R23 pin 1; encoded-row inputs
  end at U31. This does not cover the complete keyboard network.

## Remaining coverage and release boundary

Independent structural HDL and pin maps are still required for:

- the remaining U31 encoder, resistor-to-J30 keyboard matrix and connector;
- U40 VGA timing interface, U41 serializer, J40 connector and resistor path;
- diagnostic LEDs and remaining observation headers/boundaries;
- decouplers C3–C5 and C20–C23, which have no complete-instance owner.

The whole-board LVS bare-board gate remains open until those groups and a final
all-reference aggregate pass, or the owner records the explicit compensated-review
waiver. Direct contracts in `kicad/check_rev_a_physical.py` do not substitute for
independent structural LVS. Routing, DRC, package freshness and physical acceptance
remain separate gates; see [manufacturing readiness](rev-a-manufacturing-readiness.md).
