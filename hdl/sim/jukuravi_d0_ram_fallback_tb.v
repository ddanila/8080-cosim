`timescale 1ns/100ps
`default_nettype none

// Exercise the no-ACK fallback through vm80a, D57, and the D84-D91 bank.
// Generated fixtures shorten only register counts: one page per 4 KiB window.
module jukuravi_d0_ram_fallback_tb;
  reg osc = 0;
  reg active = 0;
  reg finishing = 0;
  reg serial_in = 1;
  reg [15:0] last_ram_write = 0;
  integer inject_fault = 0;
  integer io_writes = 0;
  integer data_writes = 0;
  integer data_reads = 0;
  integer ram_writes = 0;
  integer ram_reads = 0;
  integer pit_writes = 0;
  integer video_pit_writes = 0;
  integer tone_programs = 0;
  integer silences = 0;
  integer failures = 0;
  integer index;
  reg [15:0] windows_found_pc = 0;
  reg [15:0] no_windows_pc = 0;
  reg [15:0] checksum = 0;
  reg [7:0] banner_crc = 0;
  reg [7:0] rom_version = 8'h03;
  integer prefix_writes = 0;
  integer prefix_pit_writes = 0;
  integer prefix_silences = 0;
  reg [7:0] expected_pit_port [1:14];
  reg [7:0] expected_pit_value [1:14];

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
               .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(1'b0));

  wire [15:0] pc = dut.U_CPU.u.core.r16_pc;
  wire [7:0] architectural_e = dut.U_CPU.u.core.xchg_dh
      ? dut.U_CPU.u.core.r16_de[7:0] : dut.U_CPU.u.core.r16_hl[7:0];

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
    $display("JUKURAVI-D0-RAM-FALLBACK-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task check_data(input integer byte_index, input [7:0] value); begin
    if (byte_index <= 16) begin
      if (value !== 8'h55) fail("training byte");
    end else case (byte_index)
      17: if (value !== 8'hA5) fail("banner sync 1");
      18: if (value !== 8'h5A) fail("banner sync 2");
      19: if (value !== 8'h01) fail("banner type");
      20: if (value !== 8'h04) fail("banner length");
      21: if (value !== 8'h01) fail("protocol version");
      22: if (value !== rom_version) fail("ROM version");
      23: if (value !== checksum[15:8]) fail("ROM checksum high");
      24: if (value !== checksum[7:0]) fail("ROM checksum low");
      25: if (value !== banner_crc) fail("banner CRC");
      default: fail("extra USART data write");
    endcase
  end endtask

  always @(negedge dut.iowr_n) if (active) begin
    #1;
    io_writes = io_writes + 1;
    if (dut.BA[7:0] == 8'h08) begin
      data_writes = data_writes + 1;
      check_data(data_writes, dut.DB);
    end
    if (dut.BA[7:0] >= 8'h10 && dut.BA[7:0] <= 8'h17) begin
      pit_writes = pit_writes + 1;
      if (pit_writes > prefix_pit_writes) begin
        video_pit_writes = video_pit_writes + 1;
        if (video_pit_writes > 14
            || dut.BA[7:0] !== expected_pit_port[video_pit_writes]
            || dut.DB !== expected_pit_value[video_pit_writes])
          fail("video PIT initialization");
      end
    end
    if (dut.BA[7:0] == 8'h1B && dut.DB == 8'h76)
      tone_programs = tone_programs + 1;
    if (dut.BA[7:0] == 8'h1B && dut.DB == 8'h50)
      silences = silences + 1;
  end

  always @(negedge dut.iord_n) if (active) begin
    #1;
    if (dut.BA[7:0] == 8'h08) data_reads = data_reads + 1;
  end

  always @(negedge dut.memw_n) if (active) begin
    #1;
    if ((dut.BA >= 16'h4000 && dut.BA <= 16'h40FF)
        || (dut.BA >= 16'hC000 && dut.BA <= 16'hC0FF)) begin
      ram_writes = ram_writes + 1;
      last_ram_write = dut.BA;
    end
  end
  always @(posedge dut.memw_n) if (active && inject_fault
      && ((last_ram_write >= 16'h4000 && last_ram_write <= 16'h40FF)
          || (last_ram_write >= 16'hC000 && last_ram_write <= 16'hC0FF)))
    #2 dut.U_D87.mem[last_ram_write] = 1'b0;

  always @(negedge dut.memr_n) if (active) begin
    #1;
    if ((dut.BA >= 16'h4000 && dut.BA <= 16'h40FF)
        || (dut.BA >= 16'hC000 && dut.BA <= 16'hC0FF))
      ram_reads = ram_reads + 1;
  end

  always @(posedge osc) if (active && dut.U_CPU.u.core.thalt && !finishing) begin
    reg [15:0] expected_pc;
    reg [7:0] expected_e;
    integer expected_io;
    integer expected_tones;
    integer expected_silences;
    integer bad_cells;
    finishing = 1;
    expected_pc = inject_fault ? no_windows_pc : windows_found_pc;
    expected_e = inject_fault ? 8'h00 : 8'h03;
    expected_io = (inject_fault ? 81 : 73) + prefix_writes;
    expected_tones = inject_fault ? 7 : 5;
    expected_silences = (inject_fault ? 6 : 5) + prefix_silences;
    if (pc != expected_pc + 16'd1) fail("wrong terminal HLT");
    if (architectural_e !== expected_e) fail("candidate-good flags");
    if (io_writes != expected_io) fail("I/O write count");
    if (data_writes != 25 || data_reads != 0) fail("serial byte counts");
    if (pit_writes != prefix_pit_writes + 14 || video_pit_writes != 14)
      fail("video PIT write count");
    if (tone_programs != expected_tones || silences != expected_silences)
      fail("beep cadence counts");
    if (ram_writes != 2560 || ram_reads != 2560) fail("fallback RAM traffic");
    if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
    if (dut.U_PPI0.pc[1:0] !== 2'b00) fail("memory mode changed");
    if (inject_fault) begin
      if (dut.U_PIT2.mode[1] !== 3'd3 || dut.U_PIT2.reload[1] !== 17'd16000)
        fail("no-window continuous tone");
    end else if (dut.U_PIT2.mode[1] !== 3'd0 || dut.U_PIT2.reload[1] !== 17'd1) begin
      fail("windows-found terminal silence");
    end
    bad_cells = 0;
    for (index = 16'h4000; index <= 16'h40FF; index = index + 1)
      if (dram_byte(index) !== 8'h55) bad_cells = bad_cells + 1;
    if (bad_cells != 0) fail("first window final fill");
    bad_cells = 0;
    for (index = 16'hC000; index <= 16'hC0FF; index = index + 1)
      if (dram_byte(index) !== 8'h55) bad_cells = bad_cells + 1;
    if (bad_cells != 0) fail("second window final fill");
    if (failures == 0)
      $display("JUKURAVI-D0-RAM-FALLBACK-HDL: PASS fault=%0d pc=%04h flags=%02h tx=%0d writes=%0d reads=%0d tones=%0d/%0d",
               inject_fault, pc, architectural_e, data_writes, ram_writes,
               ram_reads, tone_programs, silences);
    #20 $finish;
  end

  initial begin
    if (!$value$plusargs("windows_found=%h", windows_found_pc))
      fail("missing +windows_found PC");
    if (!$value$plusargs("no_windows=%h", no_windows_pc))
      fail("missing +no_windows PC");
    if (!$value$plusargs("checksum=%h", checksum)) fail("missing +checksum");
    if (!$value$plusargs("banner_crc=%h", banner_crc)) fail("missing +banner_crc");
    if (!$value$plusargs("rom_version=%h", rom_version)) rom_version = 8'h03;
    if (!$value$plusargs("prefix_writes=%d", prefix_writes)) prefix_writes = 0;
    if (!$value$plusargs("prefix_pit_writes=%d", prefix_pit_writes))
      prefix_pit_writes = 0;
    if (!$value$plusargs("prefix_silences=%d", prefix_silences))
      prefix_silences = 0;
    inject_fault = $test$plusargs("inject_fault");

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
    #20000000;
    $display("JUKURAVI-D0-RAM-FALLBACK-HDL: TIMEOUT pc=%04h tx=%0d writes=%0d reads=%0d",
             pc, data_writes, ram_writes, ram_reads);
    fail("time cap before terminal PC");
    $finish;
  end
endmodule

`default_nettype wire
