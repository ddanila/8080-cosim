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

  initial begin
    disk_mode = $test$plusargs("expect_disk");
    repeat (4) @(posedge clk);
    motor_on = 1;

    write_reg(2'd1, 8'd22);
    write_reg(2'd0, 8'h02);
    expect_status(8'h83, 8'h00, "after restore");
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
    expect_status(8'h03, 8'h00, "after side-0 drain");
    if (drq !== 1'b0 || intrq !== 1'b1) begin
      $display("FDC-1793: FAIL read completion drq=%b intrq=%b", drq, intrq);
      errors = errors + 1;
    end

    write_reg(2'd0, 8'hFD);
    expect_status(8'h43, 8'h40, "after write-track reject");
    if (drq !== 1'b0 || intrq !== 1'b1) begin
      $display("FDC-1793: FAIL write-track reject drq=%b intrq=%b", drq, intrq);
      errors = errors + 1;
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

    motor_on = 0;
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
