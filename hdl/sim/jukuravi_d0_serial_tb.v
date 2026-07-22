`timescale 1ns/100ps
`default_nettype none

// Execute the D0 framed handshake through vm80a, D57, D11, and D104. Generated
// fixtures shorten only register delays; all protocol and terminal opcodes are
// identical to the burn image.
module jukuravi_d0_serial_tb;
  reg osc = 0;
  reg active = 0;
  reg finishing = 0;
  reg serial_in = 1;
  integer io_writes = 0;
  integer data_writes = 0;
  integer data_reads = 0;
  integer mem_writes = 0;
  integer failures = 0;
  integer expected_path = 0; // 0 valid ACK, 1 malformed ACK, 2 timeout
  reg [15:0] serial_ok_pc = 0;
  reg [15:0] serial_dead_pc = 0;
  reg [15:0] checksum = 0;
  reg [7:0] banner_crc = 0;
  reg [7:0] ack_crc = 0;

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
               .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(1'b0));

  wire [15:0] pc = dut.U_CPU.u.core.r16_pc;
  wire [7:0] architectural_e = dut.U_CPU.u.core.xchg_dh
      ? dut.U_CPU.u.core.r16_de[7:0] : dut.U_CPU.u.core.r16_hl[7:0];

  initial begin
    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    force dut.s_cts = 1'b0;
    force dut.s_sin = serial_in;
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
    $display("JUKURAVI-D0-SERIAL-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task check_data(input integer index, input [7:0] value); begin
    if (index <= 16) begin
      if (value !== 8'h55) fail("training byte");
    end else case (index)
      17: if (value !== 8'hA5) fail("banner sync 1");
      18: if (value !== 8'h5A) fail("banner sync 2");
      19: if (value !== 8'h01) fail("banner type");
      20: if (value !== 8'h04) fail("banner length");
      21: if (value !== 8'h01) fail("protocol version");
      22: if (value !== 8'h01) fail("ROM version");
      23: if (value !== checksum[15:8]) fail("ROM checksum high");
      24: if (value !== checksum[7:0]) fail("ROM checksum low");
      25: if (value !== banner_crc) fail("banner CRC");
      default: fail("extra USART data write");
    endcase
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

  task send_ack; reg [7:0] final_crc; begin
    final_crc = expected_path == 1 ? ack_crc ^ 8'h01 : ack_crc;
    send_serial_byte(8'hA5);
    send_serial_byte(8'h5A);
    send_serial_byte(8'h81);
    send_serial_byte(8'h04);
    send_serial_byte(8'h01);
    send_serial_byte(8'h01);
    send_serial_byte(checksum[15:8]);
    send_serial_byte(checksum[7:0]);
    send_serial_byte(final_crc);
  end endtask

  always @(negedge dut.iowr_n) if (active) begin
    #1;
    io_writes = io_writes + 1;
    if (dut.BA[7:0] == 8'h08) begin
      data_writes = data_writes + 1;
      check_data(data_writes, dut.DB);
    end
  end

  always @(negedge dut.iord_n) if (active) begin
    #1;
    if (dut.BA[7:0] == 8'h08) data_reads = data_reads + 1;
  end

  always @(negedge dut.memw_n) if (active) mem_writes = mem_writes + 1;

  initial begin
    wait (active && data_writes == 25);
    wait (dut.U_SIO0.tx_buffer_full == 1'b0 && dut.U_SIO0.tx_busy == 1'b0);
    if (expected_path != 2) send_ack();
  end

  always @(posedge osc) if (active && dut.U_CPU.u.core.thalt && !finishing) begin
    reg [15:0] expected_pc;
    reg [7:0] expected_a;
    integer expected_io_writes;
    finishing = 1;
    expected_pc = expected_path == 0 ? serial_ok_pc : serial_dead_pc;
    expected_a = expected_path == 0 ? 8'h01 : 8'h3E;
    expected_io_writes = expected_path == 0 ? 44 : 42;
    if (pc != expected_pc + 16'd1) fail("wrong terminal HLT");
    if (dut.U_CPU.u.core.acc !== expected_a) fail("terminal accumulator");
    if (io_writes != expected_io_writes) fail("I/O write count");
    if (data_writes != 25) fail("outbound byte count");
    if (data_reads != (expected_path == 2 ? 0 : 9)) fail("ACK byte count");
    if (mem_writes != 0) fail("RAM write before RAM test");
    if (architectural_e !== 8'hD0) fail("rolling signature is not D0");
    if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
    if (dut.ser_cts_n !== 1'b0) fail("external CTS not asserted");
    if (dut.U_PIT2.reload[0] !== 17'd8 || dut.U_PIT2.mode[0] !== 3'd2)
      fail("D57 baud generator programming");
    if (dut.U_SIO0.tx_buffer_full !== 1'b0 || dut.U_SIO0.tx_busy !== 1'b0)
      fail("USART transmitter not empty");
    if (failures == 0)
      $display("JUKURAVI-D0-SERIAL-HDL: PASS path=%0d pc=%04h signature=%02h tx=%0d rx=%0d io=%0d ram_writes=%0d",
               expected_path, pc, architectural_e, data_writes, data_reads,
               io_writes, mem_writes);
    #20 $finish;
  end

  initial begin
    if (!$value$plusargs("serial_ok=%h", serial_ok_pc)) fail("missing +serial_ok PC");
    if (!$value$plusargs("serial_dead=%h", serial_dead_pc)) fail("missing +serial_dead PC");
    if (!$value$plusargs("checksum=%h", checksum)) fail("missing +checksum");
    if (!$value$plusargs("banner_crc=%h", banner_crc)) fail("missing +banner_crc");
    if (!$value$plusargs("ack_crc=%h", ack_crc)) fail("missing +ack_crc");
    if ($test$plusargs("malformed")) expected_path = 1;
    if ($test$plusargs("timeout")) expected_path = 2;
  end

  initial begin
    #30000000;
    $display("JUKURAVI-D0-SERIAL-HDL: TIMEOUT pc=%04h io=%0d tx=%0d rx=%0d full=%b busy=%b rx_ready=%b",
             pc, io_writes, data_writes, data_reads, dut.U_SIO0.tx_buffer_full,
             dut.U_SIO0.tx_busy, dut.U_SIO0.rx_ready);
    fail("time cap before terminal PC");
    $finish;
  end
endmodule

`default_nettype wire
