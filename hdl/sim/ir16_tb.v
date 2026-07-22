`timescale 1ns/1ps
`default_nettype none

module ir16_tb;
  reg a = 0, b = 0, c = 0, d = 0;
  reg ld = 0, oc = 1, clk = 1, ser = 0;
  wire qa, qb, qc, qd;
  integer errors = 0;

  ir16 dut(.a(a), .b(b), .c(c), .d(d), .ld_sh(ld), .oc(oc), .clk(clk),
           .ser(ser), .qd(qd), .qa(qa), .qb(qb), .qc(qc));

  task check_value;
    input [3:0] value;
    input [255:0] label;
    begin
      #1;
      if ({qd, qc, qb, qa} !== value) begin
        $display("IR16: FAIL %0s got=%b expected=%b", label,
                 {qd, qc, qb, qa}, value);
        errors = errors + 1;
      end
    end
  endtask

  task falling_edge;
    begin
      #4 clk = 0;
      #4 clk = 1;
    end
  endtask

  initial begin
    // A-D = 1,0,1,0. A rising edge must not change this falling-edge device.
    {d, c, b, a} = 4'b0101;
    ld = 1;
    #4 clk = 0;
    check_value(4'b0101, "parallel load on falling edge");
    {d, c, b, a} = 4'b1010;
    #4 clk = 1;
    check_value(4'b0101, "rising edge ignored");

    // Right shift QA toward QD, with SER entering QA.
    ld = 0;
    ser = 1;
    falling_edge;
    check_value(4'b1011, "first right shift");
    ser = 0;
    falling_edge;
    check_value(4'b0110, "second right shift");

    // OC only controls output impedance; shifting continues while disabled.
    oc = 0;
    #1;
    if ({qd, qc, qb, qa} !== 4'bzzzz) begin
      $display("IR16: FAIL OC low got=%b expected=zzzz", {qd, qc, qb, qa});
      errors = errors + 1;
    end
    ser = 1;
    falling_edge;
    oc = 1;
    check_value(4'b1101, "state advances while outputs disabled");

    if (errors == 0)
      $display("IR16: PASS falling-edge load/shift and active-high OC");
    else
      $display("IR16: FAIL errors=%0d", errors);
    $finish;
  end
endmodule
`default_nettype wire
