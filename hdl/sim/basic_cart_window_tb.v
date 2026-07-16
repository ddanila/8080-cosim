`timescale 1ns/100ps
`default_nettype none

module basic_cart_window_tb;
  tri1 [7:0] d8_d;
  tri [7:0] db;
  reg oe_n = 1'b1;

  re3_prom U_D8(.a(5'b01000), .e_n(1'b0), .d(d8_d));       // physical .039 row for 0x4000
  exprom_8k U_D22(.a(13'h0000), .d(db), .cs_n(d8_d[3]), .oe_n(oe_n));

  initial begin
    #1;
    if (d8_d !== 8'hff) begin
      $display("BASIC-CART-WINDOW: FAIL D8 page byte %02h, expected physical ff", d8_d);
      $finish;
    end
    oe_n = 1'b0;
    #2;
    if (db !== 8'hzz) begin
      $display("BASIC-CART-WINDOW: FAIL D22 drove %02h despite physical D8 release", db);
      $finish;
    end
    $display("BASIC-CART-WINDOW: PASS");
    $finish;
  end
endmodule

`default_nettype wire
