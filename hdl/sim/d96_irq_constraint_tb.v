`timescale 1ns/1ps

module d96_irq_constraint_tb;
    reg condition_n = 1'b1;
    reg clk = 1'b0;
    reg clr_n = 1'b1;
    wire q, q_n;

    tm2_dff #(.FUNCTIONAL(1)) U_D96 (
        .clr1_n(1'b1), .d1(1'b0), .clk1(1'b0), .pre1_n(1'b1),
        .q1(), .q1_n(),
        .clr2_n(clr_n), .d2(condition_n), .clk2(clk),
        .pre2_n(condition_n), .q2(q), .q2_n(q_n));

    task expect_q(input expected, input [191:0] label);
        begin
            #1;
            if (q !== expected || q_n !== ~expected) begin
                $display("D96-IRQ-CONSTRAINT: FAIL %0s q=%b q_n=%b expected=%b",
                         label, q, q_n, expected);
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
        // Establish Q=0 through the only valid clear path. The recovered board
        // drawing leaves this pin unconnected; the pulse here is a device-proof
        // stimulus, not a claim about target-board copper.
        #1 clr_n = 1'b0;
        expect_q(1'b0, "explicit clear establishes Q low");
        #1 clr_n = 1'b1;

        // When the shared PRE_N/D node is high, Q can retain a previous zero
        // only until the first positive clock edge; D=1 then sets it.
        expect_q(1'b0, "inactive controls hold previous zero before clock");
        rising_edge();
        expect_q(1'b1, "clock with shared node high captures one");
        rising_edge();
        expect_q(1'b1, "later clocks cannot clear while D is high");

        // A low shared node asynchronously presets Q, also to one.
        #1 condition_n = 1'b0;
        expect_q(1'b1, "condition low asynchronously presets Q");
        #1 condition_n = 1'b1;
        rising_edge();
        expect_q(1'b1, "condition release plus clock still captures one");

        // Show again that only CLR_N can produce zero in the valid truth table.
        #1 clr_n = 1'b0;
        expect_q(1'b0, "second explicit clear is sole zero-producing input");
        #1 clr_n = 1'b1;
        #1 condition_n = 1'b0;
        expect_q(1'b1, "shared node immediately sets after clear release");

        $display("D96-IRQ-CONSTRAINT: PASS shared PRE_N/D only sets Q; CLR_N is sole clear");
        $finish;
    end
endmodule
