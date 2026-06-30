// Interrupt-mechanism unit test for the HDL twin (fast, synthetic ROM).
//
// vm80a is a real die: to interrupt it we must drive pin_int and feed the 8259's
// vector over the bus during the INTA machine cycle(s) -- there is no "push PC" shortcut
// like cosim's C. This TB proves that path on a tiny ROM (hdl/sim/intr_test.hex) before
// grafting it into the slow structural twin: assert pin_int, inject a 3-byte CALL
// (0xCD, lo, hi) on the INTA reads, and check the ISR ran (mem[0xD800]==0x55).
//
// Probes print every machine cycle (sync) + every injected INTA byte, so vm80a's exact
// INTA sequencing (how many INTA reads it does for a CALL-mode interrupt) is observed,
// not assumed.
//
// Run: iverilog -g2012 -o /tmp/jintr hdl/vendor/vm80a.v hdl/sim/intr_unit_tb.v && vvp /tmp/jintr
`timescale 1ns/100ps
`default_nettype none

module intr_unit_tb();
  reg osc=0, phi1=0, phi2=0, reset=1, ready=1;
  reg intr=0;
  wire [15:0] A; tri1 [7:0] D;
  wire dbin, wr_n, sync, hlda, inte;

  vm80a u(.pin_clk(osc), .pin_f1(phi1), .pin_f2(phi2), .pin_reset(reset),
          .pin_a(A), .pin_d(D), .pin_hold(1'b0), .pin_hlda(hlda), .pin_ready(ready),
          .pin_wait(), .pin_int(intr), .pin_inte(inte), .pin_sync(sync),
          .pin_dbin(dbin), .pin_wr_n(wr_n));

  // clock: same 2-phase + fast osc sampling as the structural twin
  initial forever begin
    phi1=1; osc=0; #10; osc=1; #10;
    phi1=0; phi2=1; osc=0; #10; osc=1; #10;
    phi2=0;
  end

  // 8080 status byte: latched on a clk edge inside the sync window (the delta-race lesson)
  reg [7:0] status=0; reg sq=0;
  always @(posedge osc) begin
    if (sync && !sq) status <= D;
    sq <= sync;
  end
  wire memr = dbin & ~status[6] & ~status[0];
  wire iord = dbin &  status[6];
  wire memw = ~wr_n & ~status[4];
  wire iow  = ~wr_n &  status[4];
  wire inta = dbin &  status[0];

  // flat memory, ROM image loaded from 0x0000
  reg [7:0] mem [0:65535]; integer i;
  initial begin
    for (i=0;i<65536;i=i+1) mem[i]=0;
    $readmemh("hdl/sim/intr_test.hex", mem);
  end

  // --- interrupt vector injection (3-byte CALL, MCS-80 mode) ---
  // CALL 0x0014 = {0xCD, 0x14, 0x00}; indexed by the INTA read counter.
  reg [7:0] vec [0:2]; initial begin vec[0]=8'hCD; vec[1]=8'h14; vec[2]=8'h00; end
  integer inta_idx = 0;

  // read-data sample-and-hold: latch the source at posedge dbin, hold across DBIN
  // (8080 tOS1/tOS2 -- combinational drive corrupts vm80a's fixed-phase capture).
  reg [7:0] rdata = 0;
  always @(posedge dbin) begin
    if (status[0]) begin rdata <= vec[inta_idx]; end   // INTA: inject vector byte
    else           begin rdata <= mem[A];          end   // memory / io read
  end
  assign D = dbin ? rdata : 8'bz;

  // advance the INTA byte index after each INTA read is consumed
  always @(negedge dbin) if (status[0]) begin
    $display("[INTA] read #%0d -> 0x%02h  (A=0x%04h)", inta_idx, vec[inta_idx], A);
    if (inta_idx < 2) inta_idx <= inta_idx + 1;
    else begin inta_idx <= 0; intr <= 0; end             // 3-byte CALL done; drop the request
  end

  // memory writes (sample while the write strobe is low)
  always @(posedge osc) if (memw) mem[A] = D;

  // per-machine-cycle probe + io-write trace
  reg [7:0] iolast = 0;
  always @(posedge osc) begin
    if (sync && !sq)
      $display("[MC ] t=%0t  A=0x%04h status=0x%02h %s", $time, A, D,
        (D[0]?"INTA":(D[6]?"IO":(D[4]?"OUT/W":"FETCH/R"))));
  end
  always @(negedge wr_n) if (iow) $display("[OUT] port=0x%02h <= 0x%02h", A[7:0], D);

  // drive the interrupt once the program is spinning in its EI loop, then watch the ISR fire
  initial begin
    reset=1; #2000 reset=0;
    #20000;                       // let LXI/8259-setup/EI run and reach the JMP $ spin
    $display("[TB ] asserting pin_int (frame interrupt)");
    intr = 1;
    #20000;                       // give the CPU time to ack + run the ISR + RET
    $display("[TB ] mem[0xD800] = 0x%02h  (expect 0x55 if the ISR ran)", mem[16'hD800]);
    if (mem[16'hD800] == 8'h55) $display("[TB ] PASS: interrupt -> ISR ran on the real vm80a die");
    else                        $display("[TB ] FAIL: ISR did not run (mem[0xD800]=0x%02h)", mem[16'hD800]);
    $finish;
  end
endmodule
`default_nettype wire
