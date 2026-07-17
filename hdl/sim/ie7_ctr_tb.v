`timescale 1ns/1ps

// Literal К555ИЕ7 / SN74LS193 behavior and two-package cascade guard.
module ie7_ctr_tb;
    reg up = 1'b1;
    reg down = 1'b1;
    reg load_n = 1'b1;
    reg clr = 1'b0;
    reg [3:0] d = 4'b0;
    wire [3:0] q;
    wire co;
    wire bo;

    wire [3:0] q_hi;
    wire co_hi;
    wire bo_hi;
    ie7_ctr dut (.up(up), .down(down), .load_n(load_n), .clr(clr),
                 .d(d), .q(q), .co(co), .bo(bo));
    ie7_ctr high (.up(co), .down(bo), .load_n(load_n), .clr(clr),
                  .d(4'b0), .q(q_hi), .co(co_hi), .bo(bo_hi));

    integer errors = 0;
    integer i;

    task expect_q;
        input [3:0] want;
        input [127:0] label;
        begin
            #1;
            if (q !== want) begin
                $display("[IE7] FAIL %-16s q=%h want=%h", label, q, want);
                errors = errors + 1;
            end
        end
    endtask

    task expect_pair;
        input [7:0] want;
        input [127:0] label;
        begin
            #1;
            if ({q_hi, q} !== want) begin
                $display("[IE7] FAIL %-16s pair=%h want=%h", label, {q_hi, q}, want);
                errors = errors + 1;
            end
        end
    endtask

    task pulse_up;
        begin
            up = 1'b0; #1;
            up = 1'b1; #1;
        end
    endtask

    task pulse_down;
        begin
            down = 1'b0; #1;
            down = 1'b1; #1;
        end
    endtask

    initial begin
        // Asynchronous clear dominates clocks, load, and data.
        d = 4'hA; load_n = 1'b0; clr = 1'b1; #1;
        expect_q(4'h0, "clear dominates");
        pulse_up();
        pulse_down();
        expect_q(4'h0, "clear holds");

        // Releasing clear under asserted /LOAD immediately exposes D, and D
        // changes continue to propagate without a clock.
        clr = 1'b0; #1;
        expect_q(4'hA, "async load");
        d = 4'h5; #1;
        expect_q(4'h5, "load follows d");
        load_n = 1'b1; #1;

        // Opposite clock low inhibits the selected rising edge.
        down = 1'b0; pulse_up();
        expect_q(4'h5, "up inhibited");
        load_n = 1'b0; down = 1'b1; #1; load_n = 1'b1; #1;
        up = 1'b0; pulse_down();
        expect_q(4'h5, "down inhibited");
        load_n = 1'b0; up = 1'b1; #1; load_n = 1'b1; #1;

        // Exercise every state and both wrap directions.
        d = 4'h0; load_n = 1'b0; #1; load_n = 1'b1; #1;
        for (i = 1; i <= 16; i = i + 1) begin
            pulse_up();
            expect_q(i[3:0], "up sequence");
        end
        for (i = 15; i >= 0; i = i - 1) begin
            pulse_down();
            expect_q(i[3:0], "down sequence");
        end

        // /CO and /BO are low only through the corresponding low clock phase
        // at terminal count; the other cascade output remains inactive.
        d = 4'hF; load_n = 1'b0; #1; load_n = 1'b1; #1;
        up = 1'b0; #1;
        if (co !== 1'b0 || bo !== 1'b1) begin
            $display("[IE7] FAIL carry pulse co=%b bo=%b", co, bo);
            errors = errors + 1;
        end
        up = 1'b1; #1;
        d = 4'h0; load_n = 1'b0; #1; load_n = 1'b1; #1;
        down = 1'b0; #1;
        if (bo !== 1'b0 || co !== 1'b1) begin
            $display("[IE7] FAIL borrow pulse co=%b bo=%b", co, bo);
            errors = errors + 1;
        end
        down = 1'b1; #1;

        // The active-low terminal pulses clock the succeeding package on their
        // rising edge: 0x0F -> 0x10 and 0x10 -> 0x0F, without an early carry.
        d = 4'h0; load_n = 1'b0; #1; load_n = 1'b1; #1;
        for (i = 1; i <= 15; i = i + 1) pulse_up();
        expect_pair(8'h0F, "before carry");
        pulse_up();
        expect_pair(8'h10, "after carry");
        pulse_down();
        expect_pair(8'h0F, "after borrow");

        if (errors == 0)
            $display("IE7-CTR: PASS async-clear/load up/down terminal-pulses cascade");
        else begin
            $display("IE7-CTR: FAIL errors=%0d", errors);
            $fatal(1);
        end
        $finish;
    end
endmodule
