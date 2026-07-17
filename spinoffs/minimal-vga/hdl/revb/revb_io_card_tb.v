// Unit TB: I/O card. Reset mode, output-latch readback, Port-C mode bits →
// MODE0/1, control-word clear.
`default_nettype none
`timescale 1ns/100ps
module revb_io_card_tb;
    reg clk = 0; reg [15:0] bA; reg [7:0] bD;
    reg bMREQ_n = 1, bIORQ_n = 1, bRD_n = 1, bWR_n = 1;
    reg reset_n = 0;
    wire [7:0] cD; wire cOE, cMODE0, cMODE1;
    wire [7:0] bDout = cOE ? cD : 8'hFF;
    integer errors = 0;
    always #5 clk = ~clk;

    revb_io_card dut (
        .clk(clk), .reset_n(reset_n), .A(bA), .D_in(bD),
        .iorq_n(bIORQ_n), .rd_n(bRD_n), .wr_n(bWR_n),
        .D_out(cD), .D_oe(cOE), .MODE0(cMODE0), .MODE1(cMODE1));

    `include "revb_bus_bfm.vh"

    task chk_mode(input m0, input m1, input [127:0] msg);
        begin #2; if (cMODE0 !== m0 || cMODE1 !== m1) begin
            errors = errors + 1;
            $display("  FAIL %0s: MODE0=%b MODE1=%b (exp %b/%b)", msg, cMODE0, cMODE1, m0, m1);
        end end
    endtask

    initial begin
        bus_idle; #20 reset_n = 1; #20;
        chk_mode(1'b0, 1'b0, "reset");
        io_wr(16'h0004, 8'h5A); chk_io_rd(16'h0004, 8'h5A, "portA_latch");
        io_wr(16'h0006, 8'h02); chk_mode(1'b0, 1'b1, "portC=2");   // mode 2
        io_wr(16'h0006, 8'h01); chk_mode(1'b1, 1'b0, "portC=1");   // mode 1
        io_wr(16'h0007, 8'h80); chk_mode(1'b0, 1'b0, "ctrl_clear");
        if (errors == 0) $display("REVB-IO-CARD-TB: PASS");
        else             $display("REVB-IO-CARD-TB: FAIL (%0d error(s))", errors);
        $finish;
    end
endmodule
`default_nettype wire
