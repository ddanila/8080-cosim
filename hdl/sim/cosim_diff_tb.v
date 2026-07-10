// Co-simulation diff guard: lockstep juku_top (the LVS-checked structural model) against
// juku_struct (the behavioral reference oracle) on ONE clock + ROM, and flag the first read
// where their data buses disagree. This is a VALUE-level equivalence check -- stronger than LVS
// (connectivity only) and than boot_check (which samples only 0xD300 + the 0xD800+ framebuffer).
// NO-DIVERGE within the window => the two independently-written models execute bit-identically.
// This is exactly how the DRAM CAS-timing write bug at 0xD441 was found (invisible to both other
// guards). Run via sync/cosim_check.sh. Bound the window with +timecap=<ns>.
//
//   iverilog -g2012 -o /tmp/cosim hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
//            hdl/sim/juku_struct.v hdl/sim/cosim_diff_tb.v && vvp /tmp/cosim +timecap=1600000000
`timescale 1ns/100ps
`default_nettype none

module cosim_diff_tb;
  reg osc=0, phi1=0, phi2=0, reset=1;

  // juku_top: the real structural netlist (Φ1/Φ2/reset/ready forced; osc = sim sampling clock)
  juku_top   dtop(.clk(1'b0), .reset_n(1'b1), .osc(osc),
    .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0), .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(1'b0));
  // juku_struct: the behavioral oracle (Φ1/Φ2/reset/ready as ports)
  juku_struct dstr(.osc(osc), .phi1(phi1), .phi2(phi2), .reset(reset), .ready(1'b1),
    .frame_tick(1'b0), .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0), .kbd_kcol(4'b0), .kbd_kbit(3'b0));

  initial begin force dtop.ready=1'b1; force dtop.reset_sys=1; #2000 force dtop.reset_sys=0; end
  initial #2000 reset=0;
  // one lockstep clock drives both (Φ1 then Φ2; osc rises mid-phase)
  initial forever begin
    phi1=1; phi2=0; force dtop.phi1=1; force dtop.phi2=0; osc=0; #10; osc=1; #10;
    phi1=0; phi2=1; force dtop.phi1=0; force dtop.phi2=1; osc=0; #10; osc=1; #10;
    phi2=0; force dtop.phi2=0;
  end

  integer nrd=0, timecap=1600000000, progress_step, progress_mark; reg done=0;
  initial if ($value$plusargs("timecap=%d", timecap)) ;
  // Sparse milestones make multi-hour default runs observable. Twenty writes
  // are negligible beside millions of lockstep reads.
  initial begin
    #1;
    progress_step = timecap / 20;
    if (progress_step < 1) progress_step = 1;
    for (progress_mark = 1; progress_mark < 20; progress_mark = progress_mark + 1) begin
      #(progress_step);
      if (!done)
        $display("COSIM-PROGRESS: %0d%% simulated (%0d/%0d ns), %0d reads compared",
                 progress_mark * 5, progress_mark * progress_step, timecap, nrd);
    end
  end
  // compare the captured read byte each memory read; first mismatch = the divergence
  always @(negedge dtop.dbin) if (~dtop.memr_n && !done) begin
    nrd = nrd + 1;
    if (dtop.D !== dstr.D) begin done=1;
      $display("DIVERGE at read#%0d: BA=%04h  juku_top.D=%02h  juku_struct.D=%02h",
               nrd, dtop.BA, dtop.D, dstr.D);
      #100 $finish;
    end
  end
  initial begin #(timecap);
    if (!done) $display("NO-DIVERGE: %0d reads compared, juku_top == juku_struct bit-identical", nrd);
    $finish;
  end
endmodule
`default_nettype wire
