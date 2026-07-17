`timescale 1ns/1ps

// К155АГ3 / 74123 trigger, clear, complement, inhibit, and retrigger contract.
module ag3_oneshot_tb;
    reg a_n = 1'b1;
    reg b = 1'b0;
    reg clr_n = 1'b0;
    reg a2_n = 1'b1;
    reg b2 = 1'b0;
    reg clr2_n = 1'b0;
    wire q, q_n, q2, q2_n;
    integer errors = 0;

    ag3_oneshot #(
        .PULSE1_NS(100), .PULSE2_NS(40),
        .RETRIGGER1_NS(10), .RETRIGGER2_NS(5)
    ) dut (
        .a_n(a_n), .b(b), .clr_n(clr_n),
        .a2_n(a2_n), .b2(b2), .clr2_n(clr2_n),
        .q(q), .q_n(q_n), .q2(q2), .q2_n(q2_n)
    );

    task expect1;
        input want;
        input [255:0] label;
        begin
            #1;
            if (q !== want || q_n !== ~want) begin
                $display("[AG3] FAIL %-32s q/q_n=%b/%b want=%b/%b", label, q, q_n, want, ~want);
                errors = errors + 1;
            end
        end
    endtask

    task expect2;
        input want;
        input [255:0] label;
        begin
            #1;
            if (q2 !== want || q2_n !== ~want) begin
                $display("[AG3] FAIL %-32s q2/q2_n=%b/%b want=%b/%b", label, q2, q2_n, want, ~want);
                errors = errors + 1;
            end
        end
    endtask

    initial begin
        // Overriding clear fixes both complementary output pairs.
        expect1(1'b0, "section1 clear");
        expect2(1'b0, "section2 clear");
        clr_n = 1'b1;
        clr2_n = 1'b1;

        // B does not trigger while A is high. A falling with B already high does.
        b = 1'b1;
        expect1(1'b0, "B inhibited by A high");
        a_n = 1'b0;
        expect1(1'b1, "A falling trigger");
        #99;
        expect1(1'b0, "section1 pulse duration");

        // A low enables a B rising trigger. A second valid edge extends the pulse.
        b = 1'b0; #10; b = 1'b1;
        expect1(1'b1, "B rising trigger");
        #49; b = 1'b0; #1; b = 1'b1;
        expect1(1'b1, "valid retrigger");
        #97;
        expect1(1'b1, "retrigger extends pulse");
        #2;
        expect1(1'b0, "extended pulse completes");

        // A retrigger inside the Cext-dependent inhibit window is ignored.
        b = 1'b0; #10; b = 1'b1;
        #2; b = 1'b0; #1; b = 1'b1;
        #95;
        expect1(1'b1, "early retrigger ignored until original end");
        #2;
        expect1(1'b0, "early retrigger did not extend");

        // Clear terminates immediately; its rising edge is itself a trigger when
        // A is low and B is high, as specified by the 74123 function table.
        b = 1'b0; #10; b = 1'b1; #10;
        clr_n = 1'b0;
        expect1(1'b0, "clear terminates pulse");
        clr_n = 1'b1;
        expect1(1'b1, "clear release trigger");
        clr_n = 1'b0;
        expect1(1'b0, "second clear terminates");

        // The second half is independent and uses its own pulse duration.
        a2_n = 1'b0;
        b2 = 1'b1;
        clr2_n = 1'b1;
        expect2(1'b1, "section2 clear-release trigger");
        #39;
        expect2(1'b0, "section2 pulse duration");
        if (q !== 1'b0 || q_n !== 1'b1) begin
            $display("[AG3] FAIL section independence q/q_n=%b/%b", q, q_n);
            errors = errors + 1;
        end

        if (errors == 0)
            $display("AG3-ONESHOT: PASS triggers clear complements inhibit retrigger dual-sections");
        else begin
            $display("AG3-ONESHOT: FAIL errors=%0d", errors);
            $fatal(1);
        end
        $finish;
    end
endmodule
