`timescale 1ns/100ps
`default_nettype none

// Execute the time-compressed local-8251 diagnostic through the vm80a-based
// juku_top. Fixtures shorten only register delays; all test and terminal-path
// opcodes remain identical to the burn image.
module jukuravi_d0_usart_local_tb;
  reg osc = 0;
  reg active = 0;
  reg finishing = 0;
  reg data_written = 0;
  integer io_writes = 0;
  integer io_reads = 0;
  integer mem_writes = 0;
  integer baud_edges = 0;
  integer status_stage = 0;
  integer failures = 0;
  integer expected_path = 0; // 0 success, 1 CPU-bad, 2 USART-bad
  integer inject_stuck = 0;
  integer block_cts = 0;
  reg [15:0] success_pc = 0;
  reg [15:0] cpu_fail_pc = 0;
  reg [15:0] usart_fail_pc = 0;

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
               .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(1'b0));

  wire [15:0] pc = dut.U_CPU.u.core.r16_pc;
  wire [7:0] architectural_e = dut.U_CPU.u.core.xchg_dh
      ? dut.U_CPU.u.core.r16_de[7:0] : dut.U_CPU.u.core.r16_hl[7:0];

  initial begin
    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    // The Nano/level-shifter fixture must assert X3 CTS; an open MC1489-class
    // receiver input produces inactive-high /CTS and legitimately blocks D11.
    if ($test$plusargs("block_cts")) force dut.s_cts = 1'b1;
    else                             force dut.s_cts = 1'b0;
    #2000;
    force dut.reset_sys = 1'b0;
    active = 1;
  end

  initial forever begin
    force dut.phi1 = 1'b1; force dut.phi2 = 1'b0; osc = 0; #10; osc = 1; #10;
    force dut.phi1 = 1'b0; force dut.phi2 = 1'b1; osc = 0; #10; osc = 1; #10;
    force dut.phi2 = 1'b0;
  end

  // The physical merge feeding the declared 16 MHz rail remains a documented
  // continuity boundary. Drive only that upstream boundary here; D103 /13,
  // D57 channel 0 /8, and both D11 clock pins remain the full-top signal path.
  initial forever begin
    force dut.xtal16m_w = 1'b0; #2;
    force dut.xtal16m_w = 1'b1; #2;
  end

  task fail(input [1023:0] message); begin
    $display("JUKURAVI-D0-USART-LOCAL-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task check_io(input integer index, input [7:0] port, input [7:0] value); begin
    case (index)
      1:  if (port !== 8'h1B || value !== 8'h76) fail("alive control");
      2:  if (port !== 8'h19 || value !== 8'hD0) fail("alive divisor low");
      3:  if (port !== 8'h19 || value !== 8'h07) fail("alive divisor high");
      4:  if (port !== 8'h1B || value !== 8'h50) fail("silence control");
      5:  if (port !== 8'h19 || value !== 8'h01) fail("silence count");
      6:  if (expected_path == 1 ? (port !== 8'h1B || value !== 8'h76)
                                : (port !== 8'h09 || value !== 8'h00)) fail("write 6");
      7:  if (expected_path == 1 ? (port !== 8'h19 || value !== 8'h40)
                                : (port !== 8'h09 || value !== 8'h00)) fail("write 7");
      8:  if (expected_path == 1 ? (port !== 8'h19 || value !== 8'h1F)
                                : (port !== 8'h09 || value !== 8'h00)) fail("write 8");
      9:  if (port !== 8'h09 || value !== 8'h40) fail("USART internal reset");
      10: if (port !== 8'h09 || value !== 8'h4E) fail("USART mode");
      11: if (port !== 8'h09 || value !== 8'h37) fail("USART command");
      12: if (port !== 8'h08 || value !== 8'h55) fail("USART test byte");
      13: if (port !== 8'h1B || value !== 8'h34) fail("baud control");
      14: if (port !== 8'h18 || value !== 8'h08) fail("baud divisor low");
      15: if (port !== 8'h18 || value !== 8'h00) fail("baud divisor high");
      16: if (expected_path != 2 || port !== 8'h1B || value !== 8'h76) fail("USART-bad control");
      17: if (expected_path != 2 || port !== 8'h19 || value !== 8'hA0) fail("USART-bad divisor low");
      18: if (expected_path != 2 || port !== 8'h19 || value !== 8'h0F) fail("USART-bad divisor high");
      default: fail("unexpected extra I/O write");
    endcase
  end endtask

  task check_status(input [7:0] value); begin
    case (status_stage)
      0: if ((value & 8'h05) == 8'h05) status_stage = 1;
         else fail("initial status is not 05");
      1: if ((value & 8'h05) == 8'h00) status_stage = 2;
         else fail("holding-full status is not 00");
      2: if ((value & 8'h05) == 8'h01) status_stage = 3;
         else if ((value & 8'h05) != 8'h00) fail("waiting-TxRDY status");
      3: if ((value & 8'h05) == 8'h05) status_stage = 4;
         else if ((value & 8'h05) != 8'h01) fail("waiting-TxEMPTY status");
      4: if ((value & 8'h05) != 8'h05) fail("final status regressed");
      default: fail("invalid status stage");
    endcase
  end endtask

  always @(negedge dut.iowr_n) if (active) begin
    #1;
    io_writes = io_writes + 1;
    check_io(io_writes, dut.BA[7:0], dut.DB);
    if (dut.BA[7:0] == 8'h08 && dut.DB == 8'h55) begin
      data_written = 1;
      if (inject_stuck) force dut.U_SIO0.tx_buffer_full = 1'b1;
    end
  end

  always @(negedge dut.iord_n) if (active) begin
    #1;
    io_reads = io_reads + 1;
    if (dut.BA[7:0] == 8'h09) check_status(dut.DB);
  end

  always @(posedge dut.pit_baud) if (active && data_written) baud_edges = baud_edges + 1;
  always @(negedge dut.memw_n) if (active) mem_writes = mem_writes + 1;

  always @(posedge osc) if (active && dut.U_CPU.u.core.thalt && !finishing) begin
    reg [15:0] expected_pc;
    reg [7:0] expected_a;
    finishing = 1;
    expected_pc = expected_path == 1 ? cpu_fail_pc
                : expected_path == 2 ? usart_fail_pc : success_pc;
    expected_a = expected_path == 1 ? 8'h1F
               : expected_path == 2 ? 8'h0F : 8'h05;
    if (pc != expected_pc + 16'd1) fail("wrong terminal HLT");
    if (io_writes != (expected_path == 0 ? 15 : expected_path == 1 ? 8 : 18))
      fail("I/O write count");
    if (mem_writes != 0) fail("RAM write before RAM test");
    if (architectural_e !== 8'hD0) fail("rolling signature is not D0");
    if (dut.U_CPU.u.core.acc !== expected_a) fail("terminal accumulator");
    if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
    if (expected_path == 0) begin
      if (status_stage != 4) fail("normal status progression incomplete");
      if (dut.U_SIO0.tx_buffer !== 8'h55) fail("USART holding byte");
      if (dut.U_SIO0.tx_buffer_full !== 1'b0 || dut.U_SIO0.tx_busy !== 1'b0)
        fail("USART not empty at success");
      if (baud_edges < 10) fail("too few D57 baud edges");
    end else if (expected_path == 2 && status_stage != 2) begin
      fail("stuck-TX status progression differs");
    end else if (expected_path == 1 && status_stage != 0) begin
      fail("CPU-bad path touched USART status");
    end
    if (expected_path != 1) begin
      if (dut.ser_cts_n !== (block_cts ? 1'b1 : 1'b0)) fail("external CTS stimulus");
      if (dut.U_PIT2.reload[0] !== 17'd8 || dut.U_PIT2.mode[0] !== 3'd2)
        fail("D57 baud generator programming");
    end
    if (failures == 0)
      $display("JUKURAVI-D0-USART-LOCAL-HDL: PASS path=%0d pc=%04h signature=%02h status_stage=%0d io=%0d baud_edges=%0d ram_writes=%0d",
               expected_path, pc, architectural_e, status_stage, io_writes,
               baud_edges, mem_writes);
    #20 $finish;
  end

  initial begin
    if (!$value$plusargs("success=%h", success_pc)) fail("missing +success PC");
    if (!$value$plusargs("cpu_fail=%h", cpu_fail_pc)) fail("missing +cpu_fail PC");
    if (!$value$plusargs("usart_fail=%h", usart_fail_pc)) fail("missing +usart_fail PC");
    if ($test$plusargs("expect_cpu_fail")) expected_path = 1;
    if ($test$plusargs("expect_usart_fail")) expected_path = 2;
    inject_stuck = $test$plusargs("inject_stuck");
    block_cts = $test$plusargs("block_cts");
  end

  initial begin
    #10000000;
    $display("JUKURAVI-D0-USART-LOCAL-HDL: TIMEOUT pc=%04h io=%0d reads=%0d stage=%0d pit_mode=%0d pit_reload=%0d pit=%b full=%b busy=%b baud_edges=%0d",
             pc, io_writes, io_reads, status_stage, dut.U_PIT2.mode[0],
             dut.U_PIT2.reload[0], dut.pit_baud, dut.U_SIO0.tx_buffer_full,
             dut.U_SIO0.tx_busy, baud_edges);
    fail("time cap before terminal PC");
    $finish;
  end
endmodule

`default_nettype wire
