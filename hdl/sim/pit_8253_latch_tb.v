`timescale 1ns/100ps
`default_nettype none

// Prove the 8253's software-visible load/latch/read contract independently of
// the Juku-specific clock cascade. GATE inputs are controlled explicitly so
// exact byte-order checks do not depend on timer phase.
module pit_8253_latch_tb;
  reg [1:0] A = 0;
  tri [7:0] D;
  reg [7:0] drive_d = 0;
  reg drive = 0, cs_n = 1, rd_n = 1, wr_n = 1;
  reg clk0 = 0, clk1 = 0, clk2 = 0;
  reg gate0 = 0, gate1 = 0, gate2 = 0;
  wire out0, out1, out2;
  integer failures = 0;
  reg [7:0] value;
  reg [15:0] first_latch;

  assign D = drive ? drive_d : 8'bz;

  pit_8253 UUT(.A(A), .D(D), .cs_n(cs_n), .rd_n(rd_n), .wr_n(wr_n),
               .clk(1'b0), .clk0(clk0), .gate0(gate0),
               .clk1(clk1), .gate1(gate1), .clk2(clk2), .gate2(gate2),
               .out0(out0), .out1(out1), .out2(out2));

  always #5 clk0 = ~clk0;
  always #7 clk1 = ~clk1;
  always #9 clk2 = ~clk2;

  task fail(input [1023:0] message); begin
    $display("PIT8253-LATCH: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task write_reg(input [1:0] addr, input [7:0] data); begin
    A = addr; drive_d = data; drive = 1; cs_n = 0; wr_n = 0;
    #3; wr_n = 1; #1; cs_n = 1; drive = 0; #2;
  end endtask

  task read_reg(input [1:0] addr, output [7:0] data); begin
    A = addr; drive = 0; cs_n = 0; rd_n = 0;
    #2; data = D; #1; rd_n = 1; #1; cs_n = 1; #2;
  end endtask

  initial begin
    // Channel 0, LSB then MSB, binary mode 0. GATE0 low freezes 1234h.
    write_reg(2'd3, 8'h30);
    write_reg(2'd0, 8'h34);
    write_reg(2'd0, 8'h12);
    write_reg(2'd3, 8'h00);
    read_reg(2'd0, value);
    if (value !== 8'h34) fail("channel-0 latched LSB order");
    read_reg(2'd0, value);
    if (value !== 8'h12) fail("channel-0 latched MSB order");
    if (UUT.latch_valid[0] !== 1'b0 || UUT.read_phase[0] !== 0)
      fail("two-byte read did not release output latch");

    // LSB-only and MSB-only formats release after one read.
    write_reg(2'd3, 8'h50);
    write_reg(2'd1, 8'hA5);
    write_reg(2'd3, 8'h40);
    read_reg(2'd1, value);
    if (value !== 8'hA5 || UUT.latch_valid[1] !== 1'b0)
      fail("channel-1 LSB-only latch/read");

    write_reg(2'd3, 8'hA0);
    write_reg(2'd2, 8'h5A);
    write_reg(2'd3, 8'h80);
    read_reg(2'd2, value);
    if (value !== 8'h5A || UUT.latch_valid[2] !== 1'b0)
      fail("channel-2 MSB-only latch/read");

    // A pending latch must ignore a second latch command while live counting
    // proceeds. Capture the first value, run well past it, and consume it.
    gate0 = 1;
    write_reg(2'd3, 8'h34);  // channel 0, LSB/MSB, mode 2
    write_reg(2'd0, 8'h08);
    write_reg(2'd0, 8'h00);
    #12;
    write_reg(2'd3, 8'h00);
    first_latch = UUT.output_latch[0];
    #80;
    write_reg(2'd3, 8'h00);
    if (UUT.output_latch[0] !== first_latch)
      fail("second command replaced a pending latch");
    read_reg(2'd0, value);
    if (value !== first_latch[7:0]) fail("pending latch LSB changed");
    read_reg(2'd0, value);
    if (value !== first_latch[15:8]) fail("pending latch MSB changed");

    // BCD counts are normalized internally but must read back as packed BCD.
    gate0 = 0;
    write_reg(2'd3, 8'h31);
    write_reg(2'd0, 8'h34);
    write_reg(2'd0, 8'h12);
    write_reg(2'd3, 8'h00);
    read_reg(2'd0, value);
    if (value !== 8'h34) fail("BCD LSB encoding");
    read_reg(2'd0, value);
    if (value !== 8'h12) fail("BCD MSB encoding");

    if (failures == 0)
      $display("PIT8253-LATCH: PASS two-byte/single-byte/BCD/pending-latch semantics");
    $finish;
  end
endmodule

`default_nettype wire
