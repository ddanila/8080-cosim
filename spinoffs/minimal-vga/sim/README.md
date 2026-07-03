# Simulation

`check.sh` is the spin-off entry point.

For now it runs:

- `../../../sync/boot_check.sh`, which compares the existing HDL boot paths
  against the C cosim oracle using the real Juku ROM.
- `../../../hdl/sim/dram_unit_tb.v`, which tests the 64K x 1 row/column DRAM
  model.

Once `../hdl/` contains a minimal top, add a third check here:

1. Compile the minimal top.
2. Boot `../../../roms/ekta37.bin`.
3. Compare its framebuffer/VRAM output to the existing cosim reference.
4. Then add VGA-side assertions for `hsync`, `vsync`, blanking, and visible
   prompt/banner output.

T80 is VHDL, so the next simulator dependency is `ghdl` or an equivalent VHDL
tool. The existing project Verilog checks still require `iverilog`/`vvp`.
