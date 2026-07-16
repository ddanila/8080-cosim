`timescale 1ns/1ps

module buf_8287_tb;
  tri [7:0] db;
  tri [7:0] dal;
  tri [7:0] db_always;
  tri [7:0] dal_always;
  tri [7:0] bp_a;
  tri [7:0] bp_b;
  reg [7:0] cpu_data = 8'h00;
  reg [7:0] fdc_data = 8'h00;
  reg cpu_drive = 1'b0;
  reg fdc_drive = 1'b0;
  reg fdc_cs_n = 1'b1;
  reg iord_n = 1'b1;
  reg bp_a_drive = 1'b0;
  reg bp_b_drive = 1'b0;
  reg [7:0] bp_a_data = 8'h00;
  reg [7:0] bp_b_data = 8'h00;
  reg bp_t = 1'b1;
  integer value;

  assign db = cpu_drive ? cpu_data : 8'hzz;
  assign dal = fdc_drive ? fdc_data : 8'hzz;
  assign db_always = cpu_drive ? cpu_data : 8'hzz;
  assign dal_always = fdc_drive ? fdc_data : 8'hzz;
  assign bp_a = bp_a_drive ? bp_a_data : 8'hzz;
  assign bp_b = bp_b_drive ? bp_b_data : 8'hzz;

  // Minimal functional control candidate consistent with the device contract:
  // selected writes have IORD high (T=1, DB -> DAL), selected reads have
  // IORD low (T=0, DAL -> DB), and deselection releases both buses.
  buf_8287 dut(
    .a(db), .b(dal), .oe_n(fdc_cs_n), .t(iord_n),
    .vss_gnd(1'b0), .vcc_5v(1'b1)
  );
  // Same required cycle states, using the always-enabled family seen on the
  // board's D23-D25 ВА87s. D93_RE_N is high except on a selected FDC read.
  buf_8287 dut_always_enabled(
    .a(db_always), .b(dal_always), .oe_n(1'b0),
    .t(fdc_cs_n | iord_n), .vss_gnd(1'b0), .vcc_5v(1'b1)
  );
  va87_out dut_backplane(.Ain(bp_a), .Aout(bp_b), .oe_n(1'b0), .t(bp_t));

  initial begin
    cpu_drive = 1'b1;
    cpu_data = 8'h5a;
    #1;
    if (dal !== 8'hzz) begin
      $display("BUF-8287: FAIL deselected DAL=%h", dal);
      $finish_and_return(1);
    end
    if (db_always !== 8'h5a || dal_always !== 8'ha5) begin
      $display("BUF-8287: FAIL always-enabled idle DB=%h DAL=%h", db_always, dal_always);
      $finish_and_return(1);
    end

    fdc_cs_n = 1'b0;
    iord_n = 1'b1;
    for (value = 0; value < 256; value = value + 1) begin
      cpu_data = value[7:0];
      #1;
      if (dal !== ~value[7:0] || dal_always !== ~value[7:0]) begin
        $display("BUF-8287: FAIL write DB=%h qualified=%h always=%h",
                 value[7:0], dal, dal_always);
        $finish_and_return(1);
      end
    end

    cpu_drive = 1'b0;
    fdc_drive = 1'b1;
    iord_n = 1'b0;
    for (value = 0; value < 256; value = value + 1) begin
      fdc_data = value[7:0];
      #1;
      if (db !== ~value[7:0] || db_always !== ~value[7:0]) begin
        $display("BUF-8287: FAIL read DAL=%h qualified=%h always=%h",
                 value[7:0], db, db_always);
        $finish_and_return(1);
      end
    end

    fdc_drive = 1'b0;
    fdc_cs_n = 1'b1;
    #1;
    if (db !== 8'hzz || dal !== 8'hzz) begin
      $display("BUF-8287: FAIL released DB=%h DAL=%h", db, dal);
      $finish_and_return(1);
    end

    // The D23-D25 model uses the same full 8287 truth table, including D25's
    // traced turnaround direction rather than the former one-way approximation.
    bp_a_drive = 1'b1;
    bp_t = 1'b1;
    for (value = 0; value < 256; value = value + 1) begin
      bp_a_data = value[7:0];
      #1;
      if (bp_b !== ~value[7:0]) begin
        $display("BUF-8287: FAIL backplane A->B A=%h B=%h", value[7:0], bp_b);
        $finish_and_return(1);
      end
    end
    bp_a_drive = 1'b0;
    bp_b_drive = 1'b1;
    bp_t = 1'b0;
    for (value = 0; value < 256; value = value + 1) begin
      bp_b_data = value[7:0];
      #1;
      if (bp_a !== ~value[7:0]) begin
        $display("BUF-8287: FAIL backplane B->A B=%h A=%h", value[7:0], bp_a);
        $finish_and_return(1);
      end
    end

    $display("BUF-8287: PASS D100 control families and D23-D25, all 256 values both directions");
    $finish;
  end
endmodule
