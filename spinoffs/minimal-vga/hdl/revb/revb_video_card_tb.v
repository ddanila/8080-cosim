// Unit TB: Video card. Framebuffer write/readback, video-write count, and window
// ownership (must not drive the bus below 0xD800).
`default_nettype none
`timescale 1ns/100ps
module revb_video_card_tb;
    reg clk = 0; reg [15:0] bA; reg [7:0] bD;
    reg bMREQ_n = 1, bIORQ_n = 1, bRD_n = 1, bWR_n = 1;
    reg reset_n = 0, bmode0 = 0, bmode1 = 0;
    wire [7:0] cD; wire cOE;
    wire [7:0] bDout = cOE ? cD : 8'hFF;
    integer errors = 0;
    always #5 clk = ~clk;

    revb_video_card #(.vw_limit(0)) dut (   // vw_limit 0 = no auto-dump/$finish
        .clk(clk), .reset_n(reset_n), .A(bA), .D_in(bD),
        .mreq_n(bMREQ_n), .rd_n(bRD_n), .wr_n(bWR_n),
        .MODE0(bmode0), .MODE1(bmode1), .D_out(cD), .D_oe(cOE));

    `include "revb_bus_bfm.vh"

    initial begin
        bus_idle; #20 reset_n = 1; #20;
        mem_wr(16'hD800, 8'h11); mem_wr(16'hD801, 8'h22); mem_wr(16'hDFFF, 8'h33);
        chk_mem_rd(16'hD800, 8'h11, "fb0");
        chk_mem_rd(16'hD801, 8'h22, "fb1");
        chk_mem_rd(16'hDFFF, 8'h33, "fbN");
        if (dut.vw !== 3) begin
            errors = errors + 1; $display("  FAIL vw=%0d (exp 3)", dut.vw);
        end
        // Ownership: video card must be silent below the framebuffer window.
        @(negedge clk); bA = 16'h4000; bMREQ_n = 0; bRD_n = 0; #2;
        if (cOE !== 1'b0) begin errors = errors + 1; $display("  FAIL video drove 0x4000"); end
        bus_idle;
        if (errors == 0) $display("REVB-VIDEO-CARD-TB: PASS");
        else             $display("REVB-VIDEO-CARD-TB: FAIL (%0d error(s))", errors);
        $finish;
    end
endmodule
`default_nettype wire
