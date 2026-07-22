`timescale 1ns/100ps
`default_nettype none

// Execute one time-bounded page of the burn image's full RAM-survey loop
// through vm80a and the bit-sliced D84-D91 DRAM bank. Only loop/delay immediates
// are shortened in the generated fixture; protocol and test opcodes are exact.
module jukuravi_d0_ram_tb;
  reg osc = 0;
  reg active = 0;
  reg finishing = 0;
  reg serial_in = 1;
  integer io_writes = 0;
  integer data_writes = 0;
  integer data_reads = 0;
  integer ram_writes = 0;
  integer ram_reads = 0;
  integer pit_writes = 0;
  integer failures = 0;
  integer inject_fault = 0;
  integer index;
  reg [15:0] success_pc = 0;
  reg [15:0] checksum = 0;
  reg [7:0] banner_crc = 0;
  reg [7:0] ack_crc = 0;
  reg [7:0] block_crc = 0;
  reg [7:0] expected_tx [1:48];
  reg [7:0] expected_pit_port [1:14];
  reg [7:0] expected_pit_value [1:14];

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
               .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(1'b0));

  wire [15:0] pc = dut.U_CPU.u.core.r16_pc;
  wire [7:0] architectural_d = dut.U_CPU.u.core.xchg_dh
      ? dut.U_CPU.u.core.r16_de[15:8] : dut.U_CPU.u.core.r16_hl[15:8];

  function [7:0] dram_byte(input integer address); begin
    dram_byte = {dut.U_D91.mem[address], dut.U_D90.mem[address],
                 dut.U_D89.mem[address], dut.U_D88.mem[address],
                 dut.U_D87.mem[address], dut.U_D86.mem[address],
                 dut.U_D85.mem[address], dut.U_D84.mem[address]};
  end endfunction

  initial begin
    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    force dut.s_cts = 1'b0;
    force dut.s_sin = serial_in;
    #1;
    if (inject_fault) dut.U_D87.mem[16'h4080] = 1'b0;
    #1999;
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
    $display("JUKURAVI-D0-RAM-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task send_serial_byte(input [7:0] value); integer bit_index; begin
    @(negedge dut.pit_baud); serial_in = 1'b0;
    @(posedge dut.pit_baud);
    for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
      @(negedge dut.pit_baud); serial_in = value[bit_index];
      @(posedge dut.pit_baud);
    end
    @(negedge dut.pit_baud); serial_in = 1'b1;
    @(posedge dut.pit_baud);
    wait (dut.U_SIO0.rx_ready == 1'b1);
    wait (dut.U_SIO0.rx_ready == 1'b0);
  end endtask

  task send_ack; begin
    send_serial_byte(8'hA5); send_serial_byte(8'h5A);
    send_serial_byte(8'h81); send_serial_byte(8'h04);
    send_serial_byte(8'h01); send_serial_byte(8'h02);
    send_serial_byte(checksum[15:8]); send_serial_byte(checksum[7:0]);
    send_serial_byte(ack_crc);
  end endtask

  always @(negedge dut.iowr_n) if (active) begin
    #1;
    io_writes = io_writes + 1;
    if (dut.BA[7:0] == 8'h08) begin
      data_writes = data_writes + 1;
      if (data_writes > 48 || dut.DB !== expected_tx[data_writes])
        fail("outbound protocol byte");
    end
    if (dut.BA[7:0] >= 8'h10 && dut.BA[7:0] <= 8'h17) begin
      pit_writes = pit_writes + 1;
      if (pit_writes > 14 || dut.BA[7:0] !== expected_pit_port[pit_writes]
          || dut.DB !== expected_pit_value[pit_writes])
        fail("video PIT initialization");
    end
  end

  always @(negedge dut.iord_n) if (active) begin
    #1;
    if (dut.BA[7:0] == 8'h08) data_reads = data_reads + 1;
  end
  always @(negedge dut.memw_n) if (active) begin
    #1;
    if (dut.BA >= 16'h4000) ram_writes = ram_writes + 1;
  end
  always @(posedge dut.memw_n) if (active && inject_fault && dut.BA == 16'h4080)
    #2 dut.U_D87.mem[16'h4080] = 1'b0;
  always @(negedge dut.memr_n) if (active) begin
    #1;
    if (dut.BA >= 16'h4000) ram_reads = ram_reads + 1;
  end

  initial begin
    wait (active && data_writes == 25);
    wait (dut.U_SIO0.tx_buffer_full == 1'b0 && dut.U_SIO0.tx_busy == 1'b0);
    send_ack();
  end

  always @(posedge osc) if (active && dut.U_CPU.u.core.thalt && !finishing) begin
    reg [7:0] expected_mask;
    reg [7:0] expected_byte;
    finishing = 1;
    expected_mask = inject_fault ? 8'h08 : 8'h00;
    if (pc != success_pc + 16'd1) fail("wrong terminal HLT");
    if (dut.U_CPU.u.core.acc !== 8'h04) fail("terminal accumulator");
    if (architectural_d !== expected_mask) fail("page failure mask");
    if (data_writes != 48 || data_reads != 9) fail("serial byte counts");
    if (io_writes != 81 || pit_writes != 14) fail("I/O write counts");
    if (ram_writes != 1282 || ram_reads != 1280) fail("RAM pass counts");
    if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
    if (dut.U_PPI0.pc[1:0] !== 2'b00) fail("memory mode changed");
    if (dut.U_SIO0.tx_buffer_full !== 1'b0 || dut.U_SIO0.tx_busy !== 1'b0)
      fail("USART transmitter not empty");
    for (index = 16'h4000; index <= 16'h40FF; index = index + 1) begin
      expected_byte = 8'h55;
      if (dram_byte(index) !== expected_byte) fail("final DRAM pattern");
    end
    if (failures == 0)
      $display("JUKURAVI-D0-RAM-HDL: PASS fault=%0d pc=%04h mask=%02h tx=%0d rx=%0d writes=%0d reads=%0d",
               inject_fault, pc, expected_mask, data_writes, data_reads,
               ram_writes, ram_reads);
    #20 $finish;
  end

  initial begin
    if (!$value$plusargs("success=%h", success_pc)) fail("missing +success PC");
    if (!$value$plusargs("checksum=%h", checksum)) fail("missing +checksum");
    if (!$value$plusargs("banner_crc=%h", banner_crc)) fail("missing +banner_crc");
    if (!$value$plusargs("ack_crc=%h", ack_crc)) fail("missing +ack_crc");
    if (!$value$plusargs("block_crc=%h", block_crc)) fail("missing +block_crc");
    inject_fault = $test$plusargs("inject_fault");

    for (index = 1; index <= 16; index = index + 1) expected_tx[index] = 8'h55;
    expected_tx[17]=8'hA5; expected_tx[18]=8'h5A; expected_tx[19]=8'h01;
    expected_tx[20]=8'h04; expected_tx[21]=8'h01; expected_tx[22]=8'h02;
    expected_tx[23]=checksum[15:8]; expected_tx[24]=checksum[7:0];
    expected_tx[25]=banner_crc;
    expected_tx[26]=8'hA5; expected_tx[27]=8'h5A; expected_tx[28]=8'h10;
    expected_tx[29]=8'h04; expected_tx[30]=8'h01; expected_tx[31]=8'h40;
    expected_tx[32]=8'hFF; expected_tx[33]=8'h01; expected_tx[34]=8'h51;
    expected_tx[35]=8'hA5; expected_tx[36]=8'h5A; expected_tx[37]=8'h11;
    expected_tx[38]=8'h02; expected_tx[39]=8'h40;
    expected_tx[40]=inject_fault ? 8'h08 : 8'h00; expected_tx[41]=block_crc;
    expected_tx[42]=8'hA5; expected_tx[43]=8'h5A; expected_tx[44]=8'h12;
    expected_tx[45]=8'h02; expected_tx[46]=8'h40; expected_tx[47]=8'hFF;
    expected_tx[48]=8'h35;

    expected_pit_port[1]=8'h13; expected_pit_value[1]=8'h15;
    expected_pit_port[2]=8'h13; expected_pit_value[2]=8'h53;
    expected_pit_port[3]=8'h13; expected_pit_value[3]=8'h93;
    expected_pit_port[4]=8'h17; expected_pit_value[4]=8'h73;
    expected_pit_port[5]=8'h17; expected_pit_value[5]=8'h93;
    expected_pit_port[6]=8'h17; expected_pit_value[6]=8'h34;
    expected_pit_port[7]=8'h14; expected_pit_value[7]=8'h39;
    expected_pit_port[8]=8'h14; expected_pit_value[8]=8'h01;
    expected_pit_port[9]=8'h10; expected_pit_value[9]=8'h64;
    expected_pit_port[10]=8'h11; expected_pit_value[10]=8'h24;
    expected_pit_port[11]=8'h12; expected_pit_value[11]=8'h08;
    expected_pit_port[12]=8'h15; expected_pit_value[12]=8'h72;
    expected_pit_port[13]=8'h15; expected_pit_value[13]=8'h00;
    expected_pit_port[14]=8'h16; expected_pit_value[14]=8'h25;
  end

  initial begin
    #50000000;
    $display("JUKURAVI-D0-RAM-HDL: TIMEOUT pc=%04h tx=%0d rx=%0d writes=%0d reads=%0d",
             pc, data_writes, data_reads, ram_writes, ram_reads);
    fail("time cap before terminal PC");
    $finish;
  end
endmodule

`default_nettype wire
