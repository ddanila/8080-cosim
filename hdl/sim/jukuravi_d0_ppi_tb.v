`timescale 1ns/100ps
`default_nettype none

// Execute the D27/8255 all-port readback test through vm80a and juku_top.
// X2 is intentionally unstimulated, matching the documented disconnected test.
module jukuravi_d0_ppi_tb;
  reg osc = 0;
  reg active = 0;
  reg finishing = 0;
  integer inject_fault = 0;
  integer io_writes = 0;
  integer pic_reads = 0;
  integer ppi_reads = 0;
  integer mem_writes = 0;
  integer failures = 0;
  reg [15:0] ppi_fail_pc = 0;
  reg [7:0] last_ppi_port = 0;
  reg [7:0] last_ppi_write = 0;

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
    $display("JUKURAVI-D0-PPI-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task expect_write(input [7:0] port, input [7:0] value,
                    input [7:0] want_port, input [7:0] want_value,
                    input [1023:0] message); begin
    if (port !== want_port || value !== want_value) fail(message);
  end endtask

  task check_output(input integer index, input [7:0] port, input [7:0] value); begin
    case (index)
      1: expect_write(port,value,8'h1B,8'h76,"alive control");
      2: expect_write(port,value,8'h19,8'hD0,"alive divisor low");
      3: expect_write(port,value,8'h19,8'h07,"alive divisor high");
      4: expect_write(port,value,8'h1B,8'h50,"alive silence control");
      5: expect_write(port,value,8'h19,8'h01,"alive silence count");
      6: expect_write(port,value,8'h00,8'hD6,"PIC ICW1");
      7: expect_write(port,value,8'h01,8'hFE,"PIC ICW2");
      8: expect_write(port,value,8'h01,8'h00,"PIC mask zero");
      9: expect_write(port,value,8'h01,8'hFF,"PIC mask full test");
      10: expect_write(port,value,8'h01,8'hFF,"PIC safe restore");
      11: expect_write(port,value,8'h0F,8'h80,"PPI all-output control");
      12: expect_write(port,value,8'h0C,8'h00,"PPI PA zero");
      13: expect_write(port,value,8'h0C,8'hFF,"PPI PA full");
      14: expect_write(port,value,8'h0D,8'h00,"PPI PB zero");
      15: expect_write(port,value,8'h0D,8'hFF,"PPI PB full");
      16: expect_write(port,value,8'h0E,8'h00,"PPI PC zero");
      17: expect_write(port,value,8'h0E,8'hFF,"PPI PC full");
      18: expect_write(port,value,8'h0F,8'h9B,"PPI all-input recovery");
      19: expect_write(port,value,8'h0C,8'h00,"PPI PA latch clear");
      20: expect_write(port,value,8'h0D,8'h00,"PPI PB latch clear");
      21: expect_write(port,value,8'h0E,8'h00,"PPI PC latch clear");
      22: if (inject_fault)
            expect_write(port,value,8'h1B,8'h76,"PPI-fail control");
          else
            expect_write(port,value,8'h09,8'h00,"post-PPI USART recovery");
      23: if (!inject_fault) fail("unexpected clean output 23");
          else expect_write(port,value,8'h19,8'h6B,"PPI-fail divisor low");
      24: if (!inject_fault) fail("unexpected clean output 24");
          else expect_write(port,value,8'h19,8'h0A,"PPI-fail divisor high");
      default: fail("unexpected extra I/O write");
    endcase
  end endtask

  task check_common; begin
    if (architectural_e !== 8'hD0) fail("CPU signature changed");
    if (mem_writes != 0) fail("RAM write before PPI verdict");
    if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
    if (dut.U_PPI0.pc[1:0] !== 2'b00) fail("memory mode changed");
    if (dut.U_INTR.mask !== 8'hFF) fail("PIC mask is not FF");
    if (dut.U_PPI1.regs[3] !== 8'h9B) fail("D27 terminal control is not 9B");
    if (dut.U_PPI1.regs[0] !== 8'h00 || dut.U_PPI1.regs[1] !== 8'h00
        || dut.U_PPI1.regs[2] !== 8'h00 || dut.U_PPI1.portc !== 8'h00)
      fail("D27 output latches are not clear");
  end endtask

  always @(negedge dut.iowr_n) if (active) begin
    #1;
    io_writes = io_writes + 1;
    check_output(io_writes, dut.BA[7:0], dut.DB);
    if (dut.BA[7:0] >= 8'h0C && dut.BA[7:0] <= 8'h0E) begin
      last_ppi_port = dut.BA[7:0];
      last_ppi_write = dut.DB;
    end
    if (!inject_fault && io_writes == 22 && !finishing) begin
      finishing = 1;
      check_common();
      if (pic_reads != 2 || ppi_reads != 6) fail("clean peripheral read counts");
      if (failures == 0)
        $display("JUKURAVI-D0-PPI-HDL: PASS path=clean pc=%04h signature=%02h io=%0d reads=%0d/%0d control=%02h ram_writes=%0d",
                 pc, architectural_e, io_writes, pic_reads, ppi_reads,
                 dut.U_PPI1.regs[3], mem_writes);
      #20 $finish;
    end
  end

  always @(posedge dut.iowr_n) if (active && inject_fault
      && last_ppi_port == 8'h0E && last_ppi_write == 8'hFF)
    #2 dut.U_PPI1.regs[2] = 8'hFE;

  always @(negedge dut.iord_n) if (active) begin
    #1;
    if (dut.BA[7:0] == 8'h01) begin
      pic_reads = pic_reads + 1;
      if (pic_reads == 1 && dut.DB !== 8'h00) fail("PIC zero readback");
      if (pic_reads == 2 && dut.DB !== 8'hFF) fail("PIC full readback");
    end
    if (dut.BA[7:0] >= 8'h0C && dut.BA[7:0] <= 8'h0E) begin
      ppi_reads = ppi_reads + 1;
      case (ppi_reads)
        1,3,5: if (dut.DB !== 8'h00) fail("PPI zero readback");
        2,4: if (dut.DB !== 8'hFF) fail("PPI full readback");
        6: if (dut.DB !== (inject_fault ? 8'hFE : 8'hFF))
             fail("PPI Port C full readback");
        default: fail("extra PPI read");
      endcase
    end
  end

  always @(negedge dut.memw_n) if (active) mem_writes = mem_writes + 1;

  always @(posedge osc) if (active && inject_fault
      && dut.U_CPU.u.core.thalt && !finishing) begin
    finishing = 1;
    if (pc != ppi_fail_pc + 16'd1) fail("wrong PPI-fail HLT");
    if (io_writes != 24 || pic_reads != 2 || ppi_reads != 6)
      fail("PPI-fail I/O counts");
    check_common();
    if (dut.U_PIT2.mode[1] !== 3'd3 || dut.U_PIT2.reload[1] !== 17'd2667)
      fail("PPI-fail continuous tone");
    if (failures == 0)
      $display("JUKURAVI-D0-PPI-HDL: PASS path=pc-stuck-low pc=%04h signature=%02h io=%0d reads=%0d/%0d control=%02h ram_writes=%0d",
               pc, architectural_e, io_writes, pic_reads, ppi_reads,
               dut.U_PPI1.regs[3], mem_writes);
    #20 $finish;
  end

  initial begin
    if (!$value$plusargs("ppi_fail=%h", ppi_fail_pc))
      fail("missing +ppi_fail PC");
    inject_fault = $test$plusargs("inject_fault");
  end

  initial begin
    #13000000;
    fail("time cap before PPI verdict");
    $finish;
  end
endmodule

`default_nettype wire
