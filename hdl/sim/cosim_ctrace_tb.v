// Deep VALUE-level guard, cosim-referenced. Locksteps juku_top's memory-read stream against a
// trace of the C emulator's (cosim) reads and flags the first read whose address or captured byte
// disagrees. cosim is the AUTHORITATIVE reference (a straightforward 8080 + flat memory model);
// juku_top must read what cosim reads.
//
// This supersedes the older juku_top-vs-juku_struct comparison (hdl/sim/cosim_diff_tb.v): comparing
// two independently-timed Verilog models made the result depend on sub-cycle event ordering (it
// diverged differently across Icarus versions -- "passed on Linux, failed on Mac"). Comparing
// against cosim removes the second model and pins each divergence to a real juku_top-vs-reference
// difference. See docs/cosim-runtime-reference.md.
//
// The trace is "addr data" hex lines, one per CPU memory read, emitted by cosim with JUKU_RDTRACE.
// The C read order is the real 8080 bus order (low byte before high) so the streams align 1:1.
//
//   sync/cosim_ctrace_check.sh   builds cosim, generates the trace, and runs this guard.
`timescale 1ns/100ps
`default_nettype none
module cosim_ctrace_tb;
  reg osc=0, phi1=0, phi2=0;
  juku_top dtop(.clk(1'b0), .reset_n(1'b1), .osc(osc),
    .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0), .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(1'b0));
  initial begin force dtop.ready=1'b1; force dtop.reset_sys=1; #2000 force dtop.reset_sys=0; end
  initial forever begin
    phi1=1; phi2=0; force dtop.phi1=1; force dtop.phi2=0; osc=0; #10; osc=1; #10;
    phi1=0; phi2=1; force dtop.phi1=0; force dtop.phi2=1; osc=0; #10; osc=1; #10;
    phi2=0; force dtop.phi2=0;
  end
  integer fd, nrd=0, timecap=1600000000, code, ea, ed;
  reg [4095:0] tracefile;
  reg done=0;
  initial begin
    if (!$value$plusargs("timecap=%d", timecap)) ;
    if (!$value$plusargs("trace=%s", tracefile)) tracefile="reads.txt";
    fd = $fopen(tracefile, "r");
    if (fd==0) begin $display("CTRACE: cannot open trace file"); $finish; end
  end
  // Each CPU memory read (negedge dbin while memr_n low) consumes the next trace entry.
  always @(negedge dtop.dbin) if (~dtop.memr_n && !done) begin
    nrd = nrd + 1;
    code = $fscanf(fd, "%h %h\n", ea, ed);
    if (code != 2) begin
      $display("CTRACE-END: trace exhausted after %0d reads; juku_top matched cosim throughout", nrd);
      done=1; #1 $finish;
    end else if (dtop.BA !== ea[15:0]) begin
      done=1;
      $display("CTRACE-DIVERGE read=%0d addr: juku_top BA=%04h  cosim addr=%04h data=%02h (juku bus=%02h di=%02h)",
               nrd, dtop.BA, ea[15:0], ed[7:0], dtop.D, dtop.U_CPU.u.core.di);
      #100 $finish;
    end else if (dtop.U_CPU.u.core.di !== ed[7:0]) begin
      done=1;
      $display("CTRACE-DIVERGE read=%0d data: BA=%04h  cosim data=%02h  juku_top di=%02h (bus=%02h)",
               nrd, dtop.BA, ed[7:0], dtop.U_CPU.u.core.di, dtop.D);
      #100 $finish;
    end
  end
  initial begin #(timecap);
    if (!done) $display("CTRACE-OK: %0d reads compared within window; juku_top == cosim", nrd);
    $finish;
  end
endmodule
`default_nettype wire
