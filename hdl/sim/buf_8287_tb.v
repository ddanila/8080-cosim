`timescale 1ns/1ps

module buf_8287_tb;
  tri [7:0] db;
  tri [7:0] dal;
  reg [7:0] cpu_data = 8'h00;
  reg [7:0] fdc_data = 8'h00;
  reg cpu_drive = 1'b0;
  reg fdc_drive = 1'b0;
  reg fdc_cs_n = 1'b1;
  reg iord_n = 1'b1;
  integer value;

  assign db = cpu_drive ? cpu_data : 8'hzz;
  assign dal = fdc_drive ? fdc_data : 8'hzz;

  // Minimal functional control candidate consistent with the device contract:
  // selected writes have IORD high (T=1, DB -> DAL), selected reads have
  // IORD low (T=0, DAL -> DB), and deselection releases both buses.
  buf_8287 dut(
    .a(db), .b(dal), .oe_n(fdc_cs_n), .t(iord_n),
    .vss_gnd(1'b0), .vcc_5v(1'b1)
  );

  initial begin
    cpu_drive = 1'b1;
    cpu_data = 8'h5a;
    #1;
    if (dal !== 8'hzz) begin
      $display("BUF-8287: FAIL deselected DAL=%h", dal);
      $finish_and_return(1);
    end

    fdc_cs_n = 1'b0;
    iord_n = 1'b1;
    for (value = 0; value < 256; value = value + 1) begin
      cpu_data = value[7:0];
      #1;
      if (dal !== ~value[7:0]) begin
        $display("BUF-8287: FAIL write DB=%h DAL=%h", value[7:0], dal);
        $finish_and_return(1);
      end
    end

    cpu_drive = 1'b0;
    fdc_drive = 1'b1;
    iord_n = 1'b0;
    for (value = 0; value < 256; value = value + 1) begin
      fdc_data = value[7:0];
      #1;
      if (db !== ~value[7:0]) begin
        $display("BUF-8287: FAIL read DAL=%h DB=%h", value[7:0], db);
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

    $display("BUF-8287: PASS all 256 values in both directions; disabled buses released");
    $finish;
  end
endmodule
