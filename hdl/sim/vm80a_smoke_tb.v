// Phase C, step 1: smoke-test the vendored vm80a (die-accurate КР580ВМ80А) in our
// iverilog toolchain. Run a trivial program through the real 8080 bus protocol and
// confirm the store reaches memory. (Not yet through the netlist structure -- that's
// the next step; this validates the core + clocking work for us.)
//   MVI A,0x42 / STA 0x4000 / HLT
// Run: iverilog -g2012 -o smoke hdl/vendor/vm80a.v hdl/sim/vm80a_smoke_tb.v && vvp smoke
`timescale 1ns/100ps

module vm80a_smoke_tb();
  tri1 [7:0] d;                       // data bus (pull-up, like the real open bus)
  wire [15:0] a;
  reg  clk=0, f1=0, f2=0, reset=1, ready=1, hold=0, intr=0;
  wire inte, hlda, waitr, sync, dbin, wr_n;
  reg  [7:0] mem [0:65535];
  integer i;

  // --- clock + 2-phase generator (fast pin_clk; f1/f2 = phase enables) ---
  initial forever begin
    f1=1; clk=0; #10; clk=1; #10;
    f1=0; f2=1; clk=0; #10; clk=1; #10;
    f2=0;
  end

  // --- behavioral memory: drive bus on DBIN (read), latch on /WR (write) ---
  assign d = dbin ? mem[a] : 8'hzz;
  always @(negedge wr_n) begin
    mem[a] = d;
    if (a == 16'h4000) begin
      $display("[smoke] STA wrote 0x%02h to 0x4000  ->  %s", d, d==8'h42 ? "PASS" : "FAIL");
      $finish;
    end
  end

  initial begin                       // trivial program
    for (i=0;i<65536;i=i+1) mem[i]=8'h00;
    mem[0]=8'h3E; mem[1]=8'h42;             // MVI A,0x42
    mem[2]=8'h32; mem[3]=8'h00; mem[4]=8'h40;// STA 0x4000
    mem[5]=8'h76;                            // HLT
  end

  initial begin reset=1; #2000 reset=0; end
  initial begin #500000 $display("[smoke] TIMEOUT (no store seen)"); $finish; end

  vm80a cpu (.pin_clk(clk), .pin_f1(f1), .pin_f2(f2), .pin_d(d), .pin_a(a),
             .pin_reset(reset), .pin_hold(hold), .pin_hlda(hlda), .pin_ready(ready),
             .pin_wait(waitr), .pin_int(intr), .pin_inte(inte), .pin_sync(sync),
             .pin_dbin(dbin), .pin_wr_n(wr_n));
endmodule
