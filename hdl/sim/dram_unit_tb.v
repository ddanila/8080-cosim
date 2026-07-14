// Unit-test the actual К565РУ5/4164-class model from hdl/devices.v. Besides
// row/column addressing, cover all write command orderings used by asynchronous
// DRAM: early write (WE before CAS), delayed write (CAS before WE), and coincident
// control edges. Every case is followed immediately by a read of the same cell.
`timescale 1ns/100ps
`default_nettype none

module dram_unit_tb;
  reg [7:0] ma = 0;
  reg ras_n = 1, cas_n = 1, we_n = 1, di = 0;
  wire do_;
  integer errors = 0;
  reg dec_a = 0, dec_b = 0, dec_active = 0, dec_ram_n = 1;
  wire [3:0] dec_y_n;
  wire dec_cas_n;

  dram_64kx1 dut(
    .ma(ma), .ras_n(ras_n), .cas_n(cas_n), .we_n(we_n), .di(di),
    .nc_vbb_option(1'b0), .vcc_option(1'b1), .vss_gnd(1'b0),
    .do_(do_), .va(16'b0), .vq()
  );

  rascas_dec dec(
    .a(dec_a), .b(dec_b), .c(1'b0), .g(1'b1), .g2a_n(1'b0), .g2b_n(1'b0),
    .sactive(dec_active), .ram_en_sim(dec_ram_n), .y_n(dec_y_n),
    .y_n4(), .y_n5(), .y_n6(), .y_n7(), .cas_sim(dec_cas_n)
  );

  // D48/D49 scramble the physical row rails. The production model reverses
  // this permutation internally so its memory index remains CPU-linear.
  function automatic [7:0] raw_row(input [7:0] linear);
    raw_row = {linear[0], linear[7], linear[6], linear[4],
               linear[2], linear[3], linear[5], linear[1]};
  endfunction

  task automatic begin_access(input [15:0] addr);
    begin
      ma = raw_row(addr[15:8]);
      #1 ras_n = 0;
      #1 ma = addr[7:0];
    end
  endtask

  task automatic end_access;
    begin
      #1 cas_n = 1;
      we_n = 1;
      ras_n = 1;
      #1;
    end
  endtask

  task automatic early_write(input [15:0] addr, input value);
    begin
      begin_access(addr);
      di = value;
      we_n = 0;
      #1 cas_n = 0;
      end_access;
    end
  endtask

  task automatic delayed_write(input [15:0] addr, input value);
    begin
      begin_access(addr);
      cas_n = 0;
      #1 di = value;
      we_n = 0;
      end_access;
    end
  endtask

  task automatic coincident_write(input [15:0] addr, input value);
    begin
      begin_access(addr);
      di = value;
      #1;
      // Deliberately update both controls in one simulation time slot. The old
      // synthetic-sclk model made the result depend on event ordering here.
      we_n = 0;
      cas_n = 0;
      end_access;
    end
  endtask

  task automatic expect_read(input [15:0] addr, input expected);
    begin
      begin_access(addr);
      cas_n = 0;
      #1;
      if (do_ !== expected) begin
        errors = errors + 1;
        $display("[DRAM-UNIT] FAIL @%04h expected=%b got=%b", addr, expected, do_);
      end
      end_access;
    end
  endtask

  initial begin
    early_write(16'h0000, 1'b1);
    expect_read(16'h0000, 1'b1);

    delayed_write(16'h1234, 1'b1);
    expect_read(16'h1234, 1'b1);

    coincident_write(16'hd300, 1'b1);
    expect_read(16'hd300, 1'b1);

    // Exercise address extremes and prove row/column reversal does not alias.
    early_write(16'habcd, 1'b1);
    early_write(16'hcdab, 1'b0);
    early_write(16'hffff, 1'b1);
    expect_read(16'habcd, 1'b1);
    expect_read(16'hcdab, 1'b0);
    expect_read(16'hffff, 1'b1);

    // The functional D53 scaffold must keep RAS low after the row phase and
    // throughout the CAS column pulse, then precharge both at access end.
    dec_ram_n = 0;
    dec_active = 1;
    dec_a = 1;
    #1;
    if (dec_y_n[0] !== 1'b0 || dec_cas_n !== 1'b1) errors = errors + 1;
    dec_a = 0;
    dec_b = 1;
    #1;
    if (dec_y_n[0] !== 1'b0 || dec_cas_n !== 1'b0) errors = errors + 1;
    dec_b = 0;
    #1;
    if (dec_y_n[0] !== 1'b0 || dec_cas_n !== 1'b1) errors = errors + 1;
    dec_active = 0;
    #1;
    if (dec_y_n[0] !== 1'b1 || dec_cas_n !== 1'b1) errors = errors + 1;

    if (errors == 0)
      $display("[DRAM-UNIT] PASS: RAS/CAS sequencing plus early/delayed/coincident writes");
    else
      $display("[DRAM-UNIT] %0d FAILURES", errors);
    $finish;
  end
endmodule

`default_nettype wire
