// Focused top-level peripheral bus harness.
//
// This does not replace the full ROMBIOS path. It proves that the LVS-checked
// juku_top decode and behavioral peripheral instances can be driven through the
// actual BA/DB/iord/iowr nets without waiting for the slow BIOS framebuffer path.
`timescale 1ns/100ps
`default_nettype none

module juku_top_periph_bus_tb();
  reg osc = 0;
  integer fails = 0;
  integer i;
  integer format_len = 0;
  integer format_output_len = 0;
  reg [7:0] rd;
  reg [7:0] format_stream [0:6249];
  reg writable_mode = 1'b0;
  reg fdc_bus_invert = 1'b0;
  reg [15:0] drive_ba = 16'h0000;
  reg [7:0] drive_db = 8'hff;
  reg kbd_en = 1'b0, kbd_pressed = 1'b0, kbd_shift = 1'b0, frame_tick = 1'b0;
  reg [3:0] kbd_kcol = 4'd0;
  reg [2:0] kbd_kbit = 3'd0;

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(kbd_en), .kbd_pressed(kbd_pressed), .kbd_shift(kbd_shift),
               .kbd_kcol(kbd_kcol), .kbd_kbit(kbd_kbit), .frame_tick(frame_tick));

  initial forever begin osc = 0; #10; osc = 1; #10; end

  task fail(input [1023:0] msg); begin
    $display("JUKU-TOP-PERIPH-BUS: FAIL %0s", msg);
    fails = fails + 1;
  end endtask

  function [15:0] io_addr(input [7:0] port); begin
    io_addr = {port, port};
  end endfunction

  function is_fdc_port(input [7:0] port); begin
    is_fdc_port = (port[4:2] == 3'd7);
  end endfunction

  task bus_idle; begin
    force dut.wr_n = 1'b1;
    force dut.dbin = 1'b0;
    force dut.iowr_n = 1'b1;
    force dut.iord_n = 1'b1;
    release dut.DB;
    #40;
  end endtask

  task io_write(input [7:0] port, input [7:0] data); begin
    @(negedge osc);
    drive_ba = io_addr(port);
    drive_db = (fdc_bus_invert && is_fdc_port(port)) ? ~data : data;
    force dut.BA = drive_ba;
    force dut.DB = drive_db;
    force dut.iord_n = 1'b1;
    force dut.iowr_n = 1'b1;
    #1;
    force dut.iowr_n = 1'b0;
    #1;
    if (port[4:2] == 3'd0 && dut.cs_pic_n) fail("PIC chip-select did not assert on write");
    if (port[4:2] == 3'd1 && dut.cs_ppi0_n) fail("PPI0 chip-select did not assert on write");
    if (port[4:2] == 3'd7) begin
      if (dut.cs_fdc_n) fail("FDC chip-select did not assert on write");
      if (dut.fdc_prom_cs_n) fail("D94 enable did not follow selected FDC write");
      if (dut.d94_a3_boundary !== dut.iowr_n) fail("D94 A3 did not match active-low IOWR");
      if (dut.fdc_prom_re_n !== 1'b1) fail("D94 /RE asserted during FDC write");
      if (dut.fdc_prom_we_n !== 1'b0) fail("D94 /WE did not assert during FDC write");
    end
    @(negedge osc);
    bus_idle();
  end endtask

  task io_read(input [7:0] port, output [7:0] data); begin
    @(negedge osc);
    drive_ba = io_addr(port);
    force dut.BA = drive_ba;
    release dut.DB;
    force dut.iowr_n = 1'b1;
    force dut.iord_n = 1'b1;
    #1;
    force dut.iord_n = 1'b0;
    #1;
    if (port[4:2] == 3'd0 && dut.cs_pic_n) fail("PIC chip-select did not assert on read");
    if (port[4:2] == 3'd1 && dut.cs_ppi0_n) fail("PPI0 chip-select did not assert on read");
    if (port[4:2] == 3'd7) begin
      if (dut.cs_fdc_n) fail("FDC chip-select did not assert on read");
      if (dut.fdc_prom_cs_n) fail("D94 enable did not follow selected FDC read");
      if (dut.d94_a3_boundary !== dut.iowr_n) fail("D94 A3 did not match active-low IOWR");
      if (dut.fdc_prom_re_n !== 1'b0) fail("D94 /RE did not assert during FDC read");
      if (dut.fdc_prom_we_n !== 1'b1) fail("D94 /WE asserted during FDC read");
    end
    @(posedge osc);
    #1;
    data = dut.DB;
    if (fdc_bus_invert && is_fdc_port(port)) data = ~data;
    @(negedge osc);
    bus_idle();
  end endtask

  task fdc_seek(input [7:0] track_id); begin
    io_write(8'h1F, track_id);
    io_write(8'h1C, 8'h10);
    while (dut.U_FDC.status[0]) @(posedge osc);
    #1;
  end endtask

  task fdc_index_pulse; begin
    force dut.U_FDC.index = 1'b0;
    #1;
    force dut.U_FDC.index = 1'b1;
    #1;
    force dut.U_FDC.index = 1'b0;
    #1;
    release dut.U_FDC.index;
  end endtask

  task inta_read(output [7:0] data); begin
    release dut.DB;
    force dut.iord_n = 1'b1;
    force dut.iowr_n = 1'b1;
    force dut.inta_n = 1'b0;
    @(posedge osc);
    #1;
    data = dut.DB;
    @(negedge osc);
    force dut.inta_n = 1'b1;
    #40;
  end endtask

  task pulse_frame; begin
    @(negedge osc);
    frame_tick = 1'b1;
    @(negedge osc);
    frame_tick = 1'b0;
    @(posedge osc);
    #1;
  end endtask

  task put_format_byte(input [7:0] value); begin
    format_stream[format_len] = value;
    format_len = format_len + 1;
    format_output_len = format_output_len + ((value == 8'hf7) ? 2 : 1);
  end endtask

  task build_format_stream(input [7:0] track_id, input side_id);
    integer sector_id;
    integer byte_index;
  begin
    format_len = 0;
    format_output_len = 0;
    for (byte_index = 0; byte_index < 32; byte_index = byte_index + 1) put_format_byte(8'h4e);
    for (sector_id = 1; sector_id <= 10; sector_id = sector_id + 1) begin
      for (byte_index = 0; byte_index < 12; byte_index = byte_index + 1) put_format_byte(8'h00);
      for (byte_index = 0; byte_index < 3; byte_index = byte_index + 1) put_format_byte(8'hf5);
      put_format_byte(8'hfe);
      put_format_byte(track_id);
      put_format_byte({7'b0, side_id});
      put_format_byte(sector_id[7:0]);
      put_format_byte(8'h02);
      put_format_byte(8'hf7);
      for (byte_index = 0; byte_index < 22; byte_index = byte_index + 1) put_format_byte(8'h4e);
      for (byte_index = 0; byte_index < 12; byte_index = byte_index + 1) put_format_byte(8'h00);
      for (byte_index = 0; byte_index < 3; byte_index = byte_index + 1) put_format_byte(8'hf5);
      put_format_byte(8'hfb);
      for (byte_index = 0; byte_index < 512; byte_index = byte_index + 1)
        put_format_byte(8'h30 + sector_id[7:0]);
      put_format_byte(8'hf7);
      for (byte_index = 0; byte_index < 35; byte_index = byte_index + 1) put_format_byte(8'h4e);
    end
    while (format_output_len < 6250) put_format_byte(8'h4e);
  end endtask

  task check_d94_data_branch; begin
    @(negedge osc);
    force dut.BA = 16'h1f1f;
    force dut.iowr_n = 1'b1;
    force dut.iord_n = 1'b0;
    force dut.d94_a4_d101_q0 = 1'b0;
    #1;
    if (dut.fdc_prom_cs_n !== 1'b0) fail("D94 enable did not assert for register-3 branch check");
    if (dut.d94_d0_boundary !== 1'b0) fail("D94 D0 did not assert for low-A4 register-3 cycle");
    if (dut.fdc_prom_re_n !== 1'b1) fail("D94 /RE did not release for low-A4 register-3 cycle");
    if (dut.fdc_prom_we_n !== 1'b1) fail("D94 /WE did not release for low-A4 register-3 cycle");
`ifdef FDC_VA87_CS_QUALIFIED
    if (dut.d100_t_boundary !== 1'b1) fail("qualified D100 pointed B->A while D94 /RE was suppressed");
`elsif FDC_VA87_ALWAYS_ENABLED
    if (dut.d100_t_boundary !== 1'b1) fail("always-enabled D100 pointed B->A while D94 /RE was suppressed");
`endif
    force dut.iord_n = 1'b1;
    release dut.d94_a4_d101_q0;
    release dut.BA;
    #40;
  end endtask

  initial begin
    writable_mode = $test$plusargs("expect_writable");
    fdc_bus_invert = $test$plusargs("fdc_bus_invert");
`ifdef FDC_VA87_CS_QUALIFIED
    if (!fdc_bus_invert) fail("qualified physical D100 build requires +fdc_bus_invert");
`elsif FDC_VA87_ALWAYS_ENABLED
    if (!fdc_bus_invert) fail("always-enabled physical D100 build requires +fdc_bus_invert");
`else
    if (fdc_bus_invert) fail("logical DB build must not use +fdc_bus_invert");
`endif
    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    force dut.phi1 = 1'b0;
    force dut.phi2 = 1'b0;
    bus_idle();
    #200;
    force dut.reset_sys = 1'b0;
    #200;

    check_d94_data_branch();

    io_write(8'h00, 8'hD6);     // PIC ICW1; ROMBIOS uses high vector bits -> 0xFED4
    io_write(8'h01, 8'hFE);     // PIC ICW2
    io_write(8'h01, 8'hDF);     // unmask IR5, matching ROMBIOS frame path
    io_read(8'h01, rd);
    if (rd !== 8'hDF) fail("PIC register readback mismatch");

    pulse_frame();
    if (dut.intr !== 1'b1) fail("frame tick did not raise top-level INTR after PIC unmask");
    inta_read(rd);
    if (rd !== 8'hCD) fail("first INTA byte should be CALL opcode");
    inta_read(rd);
    if (rd !== 8'hD4) fail("second INTA byte should be low byte of 0xFED4");
    inta_read(rd);
    if (rd !== 8'hFE) fail("third INTA byte should be high byte of 0xFED4");
    @(posedge osc);
    #1;
    if (dut.intr !== 1'b0) fail("INTR did not clear after three INTA bytes");

    kbd_en = 1'b1;
    kbd_pressed = 1'b0;
    io_write(8'h04, 8'h04);     // PPI0 Port A: scan column 4
    io_read(8'h05, rd);
    if (rd !== 8'hCF) fail("PPI0 no-key keyboard read did not match ROMBIOS first read");

    kbd_pressed = 1'b1;
    kbd_shift = 1'b1;
    kbd_kcol = 4'd4;            // T key
    kbd_kbit = 3'd3;
    io_read(8'h05, rd);
    if (rd !== 8'h88) fail("PPI0 keyboard read did not encode shifted T");
    kbd_pressed = 1'b0;

    io_write(8'h06, 8'h04);     // PPI0 Port C: motor on, mode 0
    if (dut.ppi0_pc[2] !== 1'b1) fail("PPI0 PC2 motor-on bit did not latch");

    io_read(8'h1C, rd);
    if ((rd & 8'h80) !== 8'h00) fail("FDC status should clear NOT READY once motor is on");

    io_write(8'h1D, 8'h22);     // nonzero track before ROMBIOS first restore command
    io_write(8'h1C, 8'h02);     // exact ROMBIOS first FDC command from PC E5DE
    while (dut.U_FDC.status[0]) @(posedge osc);
    #1;
    if (dut.U_FDC.command !== 8'h02) fail("FDC command latch did not capture ROMBIOS restore");
    if (dut.fdc_intrq !== 1'b1) fail("FDC restore did not raise INTRQ");
    io_read(8'h1C, rd);
    if ((rd & 8'h83) !== 8'h00) fail("FDC restore status should clear NOT_READY/BUSY/DRQ with motor on");
    if ((rd & 8'h64) !== (writable_mode ? 8'h04 : 8'h44))
      fail("FDC restore Type-I status did not report TRACK0/media-protect/head-unloaded");
    if (dut.fdc_intrq !== 1'b0) fail("FDC status read did not acknowledge restore INTRQ");
    io_read(8'h1D, rd);
    if (rd !== 8'h00) fail("FDC restore did not return track register to zero");

    io_write(8'h1F, 8'h02);     // FDC data register: seek target / sector byte
    io_write(8'h1D, 8'h00);     // FDC track register
    io_write(8'h1E, 8'h02);     // FDC sector register
    io_write(8'h1C, 8'h10);     // FDC seek: track <= data
    while (dut.U_FDC.status[0]) @(posedge osc);
    #1;
    io_read(8'h1D, rd);
    if (rd !== 8'h02) fail("FDC seek did not update track register through top-level bus");

    io_write(8'h1C, 8'h44);     // step in without update, then verify
    while (dut.U_FDC.status[0]) @(posedge osc);
    #1;
    io_read(8'h1D, rd);
    if (rd !== 8'h02 || dut.U_FDC.physical_track !== 8'h03)
      fail("FDC no-update step did not separate physical head and Track register");
    io_read(8'h1C, rd);
    if ((rd & 8'h30) !== 8'h30) fail("FDC Type-I verify did not report SEEK ERROR/head loaded");
    fdc_seek(8'h0e);
    if (dut.U_FDC.track !== 8'h0e || dut.U_FDC.physical_track !== 8'h0f)
      fail("FDC seek did not preserve the physical/register track offset");

    io_write(8'h1C, 8'h00);      // RESTORE physically recalibrates track zero
    while (dut.U_FDC.status[0]) @(posedge osc);
    #1;
    io_write(8'h1C, 8'h80);     // FDC read-sector command
    while (dut.U_FDC.drq_ticks < 63) @(posedge osc);
    #1;
    if (dut.U_FDC.buffer_pos !== 0 || (dut.U_FDC.status & 8'h04) !== 0) begin
      $display("JUKU-TOP-PERIPH-BUS: deadline early pos=%0d ticks=%0d status=%02x",
               dut.U_FDC.buffer_pos, dut.U_FDC.drq_ticks, dut.U_FDC.status);
      fail("FDC read lost-data deadline fired before one byte time");
    end
    @(negedge osc); #1;
    if (dut.U_FDC.buffer_pos !== 1) fail("FDC read deadline did not discard one byte");
    io_read(8'h1C, rd);
    if ((rd & 8'h07) !== 8'h07) fail("FDC read-sector did not report BUSY+DRQ+LOST DATA");
    io_read(8'h1F, rd);
    if (rd !== 8'h5c) fail("FDC lost-data overwrite did not expose second vendored byte");

    io_write(8'h1C, 8'hD0);     // abort the partial single-sector read
    if (dut.fdc_intrq !== 1'b0) fail("FDC D0 abort incorrectly raised INTRQ");
    io_read(8'h1C, rd);
    if ((rd & 8'h07) !== 8'h04) fail("FDC D0 abort did not preserve LOST DATA status");
    io_write(8'h1C, 8'hD8);     // immediate Force Interrupt
    if (dut.fdc_intrq !== 1'b1) fail("FDC D8 immediate Force Interrupt did not raise INTRQ");
    io_read(8'h1C, rd);
    if (dut.fdc_intrq !== 1'b1) fail("FDC D8 immediate INTRQ did not remain asserted after status read");
    io_write(8'h1C, 8'hD0);
    if (dut.fdc_intrq !== 1'b0) fail("FDC D0 did not disarm immediate INTRQ");

    io_write(8'h1C, 8'h08);     // RESTORE with h=1 loads the head
    force dut.U_FDC.index = 1'b0;
    for (i = 0; i < 14; i = i + 1) begin
      force dut.U_FDC.index = 1'b1; #1;
      force dut.U_FDC.index = 1'b0; #1;
    end
    if (!dut.U_FDC.head_loaded || dut.U_FDC.idle_index_pulses !== 14)
      fail("FDC head unloaded before 15 idle index pulses");
    io_write(8'h1C, 8'h08);     // a Type-I command restarts the idle count
    for (i = 0; i < 14; i = i + 1) begin
      force dut.U_FDC.index = 1'b1; #1;
      force dut.U_FDC.index = 1'b0; #1;
    end
    if (!dut.U_FDC.head_loaded) fail("FDC head unloaded before restarted count reached 15");
    force dut.U_FDC.index = 1'b1; #1;
    if (dut.U_FDC.head_loaded || dut.U_FDC.idle_index_pulses !== 0)
      fail("FDC head did not unload on 15th restarted idle index pulse");
    io_read(8'h1C, rd);
    if ((rd & 8'h20) !== 0) fail("FDC Type-I status retained HEAD LOADED after idle unload");
    force dut.U_FDC.index = 1'b0;

    force dut.U_FDC.ready = 1'b0;
    io_write(8'h1C, 8'hD1);
    force dut.U_FDC.ready = 1'b1;
    #1;
    if (dut.fdc_intrq !== 1'b1) fail("FDC D1 not-ready to ready transition did not raise INTRQ");
    io_read(8'h1C, rd);
    if (dut.fdc_intrq !== 1'b0) fail("FDC status read did not acknowledge D1 INTRQ");
    force dut.U_FDC.ready = 1'b0;
    #1;
    force dut.U_FDC.ready = 1'b1;
    #1;
    if (dut.fdc_intrq !== 1'b1) fail("FDC D1 did not remain armed for another ready transition");
    io_read(8'h1C, rd);

    io_write(8'h1C, 8'hD2);
    force dut.U_FDC.ready = 1'b0;
    #1;
    if (dut.fdc_intrq !== 1'b1) fail("FDC D2 ready to not-ready transition did not raise INTRQ");
    io_read(8'h1C, rd);
    if (dut.fdc_intrq !== 1'b0) fail("FDC status read did not acknowledge D2 INTRQ");

    force dut.U_FDC.index = 1'b0;
    io_write(8'h1C, 8'hD4);
    force dut.U_FDC.index = 1'b1;
    #1;
    if (dut.fdc_intrq !== 1'b1) fail("FDC D4 index pulse did not raise INTRQ");
    io_read(8'h1C, rd);
    if ((rd & 8'h02) !== 8'h02) fail("FDC Type-I status did not reflect active index input");
    force dut.U_FDC.index = 1'b0;
    #1;
    force dut.U_FDC.index = 1'b1;
    #1;
    if (dut.fdc_intrq !== 1'b1) fail("FDC D4 did not remain armed for another index pulse");
    io_read(8'h1C, rd);
    io_write(8'h1C, 8'hC1);
    force dut.U_FDC.index = 1'b0;
    #1;
    force dut.U_FDC.index = 1'b1;
    #1;
    if (dut.fdc_intrq !== 1'b0) fail("FDC non-force command did not disarm D4 index interrupt");
    io_write(8'h1C, 8'hD0);
    release dut.U_FDC.ready;
    release dut.U_FDC.index;

    fdc_seek(8'h00);
    io_write(8'h1E, 8'h07);
    io_write(8'h1C, 8'hE4);     // Type-III Read Track with the valid E flag
    io_read(8'h1C, rd);
    if ((rd & 8'h03) !== 8'h01 || !dut.U_FDC.command_delay_pending)
      fail("FDC read-track did not enter E-delay");
    while (dut.U_FDC.command_delay_pending) @(posedge osc);
    #1;
    io_read(8'h1C, rd);
    if ((rd & 8'h03) !== 8'h01) fail("FDC read-track did not wait for index after E-delay");
    i = dut.U_FDC.buffer_pos;
    io_read(8'h1F, rd);
    if (dut.U_FDC.buffer_pos !== i) fail("FDC read-track exposed data before index");
    fdc_index_pulse();
    io_read(8'h1C, rd);
    if ((rd & 8'h03) !== 8'h03) fail("FDC read-track did not start at index");
    for (i = 0; i < 6250; i = i + 1) begin
      io_read(8'h1F, rd);
      case (i)
        0, 31, 54, 75, 606, 640, 6249:
          if (rd !== 8'h4e) fail("FDC read-track gap reconstruction mismatch");
        32, 43, 76, 87:
          if (rd !== 8'h00) fail("FDC read-track sync reconstruction mismatch");
        44, 45, 46, 88, 89, 90:
          if (rd !== 8'ha1) fail("FDC read-track A1 sync mismatch");
        47: if (rd !== 8'hfe) fail("FDC read-track ID address mark mismatch");
        50: if (rd !== 8'h01) fail("FDC read-track first sector ID mismatch");
        52: if (rd !== 8'hca) fail("FDC read-track first ID CRC1 mismatch");
        53: if (rd !== 8'h6f) fail("FDC read-track first ID CRC2 mismatch");
        91: if (rd !== 8'hfb) fail("FDC read-track data address mark mismatch");
        701: if (rd !== 8'hc3) fail("FDC read-track vendored sector-2 byte 0 mismatch");
        702: if (rd !== 8'h5c) fail("FDC read-track vendored sector-2 byte 1 mismatch");
        5531: if (rd !== 8'h0a) fail("FDC read-track final sector ID mismatch");
      endcase
    end
    if (dut.fdc_intrq !== 1'b1) fail("FDC read-track completion did not raise INTRQ");
    io_read(8'h1C, rd);
    if ((rd & 8'h13) !== 8'h00) fail("FDC read-track did not complete cleanly");
    if (dut.fdc_intrq !== 1'b0) fail("FDC status read did not acknowledge read-track INTRQ");
    io_read(8'h1E, rd);
    if (rd !== 8'h07) fail("FDC read-track changed sector register");

    fdc_seek(8'h00);
    io_write(8'h1E, 8'h09);
    io_write(8'h1C, 8'h92);     // Type-II multiple-record read
    for (i = 0; i < 1024; i = i + 1) begin
      io_read(8'h1F, rd);
      if (i == 0 && rd !== 8'hff) fail("FDC multi-read sector 9 first byte mismatch");
      if (i == 512 && rd !== 8'h20) fail("FDC multi-read sector 10 first byte mismatch");
    end
    if (dut.fdc_intrq !== 1'b1) fail("FDC multi-read completion did not raise INTRQ");
    io_read(8'h1C, rd);
    if ((rd & 8'h13) !== 8'h10) fail("FDC multi-read did not end with RNF after sector 10");
    if (dut.fdc_intrq !== 1'b0) fail("FDC status read did not acknowledge multi-read INTRQ");
    io_read(8'h1E, rd);
    if (rd !== 8'h0b) fail("FDC multi-read did not advance sector register to 11");

    if (writable_mode) begin
      fdc_seek(8'h08);
      io_write(8'h1E, 8'h03);
      io_write(8'h1C, 8'hA2);   // exact ROMBIOS side-aware write-sector command
      io_read(8'h1C, rd);
      if ((rd & 8'h03) !== 8'h03) fail("FDC write-sector did not assert BUSY+DRQ");
      io_write(8'h1F, 8'h5A);
      while (dut.U_FDC.write_sector_lead_pending) @(posedge osc);
      for (i = 1; i < 512; i = i + 1) io_write(8'h1F, 8'h5A ^ i[7:0]);
      if (dut.fdc_intrq !== 1'b1) fail("FDC write-sector completion did not raise INTRQ");
      io_read(8'h1C, rd);
      if ((rd & 8'h43) !== 8'h00) fail("FDC write-sector did not complete cleanly");
      if (dut.fdc_intrq !== 1'b0) fail("FDC status read did not acknowledge write-sector INTRQ");
      io_write(8'h1C, 8'h82);
      for (i = 0; i < 512; i = i + 1) begin
        io_read(8'h1F, rd);
        if (rd !== (8'h5A ^ i[7:0])) begin
          fail("FDC write-sector top-level readback mismatch");
          i = 512;
        end
      end

      io_write(8'h1E, 8'h09);
      io_write(8'h1C, 8'hB2);   // side-aware multiple-record write
      io_write(8'h1F, 8'hA0);
      while (dut.U_FDC.write_sector_lead_pending) @(posedge osc);
      for (i = 1; i < 512; i = i + 1) io_write(8'h1F, 8'hA0 ^ i[7:0]);
      io_write(8'h1F, 8'h50);
      while (dut.U_FDC.write_sector_lead_pending) @(posedge osc);
      for (i = 1; i < 512; i = i + 1) io_write(8'h1F, 8'h50 ^ i[7:0]);
      if (dut.fdc_intrq !== 1'b1) fail("FDC multi-write completion did not raise INTRQ");
      io_read(8'h1C, rd);
      if ((rd & 8'h13) !== 8'h10) fail("FDC multi-write did not end with RNF after sector 10");
      if (dut.fdc_intrq !== 1'b0) fail("FDC status read did not acknowledge multi-write INTRQ");
      io_read(8'h1E, rd);
      if (rd !== 8'h0b) fail("FDC multi-write did not advance sector register to 11");
      io_write(8'h1E, 8'h09);
      io_write(8'h1C, 8'h82);
      for (i = 0; i < 512; i = i + 1) begin
        io_read(8'h1F, rd);
        if (rd !== (8'hA0 ^ i[7:0])) begin
          fail("FDC multi-write sector 9 top-level readback mismatch");
          i = 512;
        end
      end
      io_write(8'h1E, 8'h0a);
      io_write(8'h1C, 8'h82);
      for (i = 0; i < 512; i = i + 1) begin
        io_read(8'h1F, rd);
        if (rd !== (8'h50 ^ i[7:0])) begin
          fail("FDC multi-write sector 10 top-level readback mismatch");
          i = 512;
        end
      end

      build_format_stream(8'h08, 1'b0);
      if (format_len != 6230 || format_output_len != 6250)
        fail("FDC write-track fixture length mismatch");
      fdc_seek(8'h08);
      io_write(8'h1E, 8'h0a);
      io_write(8'h1C, 8'hF4);
      io_read(8'h1C, rd);
      if ((rd & 8'h03) !== 8'h01 || !dut.U_FDC.command_delay_pending)
        fail("FDC write-track did not enter E-delay");
      while (dut.U_FDC.command_delay_pending) @(posedge osc);
      #1;
      io_read(8'h1C, rd);
      if ((rd & 8'h03) !== 8'h03) fail("FDC write-track did not request preload after E-delay");
      io_write(8'h1F, format_stream[0]);
      io_read(8'h1C, rd);
      if ((rd & 8'h03) !== 8'h01) fail("FDC write-track did not hold preloaded byte for index");
      fdc_index_pulse();
      io_read(8'h1C, rd);
      if ((rd & 8'h03) !== 8'h03) fail("FDC write-track did not start at index");
      for (i = 1; i < format_len; i = i + 1) io_write(8'h1F, format_stream[i]);
      if (dut.fdc_intrq !== 1'b1) fail("FDC write-track completion did not raise INTRQ");
      io_read(8'h1C, rd);
      if ((rd & 8'h73) !== 8'h00) fail("FDC write-track did not complete cleanly");
      if (dut.fdc_intrq !== 1'b0) fail("FDC status read did not acknowledge write-track INTRQ");
      io_read(8'h1E, rd);
      if (rd !== 8'h0a) fail("FDC write-track changed sector register");
      io_write(8'h1E, 8'h01);
      io_write(8'h1C, 8'h82);
      for (i = 0; i < 512; i = i + 1) begin
        io_read(8'h1F, rd);
        if (rd !== 8'h31) fail("FDC formatted sector 1 readback mismatch");
      end
      io_write(8'h1E, 8'h0a);
      io_write(8'h1C, 8'h82);
      for (i = 0; i < 512; i = i + 1) begin
        io_read(8'h1F, rd);
        if (rd !== 8'h3a) fail("FDC formatted sector 10 readback mismatch");
      end
    end

    if (fails == 0) begin
      $display("JUKU-TOP-PERIPH-BUS: PASS");
      $finish;
    end
    $display("JUKU-TOP-PERIPH-BUS: FAIL count=%0d", fails);
    $finish;
  end
endmodule
`default_nettype wire
