# VJUGA Rev A scarce-chip workbench

Status: **REV-A MODEL RETAINED / PHYSICAL CHIP QUALIFICATION PENDING**

Rev A is the single-board fixture for exercising original Juku DRAM and
PROMs in their functional roles. It remains a simulation and bench reference;
the current first-article order is controlled by
[the Rev B five-board plan](rev-b-five-board-order-plan.md). Rev A's completed
software steps do not establish fabricated hardware or order readiness.

## Retained implementation

`hdl/vjuga_juku_top.v` uses the Verilog tv80 Z80 core and the root project's
`hdl/devices.v` models for К565РУ5 DRAM, D6 `.038` memory decode and D8 `.039`
ROM paging. The boot guard compares the framebuffer with cosim at the bounded
and full-banner write counts. The earlier VHDL top remains a POC reference.

The fixture provides two GAL22V10 decode modes:

- Mode A supplies internal ROM/RAM decode with the scarce PROM sockets empty.
- Mode B conditions the real D6/D8 socket outputs. D6's active-low `ROM_N`
  output is inverted when deriving the internal ROM-selection boolean.

U10–U17 are 4164-class DIP-16 sockets; KM4164B-10 is the western baseline.
The ROM socket carries the 27C256 `ekta37_z80` image. Testing original D15/D16
EPROMs and FDC parts is outside this fixture's scope. D2 WAIT/READY is optional.
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

| Part | Functional role | Required observation |
| --- | --- | --- |
| К565РУ5 | DRAM bank | boot RAM test passes and captured framebuffer matches cosim |
| D8 К155РЕ3 `.039` | ROM pager | expected socket selects and successful boot |
| D6 К556РТ4 `.038` | memory decode | J95.1/D6.12 is low during reset ROM selection; correct overlay and boot in Mode B |
| D2 К556РТ4 `.037` | optional WAIT/READY | correct DRAM-access wait timing |

Record board/part identity, settings, capture files and failures with each
physical result. Release requires independently reviewed schematic/copper,
complete connectivity evidence, fresh DRC and package review. Bench completion
requires the assembled baseline banner plus at least one physically passing
DRAM, РТ4 and РЕ3 in their functional roles. Completed development stages and
resolved sequencer bugs are retained in Git history.
