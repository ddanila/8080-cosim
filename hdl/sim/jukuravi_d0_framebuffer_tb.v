`timescale 1ns/100ps
`default_nettype none

// Execute a one-page framebuffer survey followed by eight exact address-XOR
// rows through vm80a and the bit-sliced D84-D91 DRAM. Only loop immediates are
// shortened; the burn image's survey, pattern, readback, and failure opcodes
// are unchanged. The sim-only pixel oracle is checked separately from X7.
module jukuravi_d0_framebuffer_tb;
  localparam integer FIXTURE_BYTES = 320;
  reg osc = 0;
  reg dotclk = 0;
  reg active = 0;
  reg finishing = 0;
  reg serial_in = 1;
  reg scan_active = 0;
  integer inject_fault = 0;
  integer io_writes = 0;
  integer data_writes = 0;
  integer data_reads = 0;
  integer pic_reads = 0;
  integer ppi_reads = 0;
  integer pit_reads = 0;
  integer ram_writes = 0;
  integer ram_reads = 0;
  integer pattern_writes = 0;
  integer post_survey_reads = 0;
  integer failures = 0;
  integer index;
  integer bit_index;
  reg [15:0] success_pc = 0;
  reg [15:0] failure_pc = 0;
  reg [15:0] checksum = 0;
  reg [7:0] banner_crc = 0;
  reg [7:0] ack_crc = 0;
  reg [7:0] block_crc = 0;
  reg [7:0] expected_tx [1:48];

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
               .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(1'b0),
               .dotclk(dotclk));

  wire [15:0] pc = dut.U_CPU.u.core.r16_pc;

  function [7:0] dram_byte(input integer address); begin
    dram_byte = {dut.U_D91.mem[address], dut.U_D90.mem[address],
                 dut.U_D89.mem[address], dut.U_D88.mem[address],
                 dut.U_D87.mem[address], dut.U_D86.mem[address],
                 dut.U_D85.mem[address], dut.U_D84.mem[address]};
  end endfunction

  function [7:0] address_xor(input integer address); begin
    address_xor = address[15:8] ^ address[7:0];
  end endfunction

  task fail(input [1023:0] message); begin
    $display("JUKURAVI-D0-FRAMEBUFFER-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task send_serial_byte(input [7:0] value); integer serial_bit; begin
    @(negedge dut.pit_baud); serial_in = 1'b0;
    @(posedge dut.pit_baud);
    for (serial_bit = 0; serial_bit < 8; serial_bit = serial_bit + 1) begin
      @(negedge dut.pit_baud); serial_in = value[serial_bit];
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
    send_serial_byte(8'h01); send_serial_byte(8'h08);
    send_serial_byte(checksum[15:8]); send_serial_byte(checksum[7:0]);
    send_serial_byte(ack_crc);
  end endtask

  task check_abstract_pixels;
    integer byte_offset; integer pixel; reg expected; reg [7:0] expected_byte;
  begin
    scan_active = 1;
    for (byte_offset = 0; byte_offset < FIXTURE_BYTES;
         byte_offset = byte_offset + 1) begin
      for (pixel = 7; pixel >= 0; pixel = pixel - 1) begin
        #10 dotclk = 1'b1;
        #10 dotclk = 1'b0;
        #1;
        expected_byte = address_xor(16'hD800 + byte_offset);
        expected = expected_byte[pixel];
        if (dut.vid_out !== expected) fail("abstract pixel mismatch");
      end
    end
    scan_active = 0;
  end endtask

  initial begin
    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    force dut.s_cts = 1'b0;
    force dut.s_sin = serial_in;
    #1;
    // The bounded survey covers D800..D8FF. Seed only the next 64 bytes needed
    // by the exact 320-byte preverification loop; the burn image surveys all.
    for (index = 16'hD900; index < 16'hD940; index = index + 1) begin
      dut.U_D84.mem[index] = 1'b1; dut.U_D85.mem[index] = 1'b0;
      dut.U_D86.mem[index] = 1'b1; dut.U_D87.mem[index] = 1'b0;
      dut.U_D88.mem[index] = 1'b1; dut.U_D89.mem[index] = 1'b0;
      dut.U_D90.mem[index] = 1'b1; dut.U_D91.mem[index] = 1'b0;
    end
    if (inject_fault) dut.U_D84.mem[16'hD800] = 1'b0;
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

  always @(negedge dut.iowr_n) if (active) begin
    #1;
    io_writes = io_writes + 1;
    if (dut.BA[7:0] == 8'h08) begin
      data_writes = data_writes + 1;
      if (data_writes > 48 || dut.DB !== expected_tx[data_writes])
        fail("outbound protocol byte");
    end
  end

  always @(negedge dut.iord_n) if (active) begin
    #1;
    if (dut.BA[7:0] == 8'h08) data_reads = data_reads + 1;
    if (dut.BA[7:0] == 8'h01) pic_reads = pic_reads + 1;
    if (dut.BA[7:0] >= 8'h0C && dut.BA[7:0] <= 8'h0E)
      ppi_reads = ppi_reads + 1;
    if (dut.BA[7:0] >= 8'h10 && dut.BA[7:0] <= 8'h1A
        && dut.BA[1:0] != 2'b11)
      pit_reads = pit_reads + 1;
  end

  always @(negedge dut.memw_n) if (active) begin
    #1;
    if (dut.BA >= 16'h4000) begin
      ram_writes = ram_writes + 1;
      if (data_writes == 48 && dut.BA >= 16'hD800 && dut.BA < 16'hD940)
        pattern_writes = pattern_writes + 1;
    end
  end

  always @(posedge dut.memw_n) if (active && inject_fault
      && dut.BA == 16'hD800)
    #2 dut.U_D84.mem[16'hD800] = 1'b0;

  always @(negedge dut.memr_n) if (active) begin
    #1;
    if (dut.BA >= 16'h4000) begin
      ram_reads = ram_reads + 1;
      if (data_writes == 48 && dut.BA >= 16'hD800 && dut.BA < 16'hD940)
        post_survey_reads = post_survey_reads + 1;
    end
  end

  initial begin
    wait (active && data_writes == 25);
    wait (dut.U_SIO0.tx_buffer_full == 1'b0 && dut.U_SIO0.tx_busy == 1'b0);
    send_ack();
  end

  always @(posedge osc) if (active && dut.U_CPU.u.core.thalt && !finishing) begin
    integer expected_writes;
    integer expected_reads;
    finishing = 1;
    expected_writes = inject_fault ? 1282 : 1602;
    expected_reads = inject_fault ? 1281 : 1920;
    if (pc != (inject_fault ? failure_pc : success_pc) + 16'd1)
      fail("wrong terminal HLT");
    if (data_writes != 48 || data_reads != 9) fail("serial byte counts");
    if (pic_reads != 2 || ppi_reads != 6 || pit_reads != 12)
      fail("peripheral read counts");
    if (io_writes != (inject_fault ? 140 : 137)) fail("I/O write count");
    if (ram_writes != expected_writes || ram_reads != expected_reads)
      fail("RAM traffic count");
    if (pattern_writes != (inject_fault ? 0 : FIXTURE_BYTES))
      fail("pattern write count");
    if (post_survey_reads != (inject_fault ? 1 : 2*FIXTURE_BYTES))
      fail("post-survey read count");
    if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
    if (dut.U_PPI0.pc[1:0] !== 2'b00) fail("memory mode changed");
    if (dut.U_INTR.mask !== 8'hFF) fail("PIC mask is not FF");
    if (dut.U_PPI1.regs[3] !== 8'h9B) fail("D27 control is not 9B");
    if (dut.U_SIO0.tx_buffer_full !== 1'b0 || dut.U_SIO0.tx_busy !== 1'b0)
      fail("USART transmitter not empty");

    if (inject_fault) begin
      if (dram_byte(16'hD800) !== 8'h54) fail("fault byte was not retained");
      if (dram_byte(16'hD801) !== 8'h55) fail("fault path drew a pattern");
      if (dut.U_PIT2.mode[1] !== 3'd3 || dut.U_PIT2.reload[1] !== 17'd667)
        fail("framebuffer-fail tone");
    end else begin
      for (index = 16'hD800; index < 16'hD940; index = index + 1)
        if (dram_byte(index) !== address_xor(index))
          fail("address-XOR DRAM pattern");
      if (dram_byte(16'hD940) !== 8'h00) fail("pattern exceeded fixture bound");
      check_abstract_pixels();
    end
    if (failures == 0)
      $display("JUKURAVI-D0-FRAMEBUFFER-HDL: PASS fault=%0d pc=%04h tx=%0d writes=%0d reads=%0d pattern=%0d pixels=%0d",
               inject_fault, pc, data_writes, ram_writes, ram_reads,
               pattern_writes, inject_fault ? 0 : FIXTURE_BYTES*8);
    #20 $finish;
  end

  initial begin
    if (!$value$plusargs("success=%h", success_pc)) fail("missing +success PC");
    if (!$value$plusargs("failure=%h", failure_pc)) fail("missing +failure PC");
    if (!$value$plusargs("checksum=%h", checksum)) fail("missing +checksum");
    if (!$value$plusargs("banner_crc=%h", banner_crc)) fail("missing +banner_crc");
    if (!$value$plusargs("ack_crc=%h", ack_crc)) fail("missing +ack_crc");
    if (!$value$plusargs("block_crc=%h", block_crc)) fail("missing +block_crc");
    inject_fault = $test$plusargs("inject_fault");

    for (index = 1; index <= 16; index = index + 1) expected_tx[index] = 8'h55;
    expected_tx[17]=8'hA5; expected_tx[18]=8'h5A; expected_tx[19]=8'h01;
    expected_tx[20]=8'h04; expected_tx[21]=8'h01; expected_tx[22]=8'h08;
    expected_tx[23]=checksum[15:8]; expected_tx[24]=checksum[7:0];
    expected_tx[25]=banner_crc;
    expected_tx[26]=8'hA5; expected_tx[27]=8'h5A; expected_tx[28]=8'h10;
    expected_tx[29]=8'h04; expected_tx[30]=8'h01; expected_tx[31]=8'h40;
    expected_tx[32]=8'hFF; expected_tx[33]=8'h01; expected_tx[34]=8'h51;
    expected_tx[35]=8'hA5; expected_tx[36]=8'h5A; expected_tx[37]=8'h11;
    expected_tx[38]=8'h02; expected_tx[39]=8'hD8;
    expected_tx[40]=inject_fault ? 8'h01 : 8'h00; expected_tx[41]=block_crc;
    expected_tx[42]=8'hA5; expected_tx[43]=8'h5A; expected_tx[44]=8'h12;
    expected_tx[45]=8'h02; expected_tx[46]=8'h40; expected_tx[47]=8'hFF;
    expected_tx[48]=8'h35;
  end

  initial begin
    #200000000;
    fail("time cap before framebuffer verdict");
    $finish;
  end
endmodule

`default_nettype wire
