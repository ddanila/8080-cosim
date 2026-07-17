`timescale 1ns/100ps
`default_nettype none

module fdc_1793_tb;
  reg clk = 0, cs_n = 1, rd_n = 1, wr_n = 1, motor_on = 0, side = 0;
  reg ready = 0, index = 0, hlt = 1, tr00 = 0;
  reg [1:0] A = 0;
  reg [7:0] drive = 8'h00;
  reg drive_en = 0;
  wire [7:0] D = drive_en ? drive : 8'hzz;
  wire drq, intrq, step, dirc;
  integer errors = 0;
  integer i;
  reg [7:0] got;
  reg [7:0] missed_read_next;
  reg disk_mode = 0;
  reg writable_mode = 0;
  reg [7:0] format_stream [0:6249];
  reg [7:0] baseline_sector [0:511];
  integer format_len = 0;
  integer format_output_len = 0;
  integer first_format_sector_end = 0;
  integer expected_rate = 0;
  integer step_pulses = 0;
  integer step_pulses_before = 0;

  fdc_1793 dut(.A(A), .D(D), .cs_n(cs_n), .rd_n(rd_n), .wr_n(wr_n),
               .clk(clk), .motor_on(motor_on), .side(side), .ready(ready), .index(index),
               .hlt(hlt), .tr00(tr00), .wprt(1'b0),
               .drq(drq), .intrq(intrq), .step(step), .dirc(dirc));

  always #5 clk = ~clk;
  always @(posedge step) step_pulses = step_pulses + 1;

  task write_reg(input [1:0] regno, input [7:0] value); begin
    @(negedge clk);
    A = regno; drive = value; drive_en = 1; cs_n = 0; wr_n = 0;
    @(negedge clk);
    wr_n = 1; cs_n = 1; drive_en = 0;
  end endtask

  task read_reg(input [1:0] regno, output [7:0] value); begin
    @(negedge clk);
    A = regno; cs_n = 0; rd_n = 0;
    @(posedge clk);
    #1 value = D;
    @(negedge clk);
    rd_n = 1; cs_n = 1;
  end endtask

  task seek_track(input [7:0] track_id); begin
    write_reg(2'd3, track_id);
    write_reg(2'd0, 8'h10);
    while (dut.status[0]) @(negedge clk);
    #1;
  end endtask

  task pulse_index; begin
    index = 0;
    #1 index = 1;
    #1 index = 0;
    #1;
  end endtask

  task expect_status(input [7:0] mask, input [7:0] value, input [160*8:1] label);
    reg [7:0] status;
  begin
    read_reg(2'd0, status);
    if ((status & mask) !== value) begin
      $display("FDC-1793: FAIL %0s status=%02x mask=%02x expected=%02x", label, status, mask, value);
      errors = errors + 1;
    end
  end endtask

  task expect_intrq(input value, input [160*8:1] label); begin
    if (intrq !== value) begin
      $display("FDC-1793: FAIL %0s intrq=%b expected=%b", label, intrq, value);
      errors = errors + 1;
    end
  end endtask

  function [7:0] want_byte(input integer pos, input [7:0] track, input side_bit, input [7:0] sector);
  begin
    if (pos == 0) want_byte = track;
    else if (pos == 1) want_byte = {7'b0, side_bit};
    else if (pos == 2) want_byte = sector;
    else want_byte = track + ({7'b0, side_bit} << 5) + sector + pos[7:0];
  end endfunction

  function [7:0] want_juku1_sector2(input integer pos);
  begin
    case (pos)
      0: want_juku1_sector2 = 8'hc3;
      1: want_juku1_sector2 = 8'h5c;
      2: want_juku1_sector2 = 8'hb7;
      3: want_juku1_sector2 = 8'hc3;
      4: want_juku1_sector2 = 8'h58;
      5: want_juku1_sector2 = 8'hb7;
      6: want_juku1_sector2 = 8'h7f;
      7: want_juku1_sector2 = 8'h00;
      8, 9, 10, 11, 12, 13, 14, 15: want_juku1_sector2 = 8'h20;
      default: want_juku1_sector2 = 8'hxx;
    endcase
  end endfunction

  function [7:0] want_address_byte(input integer pos);
  begin
    case (pos)
      0: want_address_byte = 8'd12;
      1: want_address_byte = 8'd0;
      2: want_address_byte = 8'd1;
      3: want_address_byte = 8'd2;
      4: want_address_byte = 8'hbd;
      5: want_address_byte = 8'hb3;
      default: want_address_byte = 8'hxx;
    endcase
  end endfunction

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
    first_format_sector_end = 0;
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
      if (sector_id == 1) first_format_sector_end = format_len;
      for (byte_index = 0; byte_index < 35; byte_index = byte_index + 1) put_format_byte(8'h4e);
    end
    while (format_output_len < 6250) put_format_byte(8'h4e);
  end endtask

  initial begin
    disk_mode = $test$plusargs("expect_disk");
    writable_mode = $test$plusargs("expect_writable");
    repeat (4) @(posedge clk);
    expect_status(8'h80, 8'h80, "initial motor-off status");
    motor_on = 1;
    ready = 1;
    expect_status(8'h80, 8'h00, "initial motor-on status");

    write_reg(2'd1, 8'd22);
    write_reg(2'd0, 8'h02);
    expect_intrq(1'b1, "restore completion");
    expect_status(8'he7, (disk_mode && !writable_mode) ? 8'h44 : 8'h04, "after restore");
    expect_intrq(1'b0, "restore status acknowledgement");
    read_reg(2'd1, got);
    if (got !== 8'd0) begin
      $display("FDC-1793: FAIL restore track=%02x", got);
      errors = errors + 1;
    end

    tr00 = 1;
    expect_status(8'h04, 8'h00, "inactive TR00 status");
    step_pulses_before = step_pulses;
    write_reg(2'd0, 8'h00);
    while (dut.status[0]) @(negedge clk);
    #1;
    if (step_pulses !== step_pulses_before + 255) begin
      $display("FDC-1793: FAIL stuck-TR00 restore steps=%0d expected=255",
               step_pulses - step_pulses_before);
      errors = errors + 1;
    end
    expect_intrq(1'b1, "restore 255-step completion");
    expect_status(8'h15, 8'h10, "restore stuck-TR00 seek error");

    seek_track(8'd5);
    step_pulses_before = step_pulses;
    write_reg(2'd0, 8'h00);
    if (dut.physical_track !== 8'd4 || dut.type_i_steps_remaining !== 254) begin
      $display("FDC-1793: FAIL restore did not issue first TR00-seeking step");
      errors = errors + 1;
    end
    while (dut.type_i_ticks > 1) @(posedge clk);
    tr00 = 0;
    @(negedge clk); #1;
    if (step_pulses !== step_pulses_before + 1 || dut.track !== 0 || dut.physical_track !== 0) begin
      $display("FDC-1793: FAIL TR00 assertion restore steps=%0d track=%02x physical=%02x",
               step_pulses - step_pulses_before, dut.track, dut.physical_track);
      errors = errors + 1;
    end
    expect_intrq(1'b1, "restore TR00 assertion completion");
    expect_status(8'h15, 8'h04, "restore TR00 assertion status");

    write_reg(2'd0, 8'h08);
    expect_status(8'h24, 8'h24, "restore head-load status");
    for (i = 0; i < 7; i = i + 1) begin
      index = 0; #1; index = 1; #1;
    end
    write_reg(2'd0, 8'hd4);  // arming an idle event does not leave idle
    for (i = 0; i < 7; i = i + 1) begin
      index = 0; #1; index = 1; #1;
    end
    if (!dut.head_loaded || dut.idle_index_pulses !== 14) begin
      $display("FDC-1793: FAIL head unloaded before 15 idle index pulses");
      errors = errors + 1;
    end
    write_reg(2'd2, 8'd1);
    write_reg(2'd0, 8'h80);  // a new busy command resets the idle count
    for (i = 0; i < 15; i = i + 1) begin
      index = 0; #1; index = 1; #1;
    end
    if (!dut.head_loaded || dut.idle_index_pulses !== 0) begin
      $display("FDC-1793: FAIL busy index pulses affected head unload state");
      errors = errors + 1;
    end
    write_reg(2'd0, 8'hd0);
    for (i = 0; i < 14; i = i + 1) begin
      index = 0; #1; index = 1; #1;
    end
    if (!dut.head_loaded) begin
      $display("FDC-1793: FAIL head unloaded before 15 post-command idle index pulses");
      errors = errors + 1;
    end
    index = 0; #1; index = 1; #1;
    if (dut.head_loaded || dut.idle_index_pulses !== 0) begin
      $display("FDC-1793: FAIL head did not unload on 15th idle index pulse");
      errors = errors + 1;
    end
    index = 0; #1;
    write_reg(2'd0, 8'h08);
    write_reg(2'd0, 8'h00);
    expect_status(8'h24, 8'h04, "restore head-unload status");

    for (i = 0; i < 4; i = i + 1) begin
      write_reg(2'd0, i[7:0]);  // zero-step restore exposes r1:r0
      case (i)
        0: expected_rate = 6000;
        1: expected_rate = 12000;
        2: expected_rate = 20000;
        default: expected_rate = 30000;
      endcase
      if (dut.type_i_rate_ticks !== expected_rate) begin
        $display("FDC-1793: FAIL rate %0d mapped to %0d ticks expected %0d",
                 i, dut.type_i_rate_ticks, expected_rate);
        errors = errors + 1;
      end
    end

    write_reg(2'd3, 8'd12);
    write_reg(2'd0, 8'h12);
    if (!dut.status[0]) begin
      $display("FDC-1793: FAIL seek timing did not assert BUSY");
      errors = errors + 1;
    end
    while (dut.status[0]) @(negedge clk);
    #1;
    expect_status(8'h83, 8'h00, "after seek");
    read_reg(2'd1, got);
    if (got !== 8'd12) begin
      $display("FDC-1793: FAIL seek track=%02x", got);
      errors = errors + 1;
    end

    hlt = 0;
    write_reg(2'd0, 8'h14);  // zero-step seek, verify after settle and HLT
    while (dut.type_i_ticks > 1) @(posedge clk);
    @(negedge clk); #1;
    if ((dut.effective_status & 8'h31) !== 8'h01 || !dut.type_i_hlt_pending || intrq) begin
      $display("FDC-1793: FAIL Type-I verify did not wait for HLT status=%02x", dut.status);
      errors = errors + 1;
    end
    hlt = 1; #1;
    expect_intrq(1'b1, "Type-I verify HLT completion");
    expect_status(8'h31, 8'h20, "matching Type-I verify after HLT");

    step_pulses_before = step_pulses;
    write_reg(2'd0, 8'h44);
    if (!dut.status[0]) begin
      $display("FDC-1793: FAIL step/verify timing did not assert BUSY");
      errors = errors + 1;
    end
    if (dut.physical_track !== 8'd13 || dut.type_i_settling ||
        step_pulses !== step_pulses_before + 1 || dut.dirc_r !== 1'b1) begin
      $display("FDC-1793: FAIL step pulse/motion was not issued before rate delay");
      errors = errors + 1;
    end
    while (dut.type_i_ticks > 1) @(posedge clk);
    #1;
    if (dut.physical_track !== 8'd13 || dut.type_i_settling || !dut.status[0]) begin
      $display("FDC-1793: FAIL 3ms step delay completed before rate boundary");
      errors = errors + 1;
    end
    @(negedge clk); #1;
    if (dut.physical_track !== 8'd13 || !dut.type_i_settling || !dut.status[0]) begin
      $display("FDC-1793: FAIL step did not enter 15ms verify settle");
      errors = errors + 1;
    end
    while (dut.type_i_ticks > 1) @(posedge clk);
    #1;
    if (!dut.status[0] || dut.status[4]) begin
      $display("FDC-1793: FAIL verify completed before settle boundary ticks=%0d status=%02x",
               dut.type_i_ticks, dut.status);
      errors = errors + 1;
    end
    @(negedge clk); #1;
    read_reg(2'd1, got);
    if (dut.physical_track !== 8'd13 || got !== 8'd12) begin
      $display("FDC-1793: FAIL verified no-update step physical=%02x track=%02x",
               dut.physical_track, got);
      errors = errors + 1;
    end
    expect_intrq(1'b1, "Type-I valid-ID mismatch completion");
    expect_status(8'h31, 8'h30, "Type-I verify seek error");
    seek_track(8'd14);
    read_reg(2'd1, got);
    if (dut.physical_track !== 8'd15 || got !== 8'd14) begin
      $display("FDC-1793: FAIL seek lost physical/register offset physical=%02x track=%02x",
               dut.physical_track, got);
      errors = errors + 1;
    end
    write_reg(2'd2, 8'd1);
    write_reg(2'd0, 8'h80);
    if ((dut.status & 8'h13) !== 8'h01 || drq || intrq) begin
      $display("FDC-1793: FAIL missing-ID search did not begin BUSY-only status=%02x", dut.status);
      errors = errors + 1;
    end
    repeat (3) pulse_index();
    if ((dut.status & 8'h13) !== 8'h01 || intrq) begin
      $display("FDC-1793: FAIL missing-ID search ended before fourth revolution status=%02x", dut.status);
      errors = errors + 1;
    end
    pulse_index();
    expect_intrq(1'b1, "missing-ID fourth-revolution completion");
    expect_status(8'h13, 8'h10, "missing-ID fourth-revolution RNF");

    seek_track(8'd80);
    write_reg(2'd0, 8'h14);
    while (!dut.type_i_verify_pending) @(negedge clk);
    #1;
    expect_status(8'h11, 8'h01, "Type-I missing-ID verify search");
    repeat (3) pulse_index();
    expect_intrq(1'b0, "Type-I missing-ID before fourth revolution");
    pulse_index();
    expect_intrq(1'b1, "Type-I missing-ID fourth-revolution completion");
    expect_status(8'h11, 8'h10, "Type-I missing-ID seek error");
    write_reg(2'd0, 8'h00);
    while (dut.status[0]) @(negedge clk);
    #1;
    write_reg(2'd3, 8'd4);
    write_reg(2'd0, 8'h10);
    if (dut.track !== 8'd1 || dut.physical_track !== 8'd1 || !dut.status[0]) begin
      $display("FDC-1793: FAIL timed seek did not issue first step immediately");
      errors = errors + 1;
    end
    write_reg(2'd0, 8'hd0);
    if (dut.track !== 8'd1 || dut.physical_track !== 8'd1 || dut.status[0] || intrq) begin
      $display("FDC-1793: FAIL D0 did not silently retain partial Type-I motion");
      errors = errors + 1;
    end
    write_reg(2'd0, 8'h00);
    while (dut.status[0]) @(negedge clk);
    #1;
    seek_track(8'd12);
    write_reg(2'd2, 8'd4);
    write_reg(2'd0, 8'h80);
    missed_read_next = disk_mode ? dut.sector_buf[1] : want_byte(1, 8'd12, 1'b0, 8'd4);
    while (dut.drq_ticks < 63) @(posedge clk);
    #1;
    if (dut.buffer_pos !== 0 || (dut.status & 8'h04) !== 0) begin
      $display("FDC-1793: FAIL read deadline fired early pos=%0d status=%02x",
               dut.buffer_pos, dut.status);
      errors = errors + 1;
    end
    @(posedge clk); #1;
    if (dut.buffer_pos !== 1) begin
      $display("FDC-1793: FAIL read deadline did not discard one byte pos=%0d", dut.buffer_pos);
      errors = errors + 1;
    end
    expect_status(8'h07, 8'h07, "read lost-data deadline");
    read_reg(2'd3, got);
    if (got !== missed_read_next) begin
      $display("FDC-1793: FAIL read lost-data overwrite got=%02x want=%02x",
               got, missed_read_next);
      errors = errors + 1;
    end
    write_reg(2'd0, 8'hd0);
    expect_status(8'h07, 8'h04, "read lost-data abort preserves status");

    seek_track(8'd12);

    write_reg(2'd0, 8'h50);
    while (dut.status[0]) @(negedge clk);
    #1;
    read_reg(2'd1, got);
    if (got !== 8'd13) begin
      $display("FDC-1793: FAIL step-in/update track=%02x", got);
      errors = errors + 1;
    end

    write_reg(2'd0, 8'h40);
    while (dut.status[0]) @(negedge clk);
    #1;
    read_reg(2'd1, got);
    if (got !== 8'd13) begin
      $display("FDC-1793: FAIL step-in/no-update track=%02x", got);
      errors = errors + 1;
    end

    write_reg(2'd0, 8'h70);
    while (dut.status[0]) @(negedge clk);
    #1;
    read_reg(2'd1, got);
    if (got !== 8'd12) begin
      $display("FDC-1793: FAIL step-out/update track=%02x", got);
      errors = errors + 1;
    end

    write_reg(2'd0, 8'h30);
    while (dut.status[0]) @(negedge clk);
    #1;
    read_reg(2'd1, got);
    if (got !== 8'd11) begin
      $display("FDC-1793: FAIL step/update previous direction track=%02x", got);
      errors = errors + 1;
    end

    write_reg(2'd0, 8'h00);
    while (dut.status[0]) @(negedge clk);
    #1;
    seek_track(8'd12);
    hlt = 0;
    write_reg(2'd0, 8'hc0);
    if ((dut.status & 8'h03) !== 8'h01 || !dut.command_hlt_pending || intrq) begin
      $display("FDC-1793: FAIL Type-III command did not wait for HLT status=%02x", dut.status);
      errors = errors + 1;
    end
    hlt = 1; #1;
    expect_status(8'h03, 8'h03, "read-address starts after HLT");
    write_reg(2'd0, 8'hd0);

    hlt = 0;
    write_reg(2'd2, 8'd9);
    write_reg(2'd0, 8'hc4);  // read address with the valid E flag set
    if ((dut.status & 8'h03) !== 8'h01 || !dut.command_delay_pending) begin
      $display("FDC-1793: FAIL read-address E-delay did not begin BUSY-only");
      errors = errors + 1;
    end
    while (dut.command_delay_ticks > 1) @(posedge clk);
    #1;
    if ((dut.status & 8'h03) !== 8'h01 || !dut.command_delay_pending) begin
      $display("FDC-1793: FAIL read-address completed before 15ms E-delay boundary");
      errors = errors + 1;
    end
    @(negedge clk); #1;
    if ((dut.status & 8'h03) !== 8'h01 || !dut.command_hlt_pending) begin
      $display("FDC-1793: FAIL E-delayed Type-III command skipped HLT wait");
      errors = errors + 1;
    end
    hlt = 1; #1;
    expect_status(8'h03, 8'h03, "after read-address E-delay and HLT");
    for (i = 0; i < 6; i = i + 1) begin
      read_reg(2'd3, got);
      if (got !== want_address_byte(i)) begin
        $display("FDC-1793: FAIL read-address byte %0d got=%02x want=%02x",
                 i, got, want_address_byte(i));
        errors = errors + 1;
      end
      if (i < 5 && dut.sector !== 8'd9) begin
        $display("FDC-1793: FAIL read-address changed sector early at byte %0d to %02x", i, dut.sector);
        errors = errors + 1;
      end
    end
    expect_intrq(1'b1, "read-address completion");
    expect_status(8'h03, 8'h00, "after read-address drain");
    expect_intrq(1'b0, "read-address status acknowledgement");
    read_reg(2'd2, got);
    if (got !== 8'd12) begin
      $display("FDC-1793: FAIL read-address sector-register result=%02x", got);
      errors = errors + 1;
    end

    seek_track(disk_mode ? 8'd0 : 8'd12);
    write_reg(2'd2, 8'd7);
    write_reg(2'd0, 8'he4);  // Read Track with the valid E flag
    while (dut.command_delay_pending) @(negedge clk);
    #1;
    expect_status(8'h03, 8'h01, "read-track waiting for first index");
    expected_rate = dut.buffer_pos;
    read_reg(2'd3, got);
    if (dut.buffer_pos !== expected_rate) begin
      $display("FDC-1793: FAIL read-track exposed data before first index");
      errors = errors + 1;
    end
    pulse_index();
    expect_status(8'h03, 8'h03, "read-track started at first index");
    for (i = 0; i < 6250; i = i + 1) begin
      read_reg(2'd3, got);
      case (i)
        0, 31, 54, 75, 606, 640, 6249:
          if (got !== 8'h4e) begin
            $display("FDC-1793: FAIL read-track gap byte %0d got=%02x", i, got);
            errors = errors + 1;
          end
        32, 43, 76, 87:
          if (got !== 8'h00) begin
            $display("FDC-1793: FAIL read-track sync byte %0d got=%02x", i, got);
            errors = errors + 1;
          end
        44, 45, 46, 88, 89, 90:
          if (got !== 8'ha1) begin
            $display("FDC-1793: FAIL read-track A1 byte %0d got=%02x", i, got);
            errors = errors + 1;
          end
        47: if (got !== 8'hfe) begin
          $display("FDC-1793: FAIL read-track IDAM got=%02x", got); errors = errors + 1;
        end
        48: if (got !== (disk_mode ? 8'd0 : 8'd12)) begin
          $display("FDC-1793: FAIL read-track track ID got=%02x", got); errors = errors + 1;
        end
        49: if (got !== 8'h00) begin
          $display("FDC-1793: FAIL read-track side ID got=%02x", got); errors = errors + 1;
        end
        50: if (got !== 8'h01) begin
          $display("FDC-1793: FAIL read-track sector ID got=%02x", got); errors = errors + 1;
        end
        51: if (got !== 8'h02) begin
          $display("FDC-1793: FAIL read-track length ID got=%02x", got); errors = errors + 1;
        end
        52: if (got !== (disk_mode ? 8'hca : 8'h85)) begin
          $display("FDC-1793: FAIL read-track ID CRC1 got=%02x", got); errors = errors + 1;
        end
        53: if (got !== (disk_mode ? 8'h6f : 8'h5d)) begin
          $display("FDC-1793: FAIL read-track ID CRC2 got=%02x", got); errors = errors + 1;
        end
        91: if (got !== 8'hfb) begin
          $display("FDC-1793: FAIL read-track DAM got=%02x", got); errors = errors + 1;
        end
        92: if (!disk_mode && got !== 8'h0c) begin
          $display("FDC-1793: FAIL synthetic read-track data0 got=%02x", got); errors = errors + 1;
        end
        604: if (!disk_mode && got !== 8'hae) begin
          $display("FDC-1793: FAIL synthetic read-track data CRC1 got=%02x", got); errors = errors + 1;
        end
        605: if (!disk_mode && got !== 8'hcc) begin
          $display("FDC-1793: FAIL synthetic read-track data CRC2 got=%02x", got); errors = errors + 1;
        end
        701: if (disk_mode && got !== 8'hc3) begin
          $display("FDC-1793: FAIL vendored read-track sector2 data0 got=%02x", got); errors = errors + 1;
        end
        702: if (disk_mode && got !== 8'h5c) begin
          $display("FDC-1793: FAIL vendored read-track sector2 data1 got=%02x", got); errors = errors + 1;
        end
        5531: if (got !== 8'h0a) begin
          $display("FDC-1793: FAIL read-track final sector ID got=%02x", got); errors = errors + 1;
        end
      endcase
    end
    expect_intrq(1'b1, "read-track completion");
    expect_status(8'h13, 8'h00, "after read-track drain");
    expect_intrq(1'b0, "read-track status acknowledgement");
    read_reg(2'd2, got);
    if (got !== 8'd7) begin
      $display("FDC-1793: FAIL read-track changed sector=%02x", got);
      errors = errors + 1;
    end

    write_reg(2'd0, 8'he0);
    pulse_index();
    for (i = 0; i < 100; i = i + 1) read_reg(2'd3, got);
    write_reg(2'd0, 8'hd0);
    expect_intrq(1'b0, "forced read-track D0 silence");
    expect_status(8'h03, 8'h00, "after forced read-track abort");

    write_reg(2'd0, 8'hc4);
    repeat (100) @(negedge clk);
    write_reg(2'd0, 8'hd0);
    repeat (30000) @(negedge clk);
    expect_intrq(1'b0, "D0 during E-delay remains silent");
    expect_status(8'h03, 8'h00, "D0 cancels E-delay");

    write_reg(2'd2, 8'd7);
    write_reg(2'd0, 8'hc0);
    read_reg(2'd3, got);
    read_reg(2'd3, got);
    write_reg(2'd0, 8'hd0);
    expect_intrq(1'b0, "D0 silent force interrupt");
    expect_status(8'h03, 8'h00, "after forced read-address abort");
    read_reg(2'd2, got);
    if (got !== 8'd7) begin
      $display("FDC-1793: FAIL aborted read-address changed sector=%02x", got);
      errors = errors + 1;
    end
    write_reg(2'd0, 8'hc1);  // reserved low bit is not Read Address
    expect_status(8'h03, 8'h01, "reserved type-III opcode");
    write_reg(2'd0, 8'hd8);
    expect_intrq(1'b1, "D8 immediate force interrupt");
    expect_status(8'h03, 8'h00, "after immediate force interrupt");
    expect_intrq(1'b1, "D8 remains asserted after status read");
    write_reg(2'd0, 8'hd0);
    expect_intrq(1'b0, "D0 disarms D8 immediate interrupt");

    ready = 0;
    write_reg(2'd0, 8'hd1);
    expect_intrq(1'b0, "D1 arms without immediate interrupt");
    ready = 1; #1;
    expect_intrq(1'b1, "D1 not-ready to ready interrupt");
    expect_status(8'h00, 8'h00, "D1 status acknowledgement");
    expect_intrq(1'b0, "D1 status read clears interrupt");
    ready = 0; #1; ready = 1; #1;
    expect_intrq(1'b1, "D1 remains armed for another ready transition");
    read_reg(2'd0, got);

    write_reg(2'd0, 8'hd2);
    ready = 0; #1;
    expect_intrq(1'b1, "D2 ready to not-ready interrupt");
    read_reg(2'd0, got);
    expect_intrq(1'b0, "D2 status read clears interrupt");
    ready = 1; #1; ready = 0; #1;
    expect_intrq(1'b1, "D2 remains armed for another not-ready transition");
    read_reg(2'd0, got);

    write_reg(2'd2, 8'd1);
    write_reg(2'd0, 8'h80);
    expect_intrq(1'b1, "READY-low read-sector completion");
    expect_status(8'h83, 8'h80, "READY-low read-sector status");
    expect_intrq(1'b0, "READY-low read-sector acknowledgement");
    write_reg(2'd0, 8'hc0);
    expect_intrq(1'b1, "READY-low read-address completion");
    expect_status(8'h83, 8'h80, "READY-low read-address status");

    seek_track(8'd1);
    expect_intrq(1'b1, "READY-low Type-I completion");
    expect_status(8'h81, 8'h80, "READY-low Type-I completion status");
    read_reg(2'd1, got);
    if (got !== 8'd1) begin
      $display("FDC-1793: FAIL READY-low Type-I seek track=%02x", got);
      errors = errors + 1;
    end
    ready = 1; #1;
    expect_status(8'h80, 8'h00, "READY-high status recovery");

    index = 0;
    write_reg(2'd0, 8'hd4);
    expect_intrq(1'b0, "D4 arms without immediate interrupt");
    index = 1; #1;
    expect_intrq(1'b1, "D4 index interrupt");
    expect_status(8'h02, 8'h02, "D4 Type-I index status");
    index = 0; #1; index = 1; #1;
    expect_intrq(1'b1, "D4 remains armed for another index pulse");
    read_reg(2'd0, got);
    write_reg(2'd0, 8'hc1);
    index = 0; #1; index = 1; #1;
    expect_intrq(1'b0, "non-force command disarms D4 index interrupt");
    write_reg(2'd0, 8'hd0);

    seek_track(disk_mode ? 8'd0 : 8'd12);
    write_reg(2'd2, disk_mode ? 8'd2 : 8'd4);
    write_reg(2'd0, 8'h80);
    expect_status(8'h03, 8'h03, disk_mode ? "after raw-disk read command" : "after side-0 read command");
    if (drq !== 1'b1 || intrq !== 1'b0) begin
      $display("FDC-1793: FAIL read command drq=%b intrq=%b", drq, intrq);
      errors = errors + 1;
    end
    for (i = 0; i < 512; i = i + 1) begin
      read_reg(2'd3, got);
      if (!disk_mode && got !== want_byte(i, 8'd12, 1'b0, 8'd4)) begin
        $display("FDC-1793: FAIL side0 byte %0d got=%02x want=%02x", i, got, want_byte(i, 8'd12, 1'b0, 8'd4));
        errors = errors + 1;
        i = 512;
      end else if (disk_mode && i < 16 && got !== want_juku1_sector2(i)) begin
        $display("FDC-1793: FAIL JUKU1 sector2 byte %0d got=%02x want=%02x", i, got, want_juku1_sector2(i));
        errors = errors + 1;
        i = 512;
      end
    end
    if (drq !== 1'b0 || intrq !== 1'b1) begin
      $display("FDC-1793: FAIL read completion drq=%b intrq=%b", drq, intrq);
      errors = errors + 1;
    end
    expect_status(8'h03, 8'h00, "after side-0 drain");
    expect_intrq(1'b0, "read-sector status acknowledgement");

    write_reg(2'd0, 8'h8a);  // C=1/S=1 mismatches the selected side-0 ID
    if ((dut.status & 8'h13) !== 8'h01 || drq || intrq) begin
      $display("FDC-1793: FAIL side-compare mismatch did not begin BUSY-only status=%02x", dut.status);
      errors = errors + 1;
    end
    repeat (4) pulse_index();
    if ((dut.status & 8'h13) !== 8'h01 || intrq) begin
      $display("FDC-1793: FAIL side-compare mismatch ended before fifth index status=%02x", dut.status);
      errors = errors + 1;
    end
    pulse_index();
    expect_intrq(1'b1, "side-compare mismatch fifth-index completion");
    expect_status(8'h13, 8'h10, "side-compare mismatch fifth-index RNF");

    if (disk_mode && !writable_mode) begin
      write_reg(2'd0, 8'hA0);
      expect_status(8'h43, 8'h40, "read-only write-sector reject");
    end

    if (disk_mode && writable_mode) begin
      seek_track(8'd8);
      write_reg(2'd2, 8'd3);

      write_reg(2'd2, 8'd11);
      write_reg(2'd0, 8'ha2);
      if ((dut.status & 8'h13) !== 8'h01 || drq || intrq) begin
        $display("FDC-1793: FAIL write missing-ID search did not begin BUSY-only status=%02x", dut.status);
        errors = errors + 1;
      end
      repeat (3) pulse_index();
      if ((dut.status & 8'h13) !== 8'h01 || intrq) begin
        $display("FDC-1793: FAIL write missing-ID search ended before fourth revolution status=%02x", dut.status);
        errors = errors + 1;
      end
      pulse_index();
      expect_intrq(1'b1, "write missing-ID fourth-revolution completion");
      expect_status(8'h13, 8'h10, "write missing-ID fourth-revolution RNF");
      write_reg(2'd2, 8'd3);

      write_reg(2'd0, 8'h82);
      for (i = 0; i < 512; i = i + 1) read_reg(2'd3, baseline_sector[i]);
      write_reg(2'd0, 8'ha2);
      while (dut.write_sector_lead_ticks > 1) @(negedge clk);
      #1;
      expect_intrq(1'b0, "write-sector lead-in before boundary");
      if ((dut.status & 8'h07) !== 8'h03) begin
        $display("FDC-1793: FAIL write-sector lead-in before boundary status=%02x", dut.status);
        errors = errors + 1;
      end
      if (dut.buffer_pos != 0) begin
        $display("FDC-1793: FAIL write-sector lead-in changed buffer before boundary");
        errors = errors + 1;
      end
      @(negedge clk); #1;
      expect_intrq(1'b1, "first write-byte timeout completion");
      expect_status(8'h07, 8'h04, "first write-byte timeout status");
      write_reg(2'd0, 8'h82);
      for (i = 0; i < 512; i = i + 1) begin
        read_reg(2'd3, got);
        if (got !== baseline_sector[i]) begin
          $display("FDC-1793: FAIL first write timeout changed byte %0d", i);
          errors = errors + 1;
          i = 512;
        end
      end

      write_reg(2'd0, 8'ha2);
      write_reg(2'd3, 8'hA5);
      while (dut.write_sector_lead_pending) @(negedge clk);
      while (dut.buffer_pos < 2) @(posedge clk);
      #1;
      for (i = 2; i < 512; i = i + 1) write_reg(2'd3, 8'hC0 ^ i[7:0]);
      expect_status(8'h07, 8'h04, "subsequent write-byte zero substitution");
      write_reg(2'd0, 8'h82);
      for (i = 0; i < 512; i = i + 1) begin
        read_reg(2'd3, got);
        if ((i == 0 && got !== 8'hA5) || (i == 1 && got !== 8'h00) ||
            (i >= 2 && got !== (8'hC0 ^ i[7:0]))) begin
          $display("FDC-1793: FAIL write lost-data byte %0d got=%02x", i, got);
          errors = errors + 1;
          i = 512;
        end
      end

      write_reg(2'd2, 8'd3);
      write_reg(2'd0, 8'ha2);  // C=1/S=0 matches the selected side-0 ID
      expect_status(8'h03, 8'h03, "writable write-sector command");
      write_reg(2'd3, 8'h5A);
      while (dut.write_sector_lead_pending) @(negedge clk);
      for (i = 1; i < 512; i = i + 1) write_reg(2'd3, 8'h5A ^ i[7:0]);
      if (drq !== 1'b0 || intrq !== 1'b1) begin
        $display("FDC-1793: FAIL write completion drq=%b intrq=%b", drq, intrq);
        errors = errors + 1;
      end
      expect_status(8'h43, 8'h00, "after writable sector fill");
      expect_intrq(1'b0, "write-sector status acknowledgement");
      write_reg(2'd0, 8'h82);
      for (i = 0; i < 512; i = i + 1) begin
        read_reg(2'd3, got);
        if (got !== (8'h5A ^ i[7:0])) begin
          $display("FDC-1793: FAIL write-sector readback byte %0d got=%02x want=%02x",
                   i, got, (8'h5A ^ i[7:0]));
          errors = errors + 1;
          i = 512;
        end
      end

      seek_track(8'd8);
      write_reg(2'd2, 8'd9);
      write_reg(2'd0, 8'hb2);  // C=1/S=0 multiple-record write
      write_reg(2'd3, 8'ha0);
      while (dut.write_sector_lead_pending) @(negedge clk);
      for (i = 1; i < 512; i = i + 1) write_reg(2'd3, 8'ha0 ^ i[7:0]);
      write_reg(2'd3, 8'h50);
      while (dut.write_sector_lead_pending) @(negedge clk);
      for (i = 1; i < 512; i = i + 1) write_reg(2'd3, 8'h50 ^ i[7:0]);
      expect_intrq(1'b1, "multi-write end-of-track completion");
      expect_status(8'h13, 8'h10, "multi-write end of track");
      read_reg(2'd2, got);
      if (got !== 8'd11) begin
        $display("FDC-1793: FAIL multi-write final sector=%02x", got);
        errors = errors + 1;
      end
      write_reg(2'd2, 8'd9);
      write_reg(2'd0, 8'h82);
      for (i = 0; i < 512; i = i + 1) begin
        read_reg(2'd3, got);
        if (got !== (8'ha0 ^ i[7:0])) begin
          $display("FDC-1793: FAIL multi-write sector9 byte %0d got=%02x", i, got);
          errors = errors + 1;
          i = 512;
        end
      end
      write_reg(2'd2, 8'd10);
      write_reg(2'd0, 8'h82);
      for (i = 0; i < 512; i = i + 1) begin
        read_reg(2'd3, got);
        if (got !== (8'h50 ^ i[7:0])) begin
          $display("FDC-1793: FAIL multi-write sector10 byte %0d got=%02x", i, got);
          errors = errors + 1;
          i = 512;
        end
      end

      side = 1;
      build_format_stream(8'd8, 1'b1);
      if (format_len != 6230 || format_output_len != 6250 || first_format_sector_end == 0) begin
        $display("FDC-1793: FAIL write-track fixture input=%0d output=%0d first=%0d",
                 format_len, format_output_len, first_format_sector_end);
        errors = errors + 1;
      end
      seek_track(8'd8);
      write_reg(2'd2, 8'd10);
      write_reg(2'd0, 8'hf4);
      while (dut.command_delay_pending) @(negedge clk);
      #1;
      repeat (100) @(negedge clk);
      expect_status(8'h07, 8'h03, "write-track preload window before index");
      pulse_index();
      expect_intrq(1'b1, "missing write-track preload at index completion");
      expect_status(8'h07, 8'h04, "missing write-track preload at index status");

      write_reg(2'd0, 8'hf4);
      if ((dut.status & 8'h03) !== 8'h01 || !dut.command_delay_pending) begin
        $display("FDC-1793: FAIL write-track E-delay did not begin BUSY-only");
        errors = errors + 1;
      end
      while (dut.command_delay_pending) @(negedge clk);
      #1;
      expect_status(8'h03, 8'h03, "writable write-track preload request");
      write_reg(2'd3, format_stream[0]);
      expect_status(8'h03, 8'h01, "write-track first-byte preload");
      pulse_index();
      expect_status(8'h03, 8'h03, "write-track starts at index");
      for (i = 1; i < format_len; i = i + 1) write_reg(2'd3, format_stream[i]);
      expect_intrq(1'b1, "write-track completion");
      expect_status(8'h73, 8'h00, "after writable track format");
      expect_intrq(1'b0, "write-track status acknowledgement");
      read_reg(2'd2, got);
      if (got !== 8'd10) begin
        $display("FDC-1793: FAIL write-track changed sector=%02x", got);
        errors = errors + 1;
      end
      for (i = 1; i <= 10; i = i + 1) begin
        write_reg(2'd2, i[7:0]);
        write_reg(2'd0, 8'h8a);
        repeat (512) begin
          read_reg(2'd3, got);
          if (got !== (8'h30 + i[7:0])) begin
            $display("FDC-1793: FAIL formatted sector %0d got=%02x", i, got);
            errors = errors + 1;
          end
        end
      end

      build_format_stream(8'd9, 1'b1);
      seek_track(8'd9);
      write_reg(2'd2, 8'd2);
      write_reg(2'd0, 8'h8a);
      for (i = 0; i < 512; i = i + 1) read_reg(2'd3, baseline_sector[i]);
      write_reg(2'd0, 8'hf0);
      write_reg(2'd3, format_stream[0]);
      pulse_index();
      for (i = 1; i < first_format_sector_end; i = i + 1)
        write_reg(2'd3, format_stream[i]);
      write_reg(2'd0, 8'hd0);
      expect_intrq(1'b0, "forced write-track D0 silence");
      expect_status(8'h03, 8'h00, "after forced write-track abort");
      write_reg(2'd2, 8'd1);
      write_reg(2'd0, 8'h8a);
      repeat (512) begin
        read_reg(2'd3, got);
        if (got !== 8'h31) begin
          $display("FDC-1793: FAIL partial format sector1 got=%02x", got);
          errors = errors + 1;
        end
      end
      write_reg(2'd2, 8'd2);
      write_reg(2'd0, 8'h8a);
      for (i = 0; i < 512; i = i + 1) begin
        read_reg(2'd3, got);
        if (got !== baseline_sector[i]) begin
          $display("FDC-1793: FAIL partial format changed sector2 byte %0d got=%02x", i, got);
          errors = errors + 1;
          i = 512;
        end
      end

      seek_track(8'd10);
      write_reg(2'd2, 8'd1);
      write_reg(2'd0, 8'h8a);
      for (i = 0; i < 512; i = i + 1) read_reg(2'd3, baseline_sector[i]);
      write_reg(2'd0, 8'hf0);
      write_reg(2'd3, 8'h4e);
      pulse_index();
      repeat (6249) write_reg(2'd3, 8'h4e);
      expect_intrq(1'b1, "unrepresentable write-track completion");
      expect_status(8'h20, 8'h20, "unrepresentable write-track status");
      write_reg(2'd2, 8'd1);
      write_reg(2'd0, 8'h8a);
      for (i = 0; i < 512; i = i + 1) begin
        read_reg(2'd3, got);
        if (got !== baseline_sector[i]) begin
          $display("FDC-1793: FAIL malformed format changed sector1 byte %0d got=%02x", i, got);
          errors = errors + 1;
          i = 512;
        end
      end
      side = 0;
    end

    if (!writable_mode) begin
      write_reg(2'd0, 8'hFD);
      if (drq !== 1'b0 || intrq !== 1'b1) begin
        $display("FDC-1793: FAIL write-track reject drq=%b intrq=%b", drq, intrq);
        errors = errors + 1;
      end
      expect_status(8'h43, 8'h40, "after write-track reject");
      expect_intrq(1'b0, "write-track status acknowledgement");
    end

    if (!disk_mode) begin
      side = 1;
      seek_track(8'd43);
      write_reg(2'd2, 8'd7);
      write_reg(2'd0, 8'h80);
      for (i = 0; i < 512; i = i + 1) begin
        read_reg(2'd3, got);
        if (got !== want_byte(i, 8'd43, 1'b1, 8'd7)) begin
          $display("FDC-1793: FAIL side1 byte %0d got=%02x want=%02x", i, got, want_byte(i, 8'd43, 1'b1, 8'd7));
          errors = errors + 1;
          i = 512;
        end
      end
    end

    side = 0;
    seek_track(8'd12);
    write_reg(2'd2, 8'd9);
    write_reg(2'd0, 8'h92);  // multiple-record read
    for (i = 0; i < 1024; i = i + 1) begin
      read_reg(2'd3, got);
      if (!disk_mode && got !== want_byte(i & 511, 8'd12, 1'b0,
                                          (i < 512) ? 8'd9 : 8'd10)) begin
        $display("FDC-1793: FAIL multi-read byte %0d got=%02x", i, got);
        errors = errors + 1;
        i = 1024;
      end
    end
    expect_intrq(1'b1, "multi-read end-of-track completion");
    expect_status(8'h53, 8'h10, "multi-read end of track");
    read_reg(2'd2, got);
    if (got !== 8'd11) begin
      $display("FDC-1793: FAIL multi-read final sector=%02x", got);
      errors = errors + 1;
    end

    write_reg(2'd2, 8'd8);
    write_reg(2'd0, 8'h90);
    for (i = 0; i < 529; i = i + 1) read_reg(2'd3, got);
    write_reg(2'd0, 8'hd0);
    expect_intrq(1'b0, "forced multi-read D0 silence");
    expect_status(8'h03, 8'h00, "forced multi-read abort");
    read_reg(2'd2, got);
    if (got !== 8'd9) begin
      $display("FDC-1793: FAIL forced multi-read current sector=%02x", got);
      errors = errors + 1;
    end

    motor_on = 0;
    write_reg(2'd0, 8'hc0);
    expect_status(8'h80, 8'h80, "motor off read address");
    write_reg(2'd0, 8'he0);
    expect_status(8'h80, 8'h80, "motor off read track");
    write_reg(2'd0, 8'hf0);
    expect_status(8'h80, 8'h80, "motor off write track");
    write_reg(2'd0, 8'h80);
    expect_status(8'h80, 8'h80, "motor off read");

    if (errors == 0) begin
      $display("FDC-1793: PASS");
      $finish;
    end
    $display("FDC-1793: FAIL errors=%0d", errors);
    $finish;
  end
endmodule

`default_nettype wire
