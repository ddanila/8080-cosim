# VJUGA Rev A scarce-chip workbench

Status: **REV-A MODEL RETAINED / PHYSICAL CHIP QUALIFICATION PENDING**

Rev A is the single-board fixture for exercising original Juku DRAM and D6
memory decode, and observing D8 outputs. It remains a simulation and bench reference;
the current first-article order is controlled by
[the Rev B five-board plan](rev-b-five-board-order-plan.md). Rev A's completed
software steps do not establish fabricated hardware or order readiness.

## Retained implementation

`hdl/vjuga_juku_top.v` uses the Verilog tv80 Z80 core and the root project's
`hdl/devices.v` models for К565РУ5 DRAM, D6 `.038` memory decode and D8 `.039`
ROM paging. The boot guard compares the framebuffer with cosim in both decode
modes at a selected write count (default `WRITES=6000`). That bounded comparison
does not establish a completed banner or full RAM test. The earlier VHDL top
remains a POC reference.

The fixture provides two GAL22V10 decode modes:

- Mode A supplies internal ROM/RAM decode with the scarce PROM sockets empty.
- Mode B uses D6's active-low `ROM_N` output for ROM selection; the internal
  ROM-selection boolean is its inverse. Both modes instantiate D8, but its
  output byte is unused and the boot guard does not check it. Physical D8
  acceptance requires a separate output-table capture.

U10–U17 are 4164-class DIP-16 sockets; KM4164B-10 is the western baseline.
U2 uses the 28C256 pin contract with the patched `ekta37_z80` image; alternate
EPROMs require compatibility review. Original D15/D16 EPROMs, FDC parts and
the D2 WAIT/READY PROM are outside the implemented fixture's scope.
See [the chip map](rev-a-chip-map.md),
[GAL equations](rev-a-gal-equations.md) and
[power budget](rev-a-power-budget.md) for the physical contract.

Nine physical LVS slices cover power/clock/reset, decode, CPU/ROM, DRAM bank,
address mux, refresh counter, spare socket, DRAM timing and PPI. Their exact
commands, endpoint scope and negative controls belong to
[the LVS coverage report](rev-a-lvs-coverage.md). Whole-board LVS remains
incomplete; the slices cannot substitute for its release requirement.

## Reproduction

From the repository root:

```sh
spinoffs/minimal-vga/sim/vjuga_boot_check.sh
```

Run the physical LVS commands listed in the coverage report when changing
Rev A connectivity. A software pass does not qualify a socketed physical part.

## Physical bench acceptance

[The bring-up procedure](phase4-bench-bringup.md) owns capture profiles,
clock-control headers, single-step wiring and per-board records. Keep the
western Mode A baseline first, then insert one scarce chip at a time.

Record board/part identity, settings, capture files and failures with each
physical result. Release requires independently reviewed schematic/copper,
complete connectivity evidence, fresh DRC and package review. Bench completion
uses the bring-up procedure's exit criteria: completed baseline banner,
recorded DRAM and D6 boot-workload comparisons, and a matching observed D8 table.
These are bounded physical results; full chip qualification remains separate.
