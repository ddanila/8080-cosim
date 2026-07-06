`timescale 1ns/100ps
`default_nettype none

module basic_cart_window_tb;
  wire [7:0] d8_d;
  tri [7:0] db;
  reg oe_n = 1'b1;

  re3_prom U_D8(.a(5'b01000), .e_n(1'b0), .d(d8_d));       // 0x4000..0x5FFF -> D22
  exprom_8k U_D22(.a(13'h0000), .d(db), .cs_n(d8_d[3]), .oe_n(oe_n));

  initial begin
    #1;
    if (d8_d !== 8'hf7) begin
      $display("BASIC-CART-WINDOW: FAIL D8 page byte %02h, expected f7", d8_d);
      $finish;
    end
    oe_n = 1'b0;
    #2;
    if (db !== 8'hc3) begin
      $display("BASIC-CART-WINDOW: FAIL D22 byte %02h, expected c3", db);
      $finish;
    end
    $display("BASIC-CART-WINDOW: PASS");
    $finish;
  end
endmodule

`default_nettype wire
