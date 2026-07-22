`timescale 1ns/100ps
`default_nettype none

// Execute the D10/8259 IMR self-test through vm80a and juku_top. The fixture
// shortens only the alive delay and regenerates the historical block sum.
module jukuravi_d0_pic_tb;
  reg osc = 0;
  reg active = 0;
  reg finishing = 0;
  integer inject_fault = 0;
  integer io_writes = 0;
  integer pic_reads = 0;
  integer mem_writes = 0;
  integer failures = 0;
  reg [15:0] pic_fail_pc = 0;
  reg [7:0] last_pic_write = 0;

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
    $display("JUKURAVI-D0-PIC-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task check_output(input integer index, input [7:0] port, input [7:0] value); begin
    case (index)
      1: if (port !== 8'h1B || value !== 8'h76) fail("alive control write");
      2: if (port !== 8'h19 || value !== 8'hD0) fail("alive divisor low");
      3: if (port !== 8'h19 || value !== 8'h07) fail("alive divisor high");
      4: if (port !== 8'h1B || value !== 8'h50) fail("silence control write");
      5: if (port !== 8'h19 || value !== 8'h01) fail("silence count write");
      6: if (port !== 8'h00 || value !== 8'hD6) fail("PIC ICW1 write");
      7: if (port !== 8'h01 || value !== 8'hFE) fail("PIC ICW2 write");
      8: if (port !== 8'h01 || value !== 8'h00) fail("PIC zero-mask write");
      9: if (port !== 8'h01 || value !== 8'hFF) fail("PIC full-mask test write");
      10: if (port !== 8'h01 || value !== 8'hFF) fail("PIC safe-mask restore");
      11: if (inject_fault) begin
            if (port !== 8'h1B || value !== 8'h76) fail("PIC-fail control write");
          end else if (port !== 8'h09 || value !== 8'h00) begin
            fail("first post-PIC USART recovery write");
          end
      12: if (!inject_fault || port !== 8'h19 || value !== 8'hF4)
            fail("PIC-fail divisor low");
      13: if (!inject_fault || port !== 8'h19 || value !== 8'h01)
            fail("PIC-fail divisor high");
      default: fail("unexpected extra I/O write");
    endcase
  end endtask

  task check_common; begin
    if (architectural_e !== 8'hD0) fail("CPU signature changed");
    if (mem_writes != 0) fail("RAM write before PIC verdict");
    if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
    if (dut.U_PPI0.pc[1:0] !== 2'b00) fail("memory mode changed");
    if (dut.U_INTR.icw1 !== 8'hD6 || dut.U_INTR.icw2 !== 8'hFE
        || dut.U_INTR.expect_icw2 !== 1'b0)
      fail("PIC initialization state");
    if (dut.U_INTR.mask !== 8'hFF) fail("terminal PIC mask is not FF");
  end endtask

  always @(negedge dut.iowr_n) if (active) begin
    #1;
    io_writes = io_writes + 1;
    check_output(io_writes, dut.BA[7:0], dut.DB);
    if (dut.BA[7:0] == 8'h01) last_pic_write = dut.DB;
    if (!inject_fault && io_writes == 11 && !finishing) begin
      finishing = 1;
      check_common();
      if (pic_reads != 2) fail("PIC read count");
      if (dut.U_PIC.regs[1] !== 8'hFF) fail("PIC readback latch not restored");
      if (failures == 0)
        $display("JUKURAVI-D0-PIC-HDL: PASS path=clean pc=%04h signature=%02h io=%0d pic_reads=%0d mask=%02h ram_writes=%0d",
                 pc, architectural_e, io_writes, pic_reads, dut.U_INTR.mask,
                 mem_writes);
      #20 $finish;
    end
  end

  always @(posedge dut.iowr_n) if (active && inject_fault
      && last_pic_write == 8'hFF)
    #2 dut.U_PIC.regs[1] = 8'hFE;

  always @(negedge dut.iord_n) if (active && dut.BA[7:0] == 8'h01) begin
    #1;
    pic_reads = pic_reads + 1;
    if (pic_reads == 1 && dut.DB !== 8'h00) fail("PIC zero-mask readback");
    if (pic_reads == 2 && dut.DB !== (inject_fault ? 8'hFE : 8'hFF))
      fail("PIC full-mask readback");
    if (pic_reads > 2) fail("extra PIC read");
  end

  always @(negedge dut.memw_n) if (active) mem_writes = mem_writes + 1;

  always @(posedge osc) if (active && inject_fault
      && dut.U_CPU.u.core.thalt && !finishing) begin
    finishing = 1;
    if (pc != pic_fail_pc + 16'd1) fail("wrong PIC-fail HLT");
    if (io_writes != 13 || pic_reads != 2) fail("PIC-fail I/O counts");
    check_common();
    if (dut.U_PIT2.mode[1] !== 3'd3 || dut.U_PIT2.reload[1] !== 17'd500)
      fail("PIC-fail continuous tone");
    if (failures == 0)
      $display("JUKURAVI-D0-PIC-HDL: PASS path=stuck-low pc=%04h signature=%02h io=%0d pic_reads=%0d mask=%02h ram_writes=%0d",
               pc, architectural_e, io_writes, pic_reads, dut.U_INTR.mask,
               mem_writes);
    #20 $finish;
  end

  initial begin
    if (!$value$plusargs("pic_fail=%h", pic_fail_pc))
      fail("missing +pic_fail PC");
    inject_fault = $test$plusargs("inject_fault");
  end

  initial begin
    #12000000;
    fail("time cap before PIC verdict");
    $finish;
  end
endmodule

`default_nettype wire
