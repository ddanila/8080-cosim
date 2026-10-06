# VJUGA simulation and model checks

From the repository root, `spinoffs/minimal-vga/sim/check.sh` runs the broad
aggregate: shared replica boot, T80 smoke and real-ROM boot, tv80 boot in both
decode modes, the Rev B tier suite, framebuffer-readback validation, U24 DRAM
timing, logical LVS, nine Rev A physical-design JSON/HDL LVS slices, and
Rev A PCB/package checks.

Initialize the T80/tv80 submodules before running the aggregate. Both the tv80
boot guard and framebuffer-readback guard exit successfully with `SKIP` when
their core is absent; aggregate success alone does not prove every listed
check ran. The aggregate stops at the first failing command, so a failure in
the full Rev B suite prevents the later readback, U24 and Rev A checks from
running. Use their individual entry points when reviewing those results.

The aggregate requires Bash, Python 3, a C compiler, Icarus Verilog, GHDL
with Synopsys IEEE package support, and Yosys. Its physical checks also use
KiCad CLI, KiCad Python and footprint libraries; the full Rev B tier has the
additional dependencies listed in [its execution guide](../docs/rev-b-execution-guide.md#verification-commands).
It regenerates schematic/netlist and report outputs and overwrites
`cosim/vram.bin`. Save any framebuffer you need and inspect the working-tree
diff afterward. This aggregate is broader than hosted CI.

## Rev B entry points

```sh
spinoffs/minimal-vga/sim/revb_tier_suite.sh --ci
spinoffs/minimal-vga/sim/revb_tier_suite.sh
```

`--ci` runs the behavioral smoke subset: commons/completeness checks, named ROM
freshness, card and bus tests, bring-up, serial console, PIT/POST expansion,
EKTA decode modes and video. `REVB_CI_GROUP=cards` or `system` selects its
corresponding subset. The default suite also runs local CAD/release checks.
See the [execution guide](../docs/rev-b-execution-guide.md) for required tools,
skip behavior and generated-file/framebuffer side effects. Suite success alone
does not qualify fabrication.

The Rev B video guard covers chip-level TTL timing and the framebuffer path.
The serial and I/O guards use hardware-rate clock/framing fixtures and negative
controls. These are modeled results, not measurements of assembled hardware.
The video crop check inspects the existing `cosim/vram.bin`; it does not
regenerate or identify its workload, and skips an absent or wrongly sized file.
Generate the intended oracle framebuffer first before citing crop coverage.
Without Icarus Verilog, the video guard also skips its HDL tests and returns
success marked `partial`.
[The five-board plan](../docs/rev-b-five-board-order-plan.md) owns current order
and first-article requirements.

## Retained Rev A scope

The T80 synthetic program exercises RAM, I/O, refresh arbitration, keyboard-like
input and VGA timing. The real-ROM T80/tv80 guards compare framebuffer writes
with cosim; they do not establish a physical shared-DRAM VGA banner.
U24's timing reference is guarded against the vendored MK4564-12 limits at
4 MHz. Device-specific GAL programming and physical chip qualification belong
to [the Rev A fixture guide](../docs/workbench-plan.md) and its linked bench
procedure. Passing simulation, LVS or package checks does not prove a physical
board works. The Rev A LVS slices compare mapped endpoints in
`rev-a-physical.board.json` with structural HDL; routed copper is checked
separately by the PCB gates.
