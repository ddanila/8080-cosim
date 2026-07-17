// VJUGA rev B — bus-functional model (shared task library for per-card unit TBs).
// `include this into a testbench that declares the standard driver signals below
// and connects them to the card under test. The BFM issues single memory / I/O
// read and write cycles on the rev B bus and checks read data against expectations,
// counting mismatches in `errors`. Reads are combinational (async-SRAM style), so
// a read task sets up the bus, waits, and samples `bDout`.
//
// Required in TB scope:
//   reg clk; reg [15:0] bA; reg [7:0] bD; reg bMREQ_n,bIORQ_n,bRD_n,bWR_n;
//   wire [7:0] bDout;          // TB assigns = card D_oe ? card D_out : 8'hFF
//   integer errors;

task bus_idle;
    begin bMREQ_n = 1; bIORQ_n = 1; bRD_n = 1; bWR_n = 1; bD = 8'h00; end
endtask

task mem_wr(input [15:0] a, input [7:0] d);
    begin
        @(negedge clk); bA = a; bD = d; bMREQ_n = 0; bWR_n = 0;
        @(posedge clk);                 // card captures on this edge
        @(negedge clk); bus_idle;
    end
endtask

task io_wr(input [15:0] a, input [7:0] d);
    begin
        @(negedge clk); bA = a; bD = d; bIORQ_n = 0; bWR_n = 0;
        @(posedge clk);
        @(negedge clk); bus_idle;
    end
endtask

task chk_mem_rd(input [15:0] a, input [7:0] exp, input [127:0] msg);
    begin
        @(negedge clk); bA = a; bMREQ_n = 0; bRD_n = 0; #2;
        if (bDout !== exp) begin
            errors = errors + 1;
            $display("  FAIL %0s: mem_rd[%04h] = %02h, expected %02h", msg, a, bDout, exp);
        end
        bus_idle; @(negedge clk);
    end
endtask

task chk_io_rd(input [15:0] a, input [7:0] exp, input [127:0] msg);
    begin
        @(negedge clk); bA = a; bIORQ_n = 0; bRD_n = 0; #2;
        if (bDout !== exp) begin
            errors = errors + 1;
            $display("  FAIL %0s: io_rd[%02h] = %02h, expected %02h", msg, a[7:0], bDout, exp);
        end
        bus_idle; @(negedge clk);
    end
endtask
