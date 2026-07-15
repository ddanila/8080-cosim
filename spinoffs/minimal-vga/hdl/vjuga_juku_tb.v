// Clock/reset the VJUGA Verilog twin until it dumps its framebuffer and $finish.
`default_nettype none
`timescale 1ns/100ps
module vjuga_juku_tb;
    parameter rom_file    = "ekta37_z80.hex";
    parameter vw_limit    = 6000;
    parameter dump_file   = "vjuga_v_vram.bin";
    parameter decode_mode = 0;   // 0 = Mode B (РТ4), 1 = Mode A (GAL-internal)
    reg clk = 0, reset_n = 0;
    always #10 clk = ~clk;

    vjuga_juku_top #(.rom_file(rom_file), .vw_limit(vw_limit),
                     .dump_file(dump_file), .DECODE_MODE(decode_mode))
        dut (.clk(clk), .reset_n(reset_n));

    initial begin
        #100 reset_n = 1;
        #400_000_000;   // watchdog
        $display("VJUGA-V: WATCHDOG - target not reached");
        $finish;
    end
endmodule
`default_nettype wire
