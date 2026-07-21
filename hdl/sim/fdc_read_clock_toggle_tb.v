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

    task expect_pair(input expected_q, input expected_q_n, input [191:0] label);
        begin
            #1;
            if (q !== expected_q || q_n !== expected_q_n) begin
                $display("D96-RCLK: FAIL %0s q=%b q_n=%b expected=%b/%b",
                         label, q, q_n, expected_q, expected_q_n);
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
        // WREQ_N drives both active-low controls. The SN74LS74A truth table
        // makes both outputs high while both controls are asserted; neither
        // clear nor preset may be assigned priority here.
        #1 wreq_n = 1'b0;
        expect_pair(1'b1, 1'b1, "WREQ asserts both asynchronous controls");
        rising_edge();
        expect_pair(1'b1, 1'b1, "clock is ignored during both-asserted state");
        #1 wreq_n = 1'b1;

        // Simultaneous release has no guaranteed hardware phase. This model
        // retains H/H until the first edge; thereafter /Q feedback divides by
        // two, which is the phase-independent behavior proved here.
        expect_pair(1'b1, 1'b1, "model retains forbidden state until an edge");
        rising_edge(); expect_pair(1'b1, 1'b0, "first recovered edge");
        rising_edge(); expect_pair(1'b0, 1'b1, "second recovered edge");
        rising_edge(); expect_pair(1'b1, 1'b0, "third recovered edge");
        rising_edge(); expect_pair(1'b0, 1'b1, "fourth recovered edge");

        #1 wreq_n = 1'b0;
        expect_pair(1'b1, 1'b1, "second WREQ assertion");
        #1 wreq_n = 1'b1;
        rising_edge(); expect_pair(1'b1, 1'b0, "first post-release edge");
        rising_edge(); expect_pair(1'b0, 1'b1, "post-release divide continues");

        $display("D96-RCLK: PASS both-async state exposed; /Q feedback divides after release");
        $finish;
    end
endmodule
