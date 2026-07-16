`timescale 1ns/1ps
`default_nettype none

module d2_ready_path_tb;
  reg [7:0] address = 8'h00;
  reg enable1_n = 1'b0;
  reg enable2_n = 1'b0;
  reg phi2ttl = 1'b0;
  tri1 [3:0] d2_data;
  wire ready_d = d2_data[0];
  wire ready;
  wire ready_n;
  integer failures = 0;

  wait_prom_037 U_D2(.a(address), .v1_n(enable1_n), .v2_n(enable2_n), .d(d2_data));
  tm2_dff #(.FUNCTIONAL(1)) U_D30(
      .clr1_n(1'b1), .d1(ready_d), .clk1(phi2ttl), .pre1_n(1'b1),
      .q1(ready), .q1_n(ready_n),
      .clr2_n(1'b1), .d2(1'b1), .clk2(1'b0), .pre2_n(1'b1),
      .q2(), .q2_n());

  task fail(input [1023:0] message); begin
    $display("D2-READY-PATH: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task latch_row(input [7:0] row, input expected_level); begin
    address = row;
    #1;
    if (ready_d !== expected_level) fail("raw D0 level does not match expected open-collector state");
    phi2ttl = 1'b1;
    #1;
    if (ready !== expected_level) fail("D30 did not latch D2 READY_D on PHI2TTL");
    phi2ttl = 1'b0;
    #1;
  end endtask

  initial begin
    // Row 00 is physical raw 0: D0 sinks READY_D and D30 latches WAIT/READY low.
    latch_row(8'h00, 1'b0);

    // Row 80 is physical raw F: D0 releases and the modeled R6 pull-up wins.
    latch_row(8'h80, 1'b1);

    // Either active-low enable high must also release every output.
    address = 8'h00;
    enable1_n = 1'b1;
    #1;
    if (d2_data !== 4'hf) fail("disabled D2 outputs did not release to pull-ups");
    phi2ttl = 1'b1;
    #1;
    if (ready !== 1'b1) fail("D30 did not latch released READY_D high");
    phi2ttl = 1'b0;
    enable1_n = 1'b0;
    enable2_n = 1'b1;
    #1;
    if (d2_data !== 4'hf) fail("second disabled D2 enable did not release to pull-ups");

    if (failures == 0) begin
      $display("D2-READY-PATH: PASS raw 00->READY 0, raw F/disabled->READY 1");
      $finish;
    end
    $display("D2-READY-PATH: FAIL count=%0d", failures);
    $finish(1);
  end
endmodule

`default_nettype wire
