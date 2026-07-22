// Execute the exact ekta37 D54/D55 programming sequence through juku_top and
// measure the autonomous physical PIT -> D56 -> D34_SYNC timing chain. The
// shared-DRAM slot schedule and D34_SIG remain outside this test.
`timescale 1ns/1ps
`default_nettype none

module video_pit_timing_tb;
  reg clk = 1'b0;
  wire hchain, vchain, hsync_dsl, vsync_dsl, hor_rtr, vert_rtr;
  wire d56_q_n, d56_q2, d56_q2_n, d34_sync;

  juku_top dut(
    .clk(clk), .reset_n(1'b1), .osc(1'b0),
    .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
    .kbd_kcol(4'b0), .kbd_kbit(3'b0),
    .frame_tick(1'b0), .dotclk(1'b0), .vid_out(),
    .probe_d34_sync(d34_sync),
    .probe_d56_q_n(d56_q_n), .probe_d56_q2(d56_q2),
    .probe_d56_q2_n(d56_q2_n),
    .probe_pit_hchain(hchain), .probe_pit_vchain(vchain),
    .probe_pit_hsync(hsync_dsl), .probe_pit_vsync(vsync_dsl),
    .probe_hor_rtr(hor_rtr), .probe_vert_rtr(vert_rtr)
  );

  // 16 MHz crystal input; D40.Q3 is therefore the source-proved 1 MHz PIT rail.
  always #31.25 clk = ~clk;

  integer errors = 0;
  integer line_count = 0;
  integer line_at_field = 0;
  integer vertical_ticks = 0;
  integer field_count = 0;
  reg armed = 1'b0;
  reg saw_hchain_low = 1'b0;
  reg saw_vchain_low = 1'b0;
  reg vertical_window = 1'b0;
  time last_line = 0;
  time last_field = 0;
  time current_line = 0;
  time q2_started = 0;
  time q1_started = 0;

  task fail;
    input [511:0] label;
    begin
      $display("VIDEO-PIT-TIMING: FAIL %0s time=%0t lines=%0d vticks=%0d",
               label, $time, line_count, vertical_ticks);
      errors = errors + 1;
    end
  endtask

  task pit_write;
    input integer which;
    input [1:0] address;
    input [7:0] value;
    begin
      // Icarus evaluates a procedural force RHS only once, so use literal
      // branches rather than forcing task arguments onto the internal nets.
      case (address)
        2'd0: force dut.BA = 16'h0000;
        2'd1: force dut.BA = 16'h0001;
        2'd2: force dut.BA = 16'h0002;
        default: force dut.BA = 16'h0003;
      endcase
      case (value)
        8'h00: force dut.DB = 8'h00;
        8'h01: force dut.DB = 8'h01;
        8'h08: force dut.DB = 8'h08;
        8'h15: force dut.DB = 8'h15;
        8'h24: force dut.DB = 8'h24;
        8'h25: force dut.DB = 8'h25;
        8'h34: force dut.DB = 8'h34;
        8'h39: force dut.DB = 8'h39;
        8'h53: force dut.DB = 8'h53;
        8'h64: force dut.DB = 8'h64;
        8'h72: force dut.DB = 8'h72;
        8'h73: force dut.DB = 8'h73;
        default: force dut.DB = 8'h93;
      endcase
      if (which == 0) force dut.cs_pit0_n = 1'b0;
      else            force dut.cs_pit1_n = 1'b0;
      #20 force dut.iowr_n = 1'b0;
      #20 force dut.iowr_n = 1'b1;
      if (which == 0) force dut.cs_pit0_n = 1'b1;
      else            force dut.cs_pit1_n = 1'b1;
      release dut.DB;
      release dut.BA;
      #20;
    end
  endtask

  always @(negedge hchain) if (armed) saw_hchain_low = 1'b1;
  always @(posedge hchain) if (armed && saw_hchain_low) begin
    line_count = line_count + 1;
    current_line = $time;
    if (last_line != 0 && $time - last_line != 64000)
      fail("D54 mode-2 line period is not 64 us");
    last_line = $time;
  end

  always @(posedge hor_rtr) if (armed && current_line != 0)
    if ($time - current_line != 24000)
      fail("D54 horizontal blank interval is not 24 us");

  always @(posedge hsync_dsl) if (armed && current_line != 0)
    if ($time - current_line != 8000)
      fail("D54 horizontal front porch is not 8 us");

  always @(posedge d56_q2) if (armed) q2_started = $time;
  always @(negedge d56_q2) if (armed && q2_started != 0)
    if ($time - q2_started != 5040)
      fail("D56 horizontal sync pulse is not 5.04 us");

  always @(negedge vchain) if (armed) saw_vchain_low = 1'b1;
  always @(posedge vchain) if (armed && saw_vchain_low) begin
    field_count = field_count + 1;
    if (last_field != 0) begin
      if (line_count - line_at_field != 313)
        fail("D55 field period is not 313 lines");
      if ($time - last_field != 20032000)
        fail("D55 field period is not 20.032 ms");
    end
    last_field = $time;
    line_at_field = line_count;
    vertical_ticks = 0;
    vertical_window = 1'b1;
  end

  always @(posedge d56_q2_n) if (armed && vertical_window)
    vertical_ticks = vertical_ticks + 1;

  always @(posedge vsync_dsl) if (armed && vertical_window) begin
    if (vertical_ticks != 25)
      fail("D55 vertical front porch is not 25 lines");
    q1_started = $time;
  end

  always @(posedge vert_rtr) if (armed && vertical_window)
    if (vertical_ticks != 72)
      fail("D55 vertical blank interval is not 72 lines");

  always @(posedge d56_q_n) if (armed && q1_started != 0)
    if ($time - q1_started != 223000)
      fail("D56 vertical sync pulse is not 223 us");

  always @(d56_q_n or d56_q2 or d34_sync) if (armed) begin
    #1;
    if (d34_sync !== (d56_q2 ^ d56_q_n))
      fail("D34_SYNC is not D56.Q2 XOR D56.Q_N");
  end

  initial begin
    // Hold the CPU inactive and perform the byte-for-byte ekta37 writes through
    // the real juku_top PIT bus pins. Chip selects return high after each write.
    force dut.reset_sys = 1'b1;
    force dut.iowr_n = 1'b1;
    force dut.iord_n = 1'b1;
    force dut.cs_pit0_n = 1'b1;
    force dut.cs_pit1_n = 1'b1;
    #2000;

    pit_write(0, 2'd3, 8'h15);
    pit_write(0, 2'd3, 8'h53);
    pit_write(0, 2'd3, 8'h93);
    pit_write(1, 2'd3, 8'h73);
    pit_write(1, 2'd3, 8'h93);
    pit_write(1, 2'd3, 8'h34);
    pit_write(1, 2'd0, 8'h39);
    pit_write(1, 2'd0, 8'h01);
    pit_write(0, 2'd0, 8'h64);
    pit_write(0, 2'd1, 8'h24);
    pit_write(0, 2'd2, 8'h08);
    pit_write(1, 2'd1, 8'h72);
    pit_write(1, 2'd1, 8'h00);
    pit_write(1, 2'd2, 8'h25);

    $display("[VIDEO-PIT] programmed D54=%0d/%0d/%0d modes=%0d/%0d/%0d D55=%0d/%0d/%0d modes=%0d/%0d/%0d",
             dut.U_PIT0.reload[0], dut.U_PIT0.reload[1], dut.U_PIT0.reload[2],
             dut.U_PIT0.mode[0], dut.U_PIT0.mode[1], dut.U_PIT0.mode[2],
             dut.U_PIT1.reload[0], dut.U_PIT1.reload[1], dut.U_PIT1.reload[2],
             dut.U_PIT1.mode[0], dut.U_PIT1.mode[1], dut.U_PIT1.mode[2]);

    armed = 1'b1;
    wait (field_count >= 2);
    #300000;
    if (line_count < 626) fail("insufficient autonomous line events");
    if (errors == 0)
      $display("VIDEO-PIT-TIMING: PASS h=15625Hz line=64000ns frame=313lines/20032000ns v=49.920128Hz active=320x241 D56=5040/223000ns");
    else
      $display("VIDEO-PIT-TIMING: FAIL errors=%0d", errors);
    $finish;
  end

  initial begin
    #45000000;
    $display("[VIDEO-PIT] timeout clk=%b osc_clk=%b pull=%b D40=%h clk1m=%b D54.count0=%0d running=%b out=%b",
             clk, dut.osc_clk, dut.d40_ctrl_pull, dut.d40_q, dut.clk1m, dut.U_PIT0.count[0],
             dut.U_PIT0.running[0], dut.U_PIT0.out_r[0]);
    fail("timeout");
    $finish;
  end
endmodule
`default_nettype wire
