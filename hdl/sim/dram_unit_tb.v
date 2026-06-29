// Loop A: unit-test a faithful vv565vvvv5 (4164-class) 64Kx1 DRAM model + the row/col
// multiplexed-address sequencing it needs. Each chip has only an 8-bit address bus;
// the 16-bit address is presented as ROW (latched on RAS falling) then COL (latched
// on CAS falling). This proves the addressing reconstructs 64K correctly before we
// wire 8 of these (bit-sliced) into the structural sim.
`timescale 1ns/100ps
`default_nettype none

// --- vv565vvvv5: 64Kx1 DRAM. Row latched on RASvvv, col on CASvvv, R/W resolved at CAS. ---
module dram_64kx1(input wire [7:0] ma, input wire ras_n, cas_n, we_n, di, output wire do_);
  reg [0:0] bits [0:65535];
  reg [7:0] row;
  reg       q;
  wire [15:0] adr = {row, ma};                       // col = ma at CAS time
  always @(negedge ras_n) row <= ma;                 // strobe row address
  always @(negedge cas_n) begin                      // strobe col -> full address
    if (~we_n) bits[adr] <= di;                      // write (early-write style)
    q <= (~we_n) ? di : bits[adr][0];                // read data out
  end
  assign do_ = q;
endmodule

// --- convention row/col + RAS/CAS sequencer for one vvP access (NOT traced; standard
//     DRAM-controller behavior). Drives ma=row, RASvvv, ma=col, CASvvv, then releases. ---
module dram_access(input wire clk, input wire start, input wire [15:0] addr, input wire we,
                   output reg [7:0] ma, output reg ras_n, cas_n, we_n, output reg busy);
  reg [2:0] st;
  initial begin ras_n=1; cas_n=1; we_n=1; ma=0; busy=0; st=0; end
  always @(posedge clk) begin
    case (st)
      0: if (start) begin ma<=addr[15:8]; we_n<=~we; busy<=1; st<=1; end  // present ROW
      1: begin ras_n<=0;            st<=2; end                            // RASvvv (latch row)
      2: begin ma<=addr[7:0];       st<=3; end                            // present COL
      3: begin cas_n<=0;            st<=4; end                            // CASvvv (latch col, R/W)
      4: begin ras_n<=1; cas_n<=1; we_n<=1; busy<=0; st<=0; end           // release
    endcase
  end
endmodule

module dram_unit_tb();
  reg clk=0; initial forever #5 clk=~clk;
  reg start=0, we=0; reg [15:0] addr; reg di_r;
  wire [7:0] ma; wire ras_n, cas_n, we_n, busy, do_;
  dram_access ctl(.clk(clk), .start(start), .addr(addr), .we(we), .ma(ma), .ras_n(ras_n), .cas_n(cas_n), .we_n(we_n), .busy(busy));
  dram_64kx1  mem(.ma(ma), .ras_n(ras_n), .cas_n(cas_n), .we_n(we_n), .di(di_r), .do_(do_));

  integer i, errors;
  task do_access(input [15:0] a, input w, input d);
    begin addr=a; we=w; di_r=d; @(negedge clk) start=1; @(negedge clk) start=0;
          wait(!busy); @(negedge clk); end
  endtask

  initial begin
    errors=0;
    // write a pattern to several spread-out addresses (exercises row+col bits)
    do_access(16'h0000,1,1'b1); do_access(16'h1234,1,1'b0); do_access(16'hABCD,1,1'b1);
    do_access(16'hFFFF,1,1'b1); do_access(16'h00FF,1,1'b0); do_access(16'hFF00,1,1'b1);
    // read back and check
    do_access(16'h0000,0,1'b0); if (do_!==1'b1) begin errors=errors+1; $display("FAIL @0000 got %b",do_); end
    do_access(16'h1234,0,1'b0); if (do_!==1'b0) begin errors=errors+1; $display("FAIL @1234 got %b",do_); end
    do_access(16'hABCD,0,1'b0); if (do_!==1'b1) begin errors=errors+1; $display("FAIL @ABCD got %b",do_); end
    do_access(16'hFFFF,0,1'b0); if (do_!==1'b1) begin errors=errors+1; $display("FAIL @FFFF got %b",do_); end
    do_access(16'h00FF,0,1'b0); if (do_!==1'b0) begin errors=errors+1; $display("FAIL @00FF got %b",do_); end
    do_access(16'hFF00,0,1'b0); if (do_!==1'b1) begin errors=errors+1; $display("FAIL @FF00 got %b",do_); end
    // alias check: 0x1234 (row 12 col 34) must NOT collide with 0x3412 (row 34 col 12)
    do_access(16'h3412,1,1'b1); do_access(16'h1234,0,1'b0);
    if (do_!==1'b0) begin errors=errors+1; $display("FAIL alias 1234 vs 3412"); end
    if (errors==0) $display("[DRAM-UNIT] PASS: 64K row/col addressing correct");
    else           $display("[DRAM-UNIT] %0d FAILURES", errors);
    $finish;
  end
endmodule
`default_nettype wire
