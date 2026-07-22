`timescale 1ns/100ps
`default_nettype none

// Execute the time-compressed Jukuravi D0 CPU-test image through the same
// vm80a-based juku_top that boots the real ROM. Only the alive-beep delay
// immediate is shortened by the fixture; all self-test and failure-code bytes
// are identical to the burn image.
module jukuravi_d0_cpu_tb;
  reg osc = 0;
  reg active = 0;
  integer io_writes = 0;
  integer mem_writes = 0;
  integer expect_fail = 0;
  integer failures = 0;
  reg finishing = 0;
  reg [15:0] success_pc = 16'h0000;
  reg [15:0] failure_pc = 16'h0000;

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
               .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(1'b0));

  wire [15:0] pc = dut.U_CPU.u.core.r16_pc;
  wire [7:0] architectural_e = dut.U_CPU.u.core.xchg_dh
      ? dut.U_CPU.u.core.r16_de[7:0] : dut.U_CPU.u.core.r16_hl[7:0];

  initial begin
    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    #2000;
    force dut.reset_sys = 1'b0;
    active = 1;
  end

  initial forever begin
    force dut.phi1 = 1'b1; force dut.phi2 = 1'b0; osc = 0; #10; osc = 1; #10;
    force dut.phi1 = 1'b0; force dut.phi2 = 1'b1; osc = 0; #10; osc = 1; #10;
    force dut.phi2 = 1'b0;
  end

  task fail(input [1023:0] message); begin
    $display("JUKURAVI-D0-CPU-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task check_io(input integer index, input [7:0] port, input [7:0] value); begin
    case (index)
      1: if (port !== 8'h1B || value !== 8'h76) fail("alive control write");
      2: if (port !== 8'h19 || value !== 8'hD0) fail("alive divisor low");
      3: if (port !== 8'h19 || value !== 8'h07) fail("alive divisor high");
      4: if (port !== 8'h1B || value !== 8'h50) fail("silence control write");
      5: if (port !== 8'h19 || value !== 8'h01) fail("silence count write");
      6: if (!expect_fail || port !== 8'h1B || value !== 8'h76) fail("CPU-bad control write");
      7: if (!expect_fail || port !== 8'h19 || value !== 8'h40) fail("CPU-bad divisor low");
      8: if (!expect_fail || port !== 8'h19 || value !== 8'h1F) fail("CPU-bad divisor high");
      default: fail("unexpected extra I/O write");
    endcase
  end endtask

  always @(negedge dut.iowr_n) if (active) begin
    #1;
    io_writes = io_writes + 1;
    check_io(io_writes, dut.BA[7:0], dut.DB);
  end

  always @(negedge dut.memw_n) if (active) mem_writes = mem_writes + 1;

  always @(posedge osc) if (active) begin
    // A conditional jump may expose its fall-through PC before the taken
    // branch retires. Judge the terminal path only once HLT has entered the
    // core's halt wait state, after all preceding I/O cycles have completed.
    if (dut.U_CPU.u.core.thalt && !finishing) begin
      finishing = 1;
      if (pc != (expect_fail ? failure_pc : success_pc) + 16'd1)
        fail("wrong terminal HLT");
      if (io_writes != (expect_fail ? 8 : 5)) fail("I/O write count");
      if (mem_writes != 0) fail("RAM write before RAM test");
      if (architectural_e !== 8'hD0) fail("rolling signature is not D0");
      if (dut.U_CPU.u.core.acc !== (expect_fail ? 8'h1F : 8'hD0))
        fail("terminal accumulator value");
      if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
      if (failures == 0)
        $display("JUKURAVI-D0-CPU-HDL: PASS path=%0s pc=%04h signature=%02h io=%0d ram_writes=%0d",
                 expect_fail ? "cpu-bad" : "success", pc, architectural_e,
                 io_writes, mem_writes);
      #20 $finish;
    end
  end

  initial begin
    if (!$value$plusargs("success=%h", success_pc)) fail("missing +success PC");
    if (!$value$plusargs("failure=%h", failure_pc)) fail("missing +failure PC");
    expect_fail = $test$plusargs("expect_fail");
  end

  initial begin
    #5000000;
    fail("time cap before terminal PC");
    $finish;
  end
endmodule

`default_nettype wire
