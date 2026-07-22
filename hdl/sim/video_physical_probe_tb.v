// Controlled-stimulus event export for source-proved physical video contributors
// in juku_top. This is a D56/D34-chain diagnostic, not a Juku waveform: the
// shared-DRAM video slot schedule and D34_SIG input function remain open.
`timescale 1ns/100ps
`default_nettype none

module video_physical_probe_tb;
  wire d42_q, d43_q, d37_pixel_n, d34_sync;
  wire d56_q_n, d56_q2, d56_q2_n;
  wire pit_hsync, pit_vsync, load_vid, slot_schedule_known;

  juku_top dut(
    .clk(1'b0), .reset_n(1'b1), .osc(1'b0),
    .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
    .kbd_kcol(4'b0), .kbd_kbit(3'b0),
    .frame_tick(1'b0), .dotclk(1'b0), .vid_out(),
    .probe_d42_q(d42_q), .probe_d43_q(d43_q),
    .probe_d37_pixel_n(d37_pixel_n), .probe_d34_sync(d34_sync),
    .probe_d56_q_n(d56_q_n), .probe_d56_q2(d56_q2),
    .probe_d56_q2_n(d56_q2_n), .probe_pit_hsync(pit_hsync),
    .probe_pit_vsync(pit_vsync), .probe_load_vid(load_vid),
    .probe_slot_schedule_known(slot_schedule_known)
  );

  integer fd;
  integer errors = 0;
  reg saw_q2 = 0;
  reg saw_q1 = 0;
  time q2_started;
  time q1_started;
  reg [1023:0] event_path;

  task record_event;
    begin
      $fwrite(fd, "%0.1f,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b\n",
              $realtime, pit_hsync, pit_vsync, d56_q_n, d56_q2, d56_q2_n,
              d34_sync, d42_q, d43_q, d37_pixel_n, load_vid,
              slot_schedule_known);
    end
  endtask

  always @(pit_hsync or pit_vsync or d56_q_n or d56_q2 or d56_q2_n or
           d34_sync or d42_q or d43_q or d37_pixel_n or load_vid or
           slot_schedule_known) begin
    #0 record_event;
  end

  always @(posedge d56_q2) begin
    q2_started = $time;
    saw_q2 = 1;
  end
  always @(negedge d56_q2) if (saw_q2 && $time - q2_started != 5040) begin
    $display("VIDEO-PHYSICAL-PROBE: FAIL D56 section2 width=%0t", $time-q2_started);
    errors = errors + 1;
  end
  always @(negedge d56_q_n) begin
    q1_started = $time;
    saw_q1 = 1;
  end
  always @(posedge d56_q_n) if (saw_q1 && $time - q1_started != 223000) begin
    $display("VIDEO-PHYSICAL-PROBE: FAIL D56 section1 width=%0t", $time-q1_started);
    errors = errors + 1;
  end
  always @(d56_q_n or d56_q2 or d34_sync) begin
    #1;
    if (d34_sync !== (d56_q2 ^ d56_q_n)) begin
      $display("VIDEO-PHYSICAL-PROBE: FAIL D34 sync XOR truth");
      errors = errors + 1;
    end
  end

  initial begin
    if (!$value$plusargs("events=%s", event_path))
      event_path = "/tmp/video-physical-events.csv";
    fd = $fopen(event_path, "w");
    $fwrite(fd, "time_ns,pit_hsync,pit_vsync,d56_q_n,d56_q2,d56_q2_n,d34_sync,d42_q,d43_q,d37_pixel_n,load_vid,slot_schedule_known\n");

    force dut.pit_hsync_dsl = 1'b0;
    force dut.pit_vert_sync_dsl = 1'b0;
    #100 force dut.pit_hsync_dsl = 1'b1;
    #10  force dut.pit_hsync_dsl = 1'b0;
    #9890 force dut.pit_vert_sync_dsl = 1'b1;
    #10   force dut.pit_vert_sync_dsl = 1'b0;
    #230000;

    if (!saw_q2 || !saw_q1) begin
      $display("VIDEO-PHYSICAL-PROBE: FAIL missing D56 pulse");
      errors = errors + 1;
    end
    if (slot_schedule_known !== 1'b0) begin
      $display("VIDEO-PHYSICAL-PROBE: FAIL slot boundary not explicit");
      errors = errors + 1;
    end
    $fclose(fd);
    if (errors == 0)
      $display("VIDEO-PHYSICAL-PROBE: PASS D56=223000/5040ns D34_SYNC=XOR slot_schedule_known=0");
    else
      $display("VIDEO-PHYSICAL-PROBE: FAIL errors=%0d", errors);
    $finish;
  end
endmodule
`default_nettype wire
