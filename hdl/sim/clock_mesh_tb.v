// Clock-mesh unit test: PROVE the discrete clock subsystem is functionally faithful when its
// divider actually RUNS -- the thing the boot harness can't show (it ties D59.xin=0 to freeze the
// divider so ststb_n collapses to ~sync for the byte-identical boot). Here we drive the crystal
// input with a real clock and check:
//   1. D40 (СТ16) divides: d40_q counts 0..15..0 on each osc_clk edge.
//   2. The traced feedback gate D39 computes d39_y = ~(Q1 & Q0) (pins 12<-Q1, 13<-Q0).
//   3. D38 turns a running mesh + CPU SYNC into a *SYNC-qualified strobe*: ststb_n falls (would
//      latch the 8238 status byte) inside every SYNC window -- i.e. wiring the real feedback nets
//      does NOT lose the strobe, it just narrows it. This is exactly what the abstract-clock model
//      approximated as ststb_n=~sync, now shown to hold with the real divider in the loop.
// This validates the functional models added in devices.v (ln1_osc/ct16_ctr/ln1_dual) that the LVS
// reads only as -lib blackboxes; the running-divider behaviour is invisible to LVS and to the boot.
`timescale 1ns/100ps
`default_nettype none

module clock_mesh_tb;
  reg clk = 0;                 // crystal drive (D59 xin)
  reg sync = 0;                // CPU SYNC (stand-in for vm80a pin_sync)
  wire osc_clk, d39_y, clkg_d33, d33_o6, ststb_n;
  wire [3:0] d40_q;

  // mirror juku_top's mesh wiring exactly
  ln1_osc   U_D59 (.xin(clk), .osc(osc_clk));
  ct16_ctr  U_D40 (.clk(osc_clk), .r_n(1'b1), .ep(1'b1), .et(1'b1), .pe_n(1'b1), .d(4'b0),
                   .q(d40_q), .co());
  la3_gate  U_D39 (.a(d40_q[1]), .b(d40_q[0]), .y(d39_y));            // pin12<-Q1, pin13<-Q0
  ln1_dual  U_D33 (.i9(1'b0), .i5(d40_q[2]), .o8(clkg_d33), .o6(d33_o6));
  la1_gate  U_D38 (.i0(clkg_d33), .i1(sync), .i2(1'b1), .i3(d39_y), .y(ststb_n));  // pin10<-d39_y, pin13 tied hi

  always #5 clk = ~clk;        // 10 ns crystal period -> divider runs

  integer errors = 0, seen_counts = 0, sync_windows = 0, strobed_windows = 0;
  reg [15:0] seen_mask = 0;
  reg strobe_this_window = 0;

  // (1)+(2): every divider edge, record the count reached and check D39's algebra
  always @(posedge osc_clk) begin
    seen_mask[d40_q] <= 1'b1;                                        // mark this counter value seen
    if (d39_y !== ~(d40_q[1] & d40_q[0])) begin
      $display("[mesh] FAIL D39 algebra at q=%0d: d39_y=%b", d40_q, d39_y); errors = errors + 1;
    end
    if (clkg_d33 !== 1'b1) begin
      $display("[mesh] FAIL clkg_d33 should be ~i2=1, got %b", clkg_d33); errors = errors + 1;
    end
  end

  // (3): drive SYNC windows (each a few divider counts wide) and confirm ststb_n falls inside each
  integer w;
  initial begin
    #23;                                                            // let the divider start
    for (w = 0; w < 8; w = w + 1) begin
      @(posedge clk); sync = 1; strobe_this_window = 0;
      repeat (6) begin @(posedge clk); if (!ststb_n) strobe_this_window = 1; end
      sync = 0;
      sync_windows = sync_windows + 1;
      if (strobe_this_window) strobed_windows = strobed_windows + 1;
      else begin $display("[mesh] FAIL SYNC window %0d: ststb_n never fell", w); errors = errors + 1; end
      repeat (3) @(posedge clk);                                    // gap between machine cycles
    end
    // did the divider actually cycle through many values?
    seen_counts = 0;
    begin : cnt integer b; for (b=0;b<16;b=b+1) seen_counts = seen_counts + seen_mask[b[3:0]]; end

    $display("[mesh] divider values seen=%0d/16, SYNC windows=%0d strobed=%0d, errors=%0d",
             seen_counts, sync_windows, strobed_windows, errors);
    if (errors == 0 && strobed_windows == sync_windows && sync_windows == 8 && seen_counts == 16)
      $display("[mesh] PASS: divider runs (all 16 states), D39 feedback correct, ststb_n is a valid SYNC-qualified strobe");
    else
      $display("[mesh] FAIL");
    $finish;
  end

  initial begin #100000; $display("[mesh] TIMEOUT"); $finish; end
endmodule
`default_nettype wire
