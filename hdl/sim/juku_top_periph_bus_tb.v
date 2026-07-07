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
  reg [7:0] rd;
  reg [15:0] drive_ba = 16'h0000;
  reg [7:0] drive_db = 8'hff;

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
               .kbd_kcol(4'd0), .kbd_kbit(3'd0), .frame_tick(1'b0));

  initial forever begin osc = 0; #10; osc = 1; #10; end

  task fail(input [1023:0] msg); begin
    $display("JUKU-TOP-PERIPH-BUS: FAIL %0s", msg);
    fails = fails + 1;
  end endtask

  function [15:0] io_addr(input [7:0] port); begin
    io_addr = {port, port};
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
    drive_db = data;
    force dut.BA = drive_ba;
    force dut.DB = drive_db;
    force dut.iord_n = 1'b1;
    force dut.iowr_n = 1'b0;
    #1;
    if (port[4:2] == 3'd0 && dut.cs_pic_n) fail("PIC chip-select did not assert on write");
    if (port[4:2] == 3'd1 && dut.cs_ppi0_n) fail("PPI0 chip-select did not assert on write");
    if (port[4:2] == 3'd7 && dut.cs_fdc_n) fail("FDC chip-select did not assert on write");
    @(negedge osc);
    bus_idle();
  end endtask

  task io_read(input [7:0] port, output [7:0] data); begin
    @(negedge osc);
    drive_ba = io_addr(port);
    force dut.BA = drive_ba;
    release dut.DB;
    force dut.iowr_n = 1'b1;
    force dut.iord_n = 1'b0;
    #1;
    if (port[4:2] == 3'd0 && dut.cs_pic_n) fail("PIC chip-select did not assert on read");
    if (port[4:2] == 3'd1 && dut.cs_ppi0_n) fail("PPI0 chip-select did not assert on read");
    if (port[4:2] == 3'd7 && dut.cs_fdc_n) fail("FDC chip-select did not assert on read");
    @(posedge osc);
    #1;
    data = dut.DB;
    @(negedge osc);
    bus_idle();
  end endtask

  initial begin
    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    force dut.phi1 = 1'b0;
    force dut.phi2 = 1'b0;
    bus_idle();
    #200;
    force dut.reset_sys = 1'b0;
    #200;

    io_write(8'h00, 8'h16);     // PIC ICW1
    io_write(8'h01, 8'hFE);     // PIC ICW2
    io_write(8'h01, 8'hDF);     // unmask IR5, matching ROMBIOS frame path
    io_read(8'h01, rd);
    if (rd !== 8'hDF) fail("PIC register readback mismatch");

    io_write(8'h06, 8'h04);     // PPI0 Port C: motor on, mode 0
    if (dut.ppi0_pc[2] !== 1'b1) fail("PPI0 PC2 motor-on bit did not latch");

    io_read(8'h1C, rd);
    if ((rd & 8'h80) == 8'h00) fail("FDC reset status should report NOT READY before commands");

    io_write(8'h1F, 8'h02);     // FDC data register: seek target / sector byte
    io_write(8'h1D, 8'h00);     // FDC track register
    io_write(8'h1E, 8'h02);     // FDC sector register
    io_write(8'h1C, 8'h10);     // FDC seek: track <= data
    io_read(8'h1D, rd);
    if (rd !== 8'h02) fail("FDC seek did not update track register through top-level bus");

    io_write(8'h1D, 8'h00);     // read vendored JUKU1 sector 2 on track 0
    io_write(8'h1C, 8'h80);     // FDC read-sector command
    io_read(8'h1C, rd);
    if ((rd & 8'h03) !== 8'h03) fail("FDC read-sector did not assert BUSY+DRQ");
    io_read(8'h1F, rd);
    if (rd !== 8'hc3) fail("FDC first vendored sector byte mismatch");

    if (fails == 0) begin
      $display("JUKU-TOP-PERIPH-BUS: PASS");
      $finish;
    end
    $display("JUKU-TOP-PERIPH-BUS: FAIL count=%0d", fails);
    $finish;
  end
endmodule
`default_nettype wire
