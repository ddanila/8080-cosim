# VJUGA simulation and model checks

From the repository root, `spinoffs/minimal-vga/sim/check.sh` runs the broad
aggregate: shared replica boot, T80 smoke and real-ROM boot, tv80 boot in both
decode modes, the Rev B tier suite, framebuffer-readback validation, U24 DRAM
timing, logical LVS, nine Rev A physical LVS slices and Rev A PCB/package checks.

## Rev B entry points

```sh
spinoffs/minimal-vga/sim/revb_tier_suite.sh --ci
spinoffs/minimal-vga/sim/revb_tier_suite.sh
```

`--ci` runs the behavioral smoke subset: commons/completeness checks, named ROM
freshness, card and bus tests, bring-up, serial console, PIT/POST expansion,
EKTA decode modes and video. `REVB_CI_GROUP=cards` or `system` selects its
corresponding subset. The default suite also runs local CAD/release checks;
read every skipped-tool message before interpreting aggregate success.
An exit of zero with a skipped release section does not qualify fabrication.

The Rev B video guard covers chip-level TTL timing and the framebuffer path.
The serial and I/O guards use hardware-rate clock/framing fixtures and negative
controls. These are modeled results, not measurements of assembled hardware.
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
board works.
