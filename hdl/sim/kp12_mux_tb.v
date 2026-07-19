`timescale 1ns/1ps
module kp12_mux_tb;
    reg a0, a1, oe0_n, oe1_n;
    reg [3:0] d0, d1;
    wire q0, q1;
    integer sel;

    kp12_mux dut(.a0(a0), .a1(a1), .oe0_n(oe0_n), .oe1_n(oe1_n),
                 .d0(d0), .d1(d1), .q0(q0), .q1(q1));

    initial begin
        d0 = 4'b1010;
        d1 = 4'b0110;
        oe0_n = 0;
        oe1_n = 0;
        for (sel = 0; sel < 4; sel = sel + 1) begin
            {a1, a0} = sel[1:0];
            #1;
            if (q0 !== d0[sel] || q1 !== d1[sel]) begin
                $display("KP12-MUX: FAIL select=%0d q0=%b q1=%b", sel, q0, q1);
                $finish_and_return(1);
            end
        end
        oe0_n = 1;
        oe1_n = 1;
        #1;
        if (q0 !== 1'bz || q1 !== 1'bz) begin
            $display("KP12-MUX: FAIL disabled q0=%b q1=%b", q0, q1);
            $finish_and_return(1);
        end
        $display("KP12-MUX: PASS");
        $finish;
    end
endmodule
