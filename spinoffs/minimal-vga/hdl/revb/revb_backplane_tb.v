// Clock/reset the rev B modular backplane twin until the Video card dumps its
// framebuffer and $finish. Mirrors vjuga_juku_tb.v.
`default_nettype none
`timescale 1ns/100ps
module revb_backplane_tb;
    parameter rom_file    = "ekta37_z80.hex";
    parameter vw_limit    = 6000;
    parameter dump_file   = "revb_vram.bin";
    parameter decode_mode = 0;   // 0 = Mode B (D6 РТ4), 1 = Mode A (GAL-internal)
    reg clk = 0, reset_n = 0;
    always #10 clk = ~clk;

    revb_backplane_top #(.rom_file(rom_file), .vw_limit(vw_limit),
                         .dump_file(dump_file), .DECODE_MODE(decode_mode))
        dut (.clk(clk), .reset_n(reset_n));

    initial begin
        #100 reset_n = 1;
        #400_000_000;   // watchdog
        $display("REVB-V: WATCHDOG - target not reached");
        $finish;
    end
endmodule
`default_nettype wire
