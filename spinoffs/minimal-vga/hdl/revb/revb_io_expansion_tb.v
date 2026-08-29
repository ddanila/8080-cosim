// R5.I2 physical-rate twin for D57, POST, sound and the real 8251.
`default_nettype none
`timescale 1ns/1ps
module revb_io_expansion_tb;
    parameter integer CLK_SOURCE = 1;
    parameter BAD_PIT_TAP = 0;
    parameter POST_ALIAS_FAULT = 0;

    reg clk = 0, baud_master = 0, reset_n = 0;
    reg [15:0] A = 0;
    reg [7:0] D_in = 0;
    reg m1_n = 1, iorq_n = 1, rd_n = 1, wr_n = 1;
    wire [7:0] D_out;
    wire D_oe, mode0, mode1, pit0, pit1, pit2, baudclk;
    wire [7:0] post_code;
    wire uart_txd;
    wire uart_rxd = uart_txd;
    integer errors = 0;
    integer cpu_edges = 0, master_edges = 0;
    integer e0, e1, period, polls;
    reg [7:0] value, lo, hi;

    always #250 clk = ~clk;          // 2.000 MHz
    always #101.725 baud_master = ~baud_master; // 4.9152 MHz
    always @(posedge clk) cpu_edges = cpu_edges + 1;
    always @(posedge baud_master) master_edges = master_edges + 1;

    revb_io_card #(.USART_REAL(1), .PIT_REAL(1), .CLK_SOURCE(CLK_SOURCE),
                   .BAD_PIT_TAP(BAD_PIT_TAP), .POST_ALIAS_FAULT(POST_ALIAS_FAULT)) dut (
        .clk(clk), .baud_master(baud_master), .reset_n(reset_n),
        .A(A), .D_in(D_in), .m1_n(m1_n), .iorq_n(iorq_n), .rd_n(rd_n), .wr_n(wr_n),
        .uart_rxd(uart_rxd), .uart_txd(uart_txd), .D_out(D_out), .D_oe(D_oe),
        .MODE0(mode0), .MODE1(mode1), .PIT_OUT0(pit0), .PIT_OUT1(pit1),
        .PIT_OUT2(pit2), .BAUDCLK_OUT(baudclk), .POST_CODE(post_code));

    task idle;
      begin iorq_n = 1; rd_n = 1; wr_n = 1; m1_n = 1; A = 0; D_in = 0; end
    endtask

    task io_write(input [7:0] port, input [7:0] data);
      begin
        @(negedge clk); A = port; D_in = data; m1_n = 1; iorq_n = 0; wr_n = 0;
        @(posedge clk); @(negedge clk); idle; #5;
      end
    endtask

    task io_read(input [7:0] port, output [7:0] data);
      begin
        @(negedge clk); A = port; m1_n = 1; iorq_n = 0; rd_n = 0; #20;
        data = D_oe ? D_out : 8'hff;
        idle; @(negedge clk);
      end
    endtask

    task fail(input [255:0] msg);
      begin errors = errors + 1; $display("  FAIL %0s", msg); end
    endtask

    initial begin
        idle;
        repeat (4) @(posedge clk);
        reset_n = 1;
        repeat (4) @(posedge clk);
        if (post_code !== 8'h00) fail("POST reset clear");

        io_write(8'h20, 8'hA5);
        if (post_code !== 8'hA5) fail("POST write/retain at 20h");
        @(negedge clk); A=8'h20; iorq_n=0; rd_n=0; #20;
        if (D_oe !== 1'b0) fail("POST read must be electrically silent");
        idle;

        // Acknowledge cycle must select neither POST nor PIT.
        @(negedge clk); A=8'h20; D_in=8'h5A; m1_n=0; iorq_n=0; wr_n=0;
        @(posedge clk); @(negedge clk); idle; #20;
        if (post_code !== 8'hA5) fail("M1-low interrupt acknowledge changed POST");

        // D57 channel 0: lobyte/hibyte, mode 3, binary, count 4.
        io_write(8'h1B, 8'h36);
        io_write(8'h18, 8'h04);
        io_write(8'h18, 8'h00);
        @(posedge pit0); e0 = master_edges;
        @(posedge pit0); e1 = master_edges;
        period = e1 - e0;
        if (period < 15 || period > 17) begin
            $display("  PIT0 master period=%0d, expected 16", period);
            fail("D57 channel-0 source/count");
        end

        // Counter latch must return a coherent count in the programmed 1..4 range.
        io_write(8'h1B, 8'h00);
        io_read(8'h18, lo);
        io_read(8'h18, hi);
        if (hi !== 8'h00 || lo < 1 || lo > 4) begin
            $display("  latched count=%02h%02h", hi, lo);
            fail("D57 count latch/read");
        end

        @(posedge baudclk); e0 = master_edges;
        @(posedge baudclk); e1 = master_edges;
        period = e1 - e0;
        if (CLK_SOURCE == 2) begin
            if (period < 31 || period > 33) fail("direct /32 recovery clock");
        end else begin
            if (period < 15 || period > 17) fail("PIT-normal or direct /16 clock");
        end

        // D57 channel 1: mode 3 count 5102. Rising-to-rising is 5102 CPU clocks.
        io_write(8'h1B, 8'h76);
        io_write(8'h19, 8'hEE);
        io_write(8'h19, 8'h13);
        @(posedge pit1); e0 = cpu_edges;
        @(posedge pit1); e1 = cpu_edges;
        period = e1 - e0;
        if (period < 5101 || period > 5103) begin
            $display("  PIT1 CPU period=%0d, expected 5102", period);
            fail("D57 channel-1 sound period");
        end

        // 8251 async x16, 8 data, no parity, one stop; enable Tx/Rx and loop back.
        io_write(8'h09, 8'h4E);
        io_write(8'h09, 8'h37);
        io_write(8'h08, 8'hA6);
        value = 0; polls = 0;
        while (!value[1] && polls < 5000) begin
            io_read(8'h09, value);
            polls = polls + 1;
        end
        if (!value[1]) fail("8251 loopback RxRDY timeout");
        else begin
            io_read(8'h08, value);
            if (value !== 8'hA6) begin
                $display("  USART loopback data=%02h", value);
                fail("8251 loopback byte");
            end
        end

        reset_n = 0; #20;
        if (post_code !== 8'h00) fail("POST reset after activity");

        if (errors == 0) $display("REVB-IO-EXPANSION-TB: PASS source=%0d", CLK_SOURCE);
        else $display("REVB-IO-EXPANSION-TB: FAIL source=%0d errors=%0d", CLK_SOURCE, errors);
        $finish;
    end

    initial begin
        #50_000_000;
        $display("REVB-IO-EXPANSION-TB: FAIL watchdog");
        $finish;
    end
endmodule
`default_nettype wire
