`timescale 1ns/1ps

// К555ИЕ10 / SN74LS161A package contract plus the traced D103 /13 loop.
module ie10_ctr_tb;
    reg clk = 1'b0;
    reg clr_n = 1'b1;
    reg load_n = 1'b1;
    reg enp = 1'b1;
    reg ent = 1'b1;
    reg [3:0] d = 4'b0;
    wire [3:0] q;
    wire co;

    reg div_clk = 1'b0;
    reg div_clr_n = 1'b1;
    wire [3:0] div_q;
    wire div_co;
    wire div_load_n = ~div_co;  // D33 section 1->2 inversion

    integer errors = 0;
    integer i;

    ie10_ctr dut (.clk(clk), .clr_n(clr_n), .load_n(load_n),
                  .enp(enp), .ent(ent), .d(d), .q(q), .co(co));
    ie10_ctr divider (.clk(div_clk), .clr_n(div_clr_n),
                      .load_n(div_load_n), .enp(1'b1), .ent(1'b1),
                      .d(4'b0011), .q(div_q), .co(div_co));

    task pulse;
        begin
            clk = 1'b1; #1;
            clk = 1'b0; #1;
        end
    endtask

    task div_pulse;
        begin
            div_clk = 1'b1; #1;
            div_clk = 1'b0; #1;
        end
    endtask

    task expect_q;
        input [3:0] want;
        input [159:0] label;
        begin
            #1;
            if (q !== want) begin
                $display("[IE10] FAIL %-20s q=%h want=%h", label, q, want);
                errors = errors + 1;
            end
        end
    endtask

    task expect_div;
        input [3:0] want;
        input [159:0] label;
        begin
            #1;
            if (div_q !== want) begin
                $display("[IE10] FAIL %-20s div_q=%h want=%h", label, div_q, want);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        // Direct clear acts without a clock and dominates a coincident clock.
        d = 4'hA; load_n = 1'b0; clr_n = 1'b0; #1;
        expect_q(4'h0, "direct clear");
        pulse();
        expect_q(4'h0, "clear dominates");

        // Unlike IE7, /LOAD and data are synchronous: neither changes Q until
        // the rising edge, where load has priority over disabled counting.
        clr_n = 1'b1; #1;
        expect_q(4'h0, "load waits for clock");
        d = 4'hB; #1;
        expect_q(4'h0, "data waits for clock");
        enp = 1'b0; ent = 1'b0; pulse();
        expect_q(4'hB, "load priority");
        load_n = 1'b1;

        // Either low enable holds the state; both high count modulo 16.
        ent = 1'b1; pulse();
        expect_q(4'hB, "ENP hold");
        enp = 1'b1; ent = 1'b0; pulse();
        expect_q(4'hB, "ENT hold");
        ent = 1'b1;
        for (i = 1; i <= 16; i = i + 1) begin
            pulse();
            expect_q((4'hB + i) & 4'hF, "binary sequence");
        end

        // RCO is combinational, high only for F with ENT asserted.
        d = 4'hF; load_n = 1'b0; pulse(); load_n = 1'b1; #1;
        if (co !== 1'b1) begin
            $display("[IE10] FAIL terminal RCO co=%b", co);
            errors = errors + 1;
        end
        ent = 1'b0; #1;
        if (co !== 1'b0) begin
            $display("[IE10] FAIL ENT-gated RCO co=%b", co);
            errors = errors + 1;
        end
        ent = 1'b1;

        // Board circuit: after startup reaches F, inverted RCO makes the next
        // rising edge synchronously load 3. Thereafter 3..F is exactly 13
        // input clocks, and Q3 is the labeled 1.23 MHz periodic output.
        div_clr_n = 1'b0; #1; div_clr_n = 1'b1; #1;
        for (i = 1; i <= 15; i = i + 1) div_pulse();
        expect_div(4'hF, "startup terminal");
        if (div_co !== 1'b1 || div_load_n !== 1'b0) begin
            $display("[IE10] FAIL divider reload arm co=%b load_n=%b", div_co, div_load_n);
            errors = errors + 1;
        end
        div_pulse();
        expect_div(4'h3, "reload preset 3");
        for (i = 1; i <= 12; i = i + 1) div_pulse();
        expect_div(4'hF, "13-clock terminal");
        div_pulse();
        expect_div(4'h3, "13-clock repeat");

        if (errors == 0)
            $display("IE10-CTR: PASS direct-clear sync-load enables RCO traced-div13");
        else begin
            $display("IE10-CTR: FAIL errors=%0d", errors);
            $fatal(1);
        end
        $finish;
    end
endmodule
