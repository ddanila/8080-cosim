// Unit TB (smoke): CPU card. Feed a NOP stream and confirm the Z80 comes out of
// reset fetching from 0x0000 and keeps fetching.
`default_nettype none
`timescale 1ns/100ps
module revb_cpu_card_tb;
    reg clk = 0, reset_n = 0;
    reg [7:0] D_in = 8'h00;                 // NOP stream
    wire [15:0] A;
    wire m1_n, mreq_n, iorq_n, rd_n, wr_n, rfsh_n, halt_n, busak_n;
    wire [7:0] cpu_do; wire cpu_oe;
    integer errors = 0, fetches = 0;
    reg first = 1; reg [15:0] first_a = 16'hFFFF;
    always #5 clk = ~clk;

    revb_cpu_card dut (
        .clk(clk), .reset_n(reset_n), .wait_n(1'b1),
        .int_n(1'b1), .nmi_n(1'b1), .busrq_n(1'b1),
        .D_in(D_in), .D_out(cpu_do), .D_oe(cpu_oe), .A(A),
        .m1_n(m1_n), .mreq_n(mreq_n), .iorq_n(iorq_n),
        .rd_n(rd_n), .wr_n(wr_n), .rfsh_n(rfsh_n), .halt_n(halt_n), .busak_n(busak_n));

    always @(posedge clk) if (reset_n && !m1_n && !mreq_n && !rd_n) begin
        fetches = fetches + 1;
        if (first) begin first = 0; first_a = A; end
    end

    initial begin
        #20 reset_n = 1; #4000;
        if (first_a !== 16'h0000) begin errors = errors + 1; $display("  FAIL first fetch @%04h (exp 0000)", first_a); end
        if (fetches < 3) begin errors = errors + 1; $display("  FAIL only %0d fetches", fetches); end
        if (errors == 0) $display("REVB-CPU-CARD-TB: PASS (%0d fetches, first@%04h)", fetches, first_a);
        else             $display("REVB-CPU-CARD-TB: FAIL (%0d error(s))", errors);
        $finish;
    end
endmodule
`default_nettype wire
