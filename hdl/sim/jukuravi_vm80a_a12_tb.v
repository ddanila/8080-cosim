`timescale 1ns/100ps
`default_nettype none

// Run the physical T32 direct-register probe against the die-derived vm80a
// register unit, clean and with only the bit-12 retain-high term removed.
module jukuravi_vm80a_a12_tb;
  parameter integer FAULT = 0;

  tri1 [7:0] d;
  wire [15:0] a;
  reg clk = 0, f1 = 0, f2 = 0, reset = 1, ready = 1, hold = 0, intr = 0;
  wire inte, hlda, wait_o, sync, dbin, wr_n;
  reg [7:0] mem [0:65535];
  reg checking = 0;
  integer i, failures = 0;
  reg [1023:0] probe_path;

  assign d = dbin ? mem[a] : 8'hzz;
  always @(negedge wr_n) mem[a] = d;

  initial forever begin
    f1 = 1; clk = 0; #10; clk = 1; #10;
    f1 = 0; f2 = 1; clk = 0; #10; clk = 1; #10;
    f2 = 0;
  end

  task expect_word(input [15:0] address, input [15:0] expected); begin
    if ({mem[address + 1], mem[address]} !== expected) begin
      $display("JUKURAVI-VM80A-A12: FAIL address=%04h expected=%04h got=%02h%02h",
               address, expected, mem[address + 1], mem[address]);
      failures = failures + 1;
    end
  end endtask

  initial begin
    for (i = 0; i < 65536; i = i + 1) mem[i] = 8'h00;
    if (!$value$plusargs("probe=%s", probe_path)) begin
      $display("JUKURAVI-VM80A-A12: FAIL missing +probe=path");
      $finish;
    end
    $readmemh(probe_path, mem, 16'h4000, 16'h4050);
    // LXI SP,C000 / CALL 4000 / HLT
    mem[0] = 8'h31; mem[1] = 8'h00; mem[2] = 8'hC0;
    mem[3] = 8'hCD; mem[4] = 8'h00; mem[5] = 8'h40;
    mem[6] = 8'h76;
    #2000 reset = 0;
  end

  always @(posedge clk) if (!reset && cpu.core.thalt && !checking) begin
    checking = 1;
    if (mem[16'h4D04] !== 8'hA5) begin
      $display("JUKURAVI-VM80A-A12: FAIL completion=%02h", mem[16'h4D04]);
      failures = failures + 1;
    end
    expect_word(16'h4D08, 16'h1000);
    expect_word(16'h4D0A, FAULT ? 16'h0A01 : 16'h1A01);
    expect_word(16'h4D0C, FAULT ? 16'h4A01 : 16'h5A01);
    expect_word(16'h4D0E, FAULT ? 16'h8A01 : 16'h9A01);
    expect_word(16'h4D10, 16'h1A01);
    if (!failures)
      $display("JUKURAVI-VM80A-A12: PASS mode=%0s words=1000 %04h %04h %04h 1A01",
               FAULT ? "fault" : "clean",
               FAULT ? 16'h0A01 : 16'h1A01,
               FAULT ? 16'h4A01 : 16'h5A01,
               FAULT ? 16'h8A01 : 16'h9A01);
    #20 $finish;
  end

  initial begin
    #5000000;
    $display("JUKURAVI-VM80A-A12: FAIL timeout");
    $finish;
  end

  vm80a #(.FAULT_A12_INCREMENT_HIGH_LOSS(FAULT)) cpu (
    .pin_clk(clk), .pin_f1(f1), .pin_f2(f2), .pin_d(d), .pin_a(a),
    .pin_reset(reset), .pin_hold(hold), .pin_hlda(hlda), .pin_ready(ready),
    .pin_wait(wait_o), .pin_int(intr), .pin_inte(inte), .pin_sync(sync),
    .pin_dbin(dbin), .pin_wr_n(wr_n)
  );
endmodule

`default_nettype wire
