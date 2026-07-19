`timescale 1ns/1ps

module fdc_read_clock_toggle_tb;
    reg wreq_n = 1'b1;
    reg clk = 1'b0;
    wire q, q_n, q2_n_test;

    tm2_dff #(.FUNCTIONAL(1)) U_D96 (
        .clr1_n(wreq_n), .d1(q_n), .clk1(clk), .pre1_n(wreq_n),
        .q1(q), .q1_n(q_n),
        .clr2_n(1'bz), .d2(1'bz), .clk2(1'bz), .pre2_n(1'bz),
        .q2(), .q2_n(q2_n_test));

    task expect_q(input expected, input [127:0] label);
        begin
            #1;
            if (q !== expected) begin
                $display("D96-RCLK: FAIL %0s q=%b expected=%b", label, q, expected);
                $fatal(1);
            end
        end
    endtask

    task rising_edge;
        begin
            #4 clk = 1'b1;
            #1 clk = 1'b0;
        end
    endtask

    initial begin
        // WREQ_N drives both active-low controls. Clear wins the deliberately
        // simultaneous write-time assertion; read-clock state is irrelevant
        // while the controller writes.
        #1 wreq_n = 1'b0;
        expect_q(1'b0, "WREQ assertion");
        #1 wreq_n = 1'b1;

        rising_edge(); expect_q(1'b1, "first recovered edge");
        rising_edge(); expect_q(1'b0, "second recovered edge");
        rising_edge(); expect_q(1'b1, "third recovered edge");
        rising_edge(); expect_q(1'b0, "fourth recovered edge");

        #1 wreq_n = 1'b0;
        expect_q(1'b0, "second WREQ assertion");
        #1 wreq_n = 1'b1;
        rising_edge(); expect_q(1'b1, "restart edge");

        $display("D96-RCLK: PASS WREQ controls, /Q feedback, divide-by-two, restart");
        $finish;
    end
endmodule
