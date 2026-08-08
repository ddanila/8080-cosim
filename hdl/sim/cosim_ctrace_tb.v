// Deep CPU-bus guard, cosim-referenced. Locksteps juku_top's memory reads,
// memory writes, I/O reads, I/O writes, and interrupt-acknowledge bytes against
// the independent C emulator. This is a functional event-order/value contract,
// not a claim that cosim supplies physical sub-cycle timing.
//
// This supersedes the older juku_top-vs-juku_struct comparison (hdl/sim/cosim_diff_tb.v): comparing
// two independently-timed Verilog models made the result depend on sub-cycle event ordering (it
// diverged differently across Icarus versions -- "passed on Linux, failed on Mac"). Comparing
// against cosim removes the second model and pins each divergence to a real juku_top-vs-reference
// difference. See docs/cosim-runtime-reference.md.
//
// The trace is "TYPE addr data", where TYPE is MR/MW/IR/IW/IA, emitted with
// JUKU_BUS_TRACE. The C access order follows the real 8080 low-byte/high-byte
// order, so multi-byte CPU transactions align with the physical bus sequence.
//
//   sync/cosim_check.sh   builds cosim, generates the trace, and runs this guard.
`timescale 1ns/100ps
`default_nettype none
module cosim_ctrace_tb;
  reg osc=0, phi1=0, phi2=0, frame_tick=0;
  juku_top dtop(.clk(1'b0), .reset_n(1'b1), .osc(osc),
    .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0), .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(frame_tick));
  initial begin force dtop.ready=1'b1; force dtop.reset_sys=1; #2000 force dtop.reset_sys=0; end
  initial forever begin
    phi1=1; phi2=0; force dtop.phi1=1; force dtop.phi2=0; osc=0; #10; osc=1; #10;
    phi1=0; phi2=1; force dtop.phi1=0; force dtop.phi2=1; osc=0; #10; osc=1; #10;
    phi2=0; force dtop.phi2=0;
  end
  integer fd, nevent=0, timecap=1600000000, code, ea, ed, irq_after=0;
  reg [15:0] ekind;
  reg [4095:0] tracefile;
  reg done=0;
  reg irq_started=0;
  initial begin
    if (!$value$plusargs("timecap=%d", timecap)) ;
    if (!$value$plusargs("irq_after=%d", irq_after)) ;
    if (!$value$plusargs("trace=%s", tracefile)) tracefile="bus-events.txt";
    fd = $fopen(tracefile, "r");
    if (fd==0) begin $display("BTRACE: cannot open trace file"); $finish; end
  end

  task check_event(input [15:0] actual_kind, input [15:0] actual_addr,
                   input [7:0] actual_data); begin
    if (!done) begin
      nevent = nevent + 1;
      code = $fscanf(fd, "%s %h %h\n", ekind, ea, ed);
      if (code != 3) begin
        $display("BTRACE-END: trace exhausted after %0d events; juku_top matched cosim throughout", nevent-1);
        done=1; #1 $finish;
      end else if (actual_kind !== ekind) begin
        done=1;
        $display("BTRACE-DIVERGE event=%0d type: juku_top=%0s cosim=%0s addr=%04h data=%02h",
                 nevent, actual_kind, ekind, actual_addr, actual_data);
        #100 $finish;
      end else if (actual_kind !== "IA" && actual_addr !== ea[15:0]) begin
        done=1;
        $display("BTRACE-DIVERGE event=%0d addr: type=%0s juku_top=%04h cosim=%04h data=%02h",
                 nevent, actual_kind, actual_addr, ea[15:0], actual_data);
        #100 $finish;
      end else if (actual_data !== ed[7:0]) begin
        done=1;
        $display("BTRACE-DIVERGE event=%0d data: type=%0s addr=%04h juku_top=%02h cosim=%02h bus=%02h",
                 nevent, actual_kind, actual_addr, actual_data, ed[7:0], dtop.DB);
        #100 $finish;
      end else if (irq_after > 0 && nevent == irq_after && !irq_started) begin
        // The focused guard asserts this one operand transfer before the
        // reference instruction ends, allowing the sim-only frame synchronizer
        // to settle while preserving that instruction's final bus read. The
        // 8259 adjunct then supplies CD/low/high on real vm80a INTA cycles.
        irq_started=1;
        frame_tick=1;
        fork begin #80 frame_tick=0; end join_none
      end
    end
  end endtask

  // Read data is captured at the end of DBIN, after the vm80a core has sampled
  // it. The active 8238 strobe classifies the transfer.
  always @(negedge dtop.dbin) if (!done) begin
    if (~dtop.memr_n)
      check_event("MR", dtop.BA, dtop.U_CPU.u.core.di);
    else if (~dtop.iord_n)
      check_event("IR", {8'h00, dtop.BA[7:0]}, dtop.U_CPU.u.core.di);
    else if (~dtop.inta_n)
      check_event("IA", 16'h0000, dtop.U_CPU.u.core.di);
  end

  // WR_N is the CPU-side write envelope. A delta of settling lets the 8238
  // status decode and DB transceiver reach their stable values before capture.
  always @(negedge dtop.wr_n) if (!done && $time > 2000) begin
    #0.1;
    if (~dtop.memw_n)
      check_event("MW", dtop.BA, dtop.DB);
    else if (~dtop.iowr_raw_n)
      check_event("IW", {8'h00, dtop.BA[7:0]}, dtop.DB);
  end
  initial begin #(timecap);
    if (!done) $display("BTRACE-OK: %0d events compared within window; juku_top == cosim", nevent);
    $finish;
  end
endmodule
`default_nettype wire
