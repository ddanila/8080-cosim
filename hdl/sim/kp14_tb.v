`timescale 1ns/1ps
`default_nettype none

module kp14_tb;
  reg [3:0] a = 4'b1010;
  reg [3:0] b = 4'b0101;
  reg sel = 0;
  reg en_n = 0;
  wire [3:0] y_n;
  integer errors = 0;

  kp14_mux dut(.a(a), .b(b), .sel(sel), .en_n(en_n), .y_n(y_n));

  task check_value;
    input [3:0] value;
    input [255:0] label;
    begin
      #1;
      if (y_n !== value) begin
        $display("KP14: FAIL %0s got=%b expected=%b", label, y_n, value);
        errors = errors + 1;
      end
    end
  endtask

  initial begin
    check_value(4'b0101, "select A with inverted output");
    sel = 1;
    check_value(4'b1010, "select B with inverted output");
    en_n = 1;
    check_value(4'bzzzz, "active-low enable high impedance");

    if (errors == 0)
      $display("KP14: PASS inverted selection and active-low enable");
    else
      $display("KP14: FAIL errors=%0d", errors);
    $finish;
  end
endmodule
`default_nettype wire
