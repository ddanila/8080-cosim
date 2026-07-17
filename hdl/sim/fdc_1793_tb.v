`timescale 1ns/100ps
`default_nettype none

module fdc_1793_tb;
  reg clk = 0, cs_n = 1, rd_n = 1, wr_n = 1, motor_on = 0, side = 0;
  reg [1:0] A = 0;
  reg [7:0] drive = 8'h00;
  reg drive_en = 0;
  wire [7:0] D = drive_en ? drive : 8'hzz;
  wire drq, intrq;
  integer errors = 0;
  integer i;
  reg [7:0] got;
  reg disk_mode = 0;
  reg writable_mode = 0;
  reg [7:0] format_stream [0:6249];
  reg [7:0] baseline_sector [0:511];
  integer format_len = 0;
  integer format_output_len = 0;
  integer first_format_sector_end = 0;

  fdc_1793 dut(.A(A), .D(D), .cs_n(cs_n), .rd_n(rd_n), .wr_n(wr_n),
               .clk(clk), .motor_on(motor_on), .side(side), .drq(drq), .intrq(intrq));

  always #5 clk = ~clk;

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
    expect_status(8'h80, 8'h00, "initial motor-on status");

    write_reg(2'd1, 8'd22);
    write_reg(2'd0, 8'h02);
    expect_intrq(1'b1, "restore completion");
    expect_status(8'h83, 8'h00, "after restore");
    expect_intrq(1'b0, "restore status acknowledgement");
    read_reg(2'd1, got);
    if (got !== 8'd0) begin
      $display("FDC-1793: FAIL restore track=%02x", got);
      errors = errors + 1;
    end

    write_reg(2'd3, 8'd12);
    write_reg(2'd0, 8'h12);
    expect_status(8'h83, 8'h00, "after seek");
    read_reg(2'd1, got);
    if (got !== 8'd12) begin
      $display("FDC-1793: FAIL seek track=%02x", got);
      errors = errors + 1;
    end

    write_reg(2'd0, 8'h50);
    read_reg(2'd1, got);
    if (got !== 8'd13) begin
      $display("FDC-1793: FAIL step-in/update track=%02x", got);
      errors = errors + 1;
    end

    write_reg(2'd0, 8'h40);
    read_reg(2'd1, got);
    if (got !== 8'd13) begin
      $display("FDC-1793: FAIL step-in/no-update track=%02x", got);
      errors = errors + 1;
    end

    write_reg(2'd0, 8'h70);
    read_reg(2'd1, got);
    if (got !== 8'd12) begin
      $display("FDC-1793: FAIL step-out/update track=%02x", got);
      errors = errors + 1;
    end

    write_reg(2'd0, 8'h30);
    read_reg(2'd1, got);
    if (got !== 8'd11) begin
      $display("FDC-1793: FAIL step/update previous direction track=%02x", got);
      errors = errors + 1;
    end

    write_reg(2'd1, 8'd12);
    write_reg(2'd2, 8'd9);
    write_reg(2'd0, 8'hc4);  // read address with the valid E flag set
    expect_status(8'h03, 8'h03, "after read-address command");
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

    write_reg(2'd1, disk_mode ? 8'd0 : 8'd12);
    write_reg(2'd2, 8'd7);
    write_reg(2'd0, 8'he4);  // Read Track with the valid E flag
    expect_status(8'h03, 8'h03, "after read-track command");
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
    for (i = 0; i < 100; i = i + 1) read_reg(2'd3, got);
    write_reg(2'd0, 8'hd0);
    expect_intrq(1'b0, "forced read-track D0 silence");
    expect_status(8'h03, 8'h00, "after forced read-track abort");

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
    expect_intrq(1'b0, "D8 status acknowledgement");

    write_reg(2'd1, disk_mode ? 8'd0 : 8'd12);
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

    if (disk_mode && !writable_mode) begin
      write_reg(2'd0, 8'hA0);
      expect_status(8'h43, 8'h40, "read-only write-sector reject");
    end

    if (disk_mode && writable_mode) begin
      write_reg(2'd1, 8'd8);
      write_reg(2'd2, 8'd3);
      write_reg(2'd0, 8'hA2);  // exact ROMBIOS side-aware write-sector variant
      expect_status(8'h03, 8'h03, "writable write-sector command");
      for (i = 0; i < 512; i = i + 1) write_reg(2'd3, 8'h5A ^ i[7:0]);
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

      write_reg(2'd1, 8'd8);
      write_reg(2'd2, 8'd9);
      write_reg(2'd0, 8'hb2);  // side-aware multiple-record write
      for (i = 0; i < 1024; i = i + 1)
        write_reg(2'd3, ((i < 512) ? 8'ha0 : 8'h50) ^ i[7:0]);
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
      write_reg(2'd1, 8'd8);
      write_reg(2'd2, 8'd10);
      write_reg(2'd0, 8'hf4);
      expect_status(8'h03, 8'h03, "writable write-track command");
      for (i = 0; i < format_len; i = i + 1) write_reg(2'd3, format_stream[i]);
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
        write_reg(2'd0, 8'h82);
        repeat (512) begin
          read_reg(2'd3, got);
          if (got !== (8'h30 + i[7:0])) begin
            $display("FDC-1793: FAIL formatted sector %0d got=%02x", i, got);
            errors = errors + 1;
          end
        end
      end

      build_format_stream(8'd9, 1'b1);
      write_reg(2'd1, 8'd9);
      write_reg(2'd2, 8'd2);
      write_reg(2'd0, 8'h82);
      for (i = 0; i < 512; i = i + 1) read_reg(2'd3, baseline_sector[i]);
      write_reg(2'd0, 8'hf0);
      for (i = 0; i < first_format_sector_end; i = i + 1)
        write_reg(2'd3, format_stream[i]);
      write_reg(2'd0, 8'hd0);
      expect_intrq(1'b0, "forced write-track D0 silence");
      expect_status(8'h03, 8'h00, "after forced write-track abort");
      write_reg(2'd2, 8'd1);
      write_reg(2'd0, 8'h82);
      repeat (512) begin
        read_reg(2'd3, got);
        if (got !== 8'h31) begin
          $display("FDC-1793: FAIL partial format sector1 got=%02x", got);
          errors = errors + 1;
        end
      end
      write_reg(2'd2, 8'd2);
      write_reg(2'd0, 8'h82);
      for (i = 0; i < 512; i = i + 1) begin
        read_reg(2'd3, got);
        if (got !== baseline_sector[i]) begin
          $display("FDC-1793: FAIL partial format changed sector2 byte %0d got=%02x", i, got);
          errors = errors + 1;
          i = 512;
        end
      end

      write_reg(2'd1, 8'd10);
      write_reg(2'd2, 8'd1);
      write_reg(2'd0, 8'h82);
      for (i = 0; i < 512; i = i + 1) read_reg(2'd3, baseline_sector[i]);
      write_reg(2'd0, 8'hf0);
      repeat (6250) write_reg(2'd3, 8'h4e);
      expect_intrq(1'b1, "unrepresentable write-track completion");
      expect_status(8'h20, 8'h20, "unrepresentable write-track status");
      write_reg(2'd2, 8'd1);
      write_reg(2'd0, 8'h82);
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
      write_reg(2'd1, 8'd43);
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
    write_reg(2'd1, 8'd12);
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
