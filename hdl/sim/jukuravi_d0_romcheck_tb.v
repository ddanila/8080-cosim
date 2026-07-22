`timescale 1ns/100ps
`default_nettype none

// Execute the historical block-1 checksum through vm80a and the physical
// D15 ROM path. The generated fixture shortens only the alive delay; its
// stored 000Ah sum is regenerated before the corrupt case flips byte 07FFh.
module jukuravi_d0_romcheck_tb;
  reg osc = 0;
  reg active = 0;
  reg finishing = 0;
  integer expect_fail = 0;
  integer io_writes = 0;
  integer mem_writes = 0;
  integer failures = 0;
  reg [15:0] rom_fail_pc = 0;

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
    $display("JUKURAVI-D0-ROMCHECK-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task check_io(input integer index, input [7:0] port, input [7:0] value); begin
    case (index)
      1: if (port !== 8'h1B || value !== 8'h76) fail("alive control write");
      2: if (port !== 8'h19 || value !== 8'hD0) fail("alive divisor low");
      3: if (port !== 8'h19 || value !== 8'h07) fail("alive divisor high");
      4: if (port !== 8'h1B || value !== 8'h50) fail("silence control write");
      5: if (port !== 8'h19 || value !== 8'h01) fail("silence count write");
      6: if (expect_fail) begin
           if (port !== 8'h1B || value !== 8'h76) fail("ROM-fail control write");
         end else if (port !== 8'h09 || value !== 8'h00) begin
           fail("first post-ROM-check USART recovery write");
         end
      7: if (!expect_fail || port !== 8'h19 || value !== 8'hE8)
           fail("ROM-fail divisor low");
      8: if (!expect_fail || port !== 8'h19 || value !== 8'h03)
           fail("ROM-fail divisor high");
      default: fail("unexpected extra I/O write");
    endcase
  end endtask

  always @(negedge dut.iowr_n) if (active) begin
    #1;
    io_writes = io_writes + 1;
    check_io(io_writes, dut.BA[7:0], dut.DB);
    if (!expect_fail && io_writes == 6 && !finishing) begin
      finishing = 1;
      if (architectural_e !== 8'hD0) fail("CPU signature changed");
      if (mem_writes != 0) fail("RAM write before USART stage");
      if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
      if (dut.U_PPI0.pc[1:0] !== 2'b00) fail("memory mode changed");
      if (failures == 0)
        $display("JUKURAVI-D0-ROMCHECK-HDL: PASS path=clean pc=%04h signature=%02h io=%0d ram_writes=%0d",
                 pc, architectural_e, io_writes, mem_writes);
      #20 $finish;
    end
  end

  always @(negedge dut.memw_n) if (active) mem_writes = mem_writes + 1;

  always @(posedge osc) if (active && expect_fail
      && dut.U_CPU.u.core.thalt && !finishing) begin
    finishing = 1;
    if (pc != rom_fail_pc + 16'd1) fail("wrong ROM-fail HLT");
    if (io_writes != 8) fail("ROM-fail I/O write count");
    if (architectural_e !== 8'hD0) fail("CPU signature changed");
    if (mem_writes != 0) fail("RAM write on ROM-fail path");
    if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
    if (dut.U_PPI0.pc[1:0] !== 2'b00) fail("memory mode changed");
    if (dut.U_PIT2.mode[1] !== 3'd3 || dut.U_PIT2.reload[1] !== 17'd1000)
      fail("ROM-fail continuous tone");
    if (failures == 0)
      $display("JUKURAVI-D0-ROMCHECK-HDL: PASS path=corrupt pc=%04h signature=%02h io=%0d ram_writes=%0d",
               pc, architectural_e, io_writes, mem_writes);
    #20 $finish;
  end

  initial begin
    if (!$value$plusargs("rom_fail=%h", rom_fail_pc))
      fail("missing +rom_fail PC");
    expect_fail = $test$plusargs("expect_fail");
  end

  initial begin
    #10000000;
    fail("time cap before ROM verdict");
    $finish;
  end
endmodule

`default_nettype wire
