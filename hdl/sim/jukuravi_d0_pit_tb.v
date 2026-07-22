`timescale 1ns/100ps
`default_nettype none

// Execute the version-7 extension guard and phase-tolerant PIT register test
// through vm80a and all three physical juku_top PIT instances.
module jukuravi_d0_pit_tb;
  reg osc = 0;
  reg active = 0;
  reg finishing = 0;
  integer inject_fault = 0;
  integer extension_fault = 0;
  integer io_writes = 0;
  integer pic_reads = 0;
  integer ppi_reads = 0;
  integer pit_writes = 0;
  integer pit_reads = 0;
  integer d55_ch0_reads = 0;
  integer mem_writes = 0;
  integer failures = 0;
  integer expected_write_index;
  integer index;
  integer chip;
  integer channel;
  reg pit_started = 0;
  reg pit_recovery_done = 0;
  reg [15:0] pit_fail_pc = 0;
  reg [15:0] rom_fail_pc = 0;
  reg [7:0] last_port = 0;
  reg [7:0] last_value = 0;
  reg [7:0] expected_write_port [1:40];
  reg [7:0] expected_write_value [1:40];
  reg [7:0] expected_read_port [1:12];
  reg expected_read_sign [1:12];

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

  initial forever begin
    force dut.xtal16m_w = 1'b0; #2;
    force dut.xtal16m_w = 1'b1; #2;
  end

  task fail(input [1023:0] message); begin
    $display("JUKURAVI-D0-PIT-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task check_common; begin
    if (architectural_e !== 8'hD0) fail("CPU signature changed");
    if (mem_writes != 0) fail("RAM write before PIT verdict");
    if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
    if (dut.U_PPI0.pc[1:0] !== 2'b00) fail("memory mode changed");
    if (dut.U_INTR.mask !== 8'hFF) fail("PIC mask is not FF");
    if (dut.U_PPI1.regs[3] !== 8'h9B) fail("D27 terminal control is not 9B");
    if (dut.U_PPI1.regs[0] !== 0 || dut.U_PPI1.regs[1] !== 0
        || dut.U_PPI1.regs[2] !== 0) fail("D27 output latches are not clear");
  end endtask

  task finish_clean; begin
    finishing = 1;
    check_common();
    if (io_writes != 62 || pic_reads != 2 || ppi_reads != 6
        || pit_writes != 40 || pit_reads != 12)
      fail("clean I/O counts");
    if (dut.U_PIT2.mode[1] !== 3'd0 || dut.U_PIT2.reload[1] !== 17'd1
        || dut.U_PIT2.mode[2] !== 3'd0 || dut.U_PIT2.reload[2] !== 17'd1)
      fail("clean D57 recovery");
    if (failures == 0)
      $display("JUKURAVI-D0-PIT-HDL: PASS path=clean pc=%04h io=%0d reads=%0d extension=guarded d57=%0d/%0d",
               pc, io_writes, pit_reads, dut.U_PIT2.reload[1], dut.U_PIT2.reload[2]);
    #20 $finish;
  end endtask

  always @(negedge dut.iowr_n) if (active) begin
    #1;
    io_writes = io_writes + 1;
    last_port = dut.BA[7:0];
    last_value = dut.DB;
    if (!pit_started && dut.BA[7:0] == 8'h13 && dut.DB == 8'h20)
      pit_started = 1;
    if (pit_started && !pit_recovery_done) begin
      pit_writes = pit_writes + 1;
      expected_write_index = (inject_fault && pit_writes > 24)
          ? pit_writes + 12 : pit_writes;
      if (dut.BA[7:0] !== expected_write_port[expected_write_index]
          || dut.DB !== expected_write_value[expected_write_index])
        fail("PIT write sequence");
      if ((!inject_fault && pit_writes == 40)
          || (inject_fault && pit_writes == 28))
        pit_recovery_done = 1;
    end
    if (!inject_fault && !extension_fault && pit_writes == 40
        && dut.BA[7:0] == 8'h09 && dut.DB == 8'h00 && !finishing)
      finish_clean();
  end

  always @(posedge dut.iowr_n) if (active && inject_fault
      && last_port == 8'h17 && last_value == 8'h00 && d55_ch0_reads == 1)
    #2 dut.U_PIT1.output_latch[0][15] = 1'b1;

  always @(negedge dut.iord_n) if (active) begin
    #1;
    if (dut.BA[7:0] == 8'h01) pic_reads = pic_reads + 1;
    if (dut.BA[7:0] >= 8'h0C && dut.BA[7:0] <= 8'h0E)
      ppi_reads = ppi_reads + 1;
    if (pit_started && dut.BA[7:0] >= 8'h10 && dut.BA[7:0] <= 8'h1A
        && dut.BA[1:0] != 2'b11) begin
      pit_reads = pit_reads + 1;
      if (pit_reads > 12 || dut.BA[7:0] !== expected_read_port[pit_reads])
        fail("PIT read-port sequence");
      else if (dut.DB[7] !== expected_read_sign[pit_reads])
        fail("PIT phase-tolerant DB7 predicate");
      if (dut.BA[7:0] == 8'h14) d55_ch0_reads = d55_ch0_reads + 1;
    end
  end

  always @(negedge dut.memw_n) if (active) mem_writes = mem_writes + 1;

  always @(posedge osc) if (active && dut.U_CPU.u.core.thalt && !finishing) begin
    finishing = 1;
    check_common();
    if (extension_fault) begin
      if (pc != rom_fail_pc + 16'd1) fail("wrong extension-checksum HLT");
      if (pit_writes != 0 || pit_reads != 0 || io_writes != 24)
        fail("extension fault reached PIT or wrong I/O count");
      if (dut.U_PIT2.mode[1] !== 3'd3 || dut.U_PIT2.reload[1] !== 17'd1000)
        fail("extension fault did not select ROM-bad tone");
      if (failures == 0)
        $display("JUKURAVI-D0-PIT-HDL: PASS path=extension-corrupt pc=%04h io=%0d pit_reads=%0d",
                 pc, io_writes, pit_reads);
    end else begin
      if (!inject_fault) fail("unexpected clean HLT before USART handoff");
      if (pc != pit_fail_pc + 16'd1) fail("wrong PIT-fail HLT");
      if (io_writes != 52 || pit_writes != 28 || pit_reads != 8)
        fail("PIT-fail I/O counts");
      if (dut.U_PIT2.mode[1] !== 3'd3 || dut.U_PIT2.reload[1] !== 17'd1333
          || dut.U_PIT2.mode[2] !== 3'd0 || dut.U_PIT2.reload[2] !== 17'd1)
        fail("PIT-fail recovery/tone state");
      if (failures == 0)
        $display("JUKURAVI-D0-PIT-HDL: PASS path=d55-db7-stuck-high pc=%04h io=%0d reads=%0d d57=%0d/%0d",
                 pc, io_writes, pit_reads, dut.U_PIT2.reload[1], dut.U_PIT2.reload[2]);
    end
    #20 $finish;
  end

  initial begin
    if (!$value$plusargs("pit_fail=%h", pit_fail_pc)) fail("missing +pit_fail PC");
    if (!$value$plusargs("rom_fail=%h", rom_fail_pc)) fail("missing +rom_fail PC");
    inject_fault = $test$plusargs("inject_fault");
    extension_fault = $test$plusargs("extension_fault");

    index = 0;
    for (chip = 0; chip < 3; chip = chip + 1) begin
      for (channel = 0; channel < 3; channel = channel + 1) begin
        index = index + 1; expected_write_port[index] = 8'h13 + 4*chip;
        expected_write_value[index] = 8'h20 + 8'h40*channel;
        index = index + 1; expected_write_port[index] = 8'h10 + 4*chip + channel;
        expected_write_value[index] = 8'hFF;
        index = index + 1; expected_write_port[index] = 8'h13 + 4*chip;
        expected_write_value[index] = 8'h40*channel;
      end
      index = index + 1; expected_write_port[index] = 8'h13 + 4*chip;
      expected_write_value[index] = 8'h20;
      index = index + 1; expected_write_port[index] = 8'h10 + 4*chip;
      expected_write_value[index] = 8'h3F;
      index = index + 1; expected_write_port[index] = 8'h13 + 4*chip;
      expected_write_value[index] = 8'h00;
    end
    index = index + 1; expected_write_port[index] = 8'h1B; expected_write_value[index] = 8'h50;
    index = index + 1; expected_write_port[index] = 8'h19; expected_write_value[index] = 8'h01;
    index = index + 1; expected_write_port[index] = 8'h1B; expected_write_value[index] = 8'h90;
    index = index + 1; expected_write_port[index] = 8'h1A; expected_write_value[index] = 8'h01;

    index = 0;
    for (chip = 0; chip < 3; chip = chip + 1) begin
      for (channel = 0; channel < 3; channel = channel + 1) begin
        index = index + 1; expected_read_port[index] = 8'h10 + 4*chip + channel;
        expected_read_sign[index] = 1'b1;
      end
      index = index + 1; expected_read_port[index] = 8'h10 + 4*chip;
      expected_read_sign[index] = (inject_fault && chip == 1) ? 1'b1 : 1'b0;
    end
  end

  initial begin
    #14000000;
    fail("time cap before PIT verdict");
    $finish;
  end
endmodule

`default_nettype wire
