# juku_top checkpoint load

Status: **PASS**

This diagnostic regenerates the 30,000-write EKDOS/TDD cosim checkpoint,
loads its 64 KiB RAM image into the `juku_top` D84..D91
bit-sliced DRAM planes, and seeds CPU/PPI/PIC/FDC latches from fixed
testbench values. It dumps RAM and framebuffer bytes back out and
compares hashes; selected latches are checked against those constants.

The runner does not parse the generated `.state` file or compare latch
values against a fresh cosim state capture. This is a RAM transfer and
latch-injection check; CPU execution is tested by the separate resume probe.

## Command

Run with Python 3, `sha256sum`, a C compiler (`CC`, default `cc`),
and Icarus Verilog (`iverilog` and `vvp`). The runner overwrites this
report and uses a temporary directory for builds and checkpoint files.
It restores `cosim/vram.bin`
after checkpoint capture completes normally.

```sh
sync/juku_top_checkpoint_load_check.py
```

Connectivity is checked by the separate [LVS guard](../sync/README.md).
This runner does not invoke it.

## Evidence

- Cosim trace exit code: `0`
- HDL loader exit code: `0`
- HDL RAM pass line: `yes`
- HDL state pass line: `yes`
- Cosim RAM SHA256: `eaa42964cdbc37bce58081edc085c5bcf94e95deed6454230e1aab8f1c3a38d4`
- HDL RAM SHA256: `eaa42964cdbc37bce58081edc085c5bcf94e95deed6454230e1aab8f1c3a38d4`
- Cosim VRAM SHA256: `0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68`
- HDL VRAM SHA256: `0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68`

## Boundary

- CPU execution from this checkpoint is covered separately by
  [resume probe](juku-top-checkpoint-resume.md), which seeds a clean M1 fetch
  boundary and reaches the first post-checkpoint PIC/keyboard events.
- Peripheral state coverage is limited to the visible latches needed at
  the 30,000-write pre-PIC boundary.
- This loader remains a regression-narrowing diagnostic. Uninterrupted
  reset-to-EKDOS evidence is the stronger user-visible milestone.
