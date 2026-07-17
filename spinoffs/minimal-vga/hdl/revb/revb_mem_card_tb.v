// Unit TB: Memory card. ROM read (Mode A decode), RAM write/readback, RAM default,
// ROM read-only. +injectfail proves the harness detects a bad expectation.
`default_nettype none
`timescale 1ns/100ps
module revb_mem_card_tb;
    parameter rom_file = "memtest.hex";
    reg clk = 0; reg [15:0] bA; reg [7:0] bD;
    reg bMREQ_n = 1, bIORQ_n = 1, bRD_n = 1, bWR_n = 1;
    reg reset_n = 0, bmode0 = 0, bmode1 = 0;
    wire [7:0] cD; wire cOE;
    wire [7:0] bDout = cOE ? cD : 8'hFF;
    integer errors = 0;
    always #5 clk = ~clk;

    revb_mem_card #(.rom_file(rom_file), .DECODE_MODE(1)) dut (
        .clk(clk), .reset_n(reset_n), .A(bA), .D_in(bD),
        .mreq_n(bMREQ_n), .rd_n(bRD_n), .wr_n(bWR_n),
        .MODE0(bmode0), .MODE1(bmode1), .D_out(cD), .D_oe(cOE));

    `include "revb_bus_bfm.vh"

    initial begin
        bus_idle; #20 reset_n = 1; #20;
        chk_mem_rd(16'h0000, 8'h3C, "rom0");        // Mode A: ROM in low 16K
        chk_mem_rd(16'h0001, 8'h4D, "rom1");
        mem_wr(16'h4000, 8'hA5);
        chk_mem_rd(16'h4000, 8'hA5, "ram_wr");      // RAM write/readback
        chk_mem_rd(16'h5000, 8'h00, "ram_default"); // untouched RAM reads 0
        mem_wr(16'h0000, 8'hFF);
        chk_mem_rd(16'h0000, 8'h3C, "rom_ro");      // ROM ignores writes
        if ($test$plusargs("injectfail"))
            chk_mem_rd(16'h4000, 8'h00, "INJECTED"); // wrong on purpose (real = 0xA5)
        if (errors == 0) $display("REVB-MEM-CARD-TB: PASS");
        else             $display("REVB-MEM-CARD-TB: FAIL (%0d error(s))", errors);
        $finish;
    end
endmodule
`default_nettype wire
