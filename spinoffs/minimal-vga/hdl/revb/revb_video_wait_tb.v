// VJUGA rev B — Video /WAIT contention testbench (TI.2 gate c; D2.5).
// Scanout owns the framebuffer during the active region; a CPU framebuffer access there
// must be held off (WAIT_N low) and serviced in blanking, never lost. Two checks:
//   (1) every dot: wait_od_n == ~(cpu_access & active)  -- scanout-priority contract;
//   (2) writes launched in the active region are HELD then land correctly; writes
//       launched in blanking land immediately. Both are checked across many dot phases.
// Small timing params (frame ~ 98 dots) keep the sweep fast; the contention logic is
// frame-size-independent, and full-scale timing is covered by the scanout tb.
`default_nettype none
module revb_video_wait_tb;
    reg dot_clk = 0, clk = 0, reset_n = 0;
    reg [15:0] A = 16'h0000;
    reg [7:0]  D_in = 8'h00;
    reg        mreq_n = 1'b1, rd_n = 1'b1, wr_n = 1'b1;
    wire [7:0] D_out; wire D_oe, wait_od_n, hsync_n, vsync_n, active, pixel;

    revb_video_card_ttl #(
        .H_ACTIVE(8), .H_FP(2), .H_SYNC(2), .H_BP(2), .H_TOTAL(14),
        .V_ACTIVE(4), .V_FP(1), .V_SYNC(1), .V_BP(1), .V_TOTAL(7),
        .vw_limit(0), .V_FIT(0)) uut (
        .dot_clk(dot_clk), .clk(clk), .reset_n(reset_n),
        .A(A), .D_in(D_in), .mreq_n(mreq_n), .rd_n(rd_n), .wr_n(wr_n),
        .MODE0(1'b0), .MODE1(1'b0), .D_out(D_out), .D_oe(D_oe), .wait_od_n(wait_od_n),
        .hsync_n(hsync_n), .vsync_n(vsync_n), .active(active), .pixel(pixel));

    always #2 dot_clk = ~dot_clk;
    always #3 clk     = ~clk;

    wire cpu_acc = (mreq_n==0) && (wr_n==0 || rd_n==0) && (A >= 16'hD800);
    integer inv_err, land_err, held_cnt, k;

    always @(posedge dot_clk) if (reset_n)
        if (wait_od_n !== ~(cpu_acc & active)) inv_err = inv_err + 1;

    initial begin #200000; $display("REVB-VIDEO-WAIT: FAIL (watchdog)"); $finish; end

    task one_write(input [15:0] addr, input [7:0] val, input want_active); begin
        // position the launch: wait (bounded) for the requested region
        for (k = 0; k < 200 && (active != want_active); k = k + 1) @(posedge dot_clk);
        @(negedge clk); A = addr; D_in = val; mreq_n = 0; wr_n = 0;
        if (want_active) begin
            @(posedge dot_clk);                          // one dot with the access up
            if (wait_od_n === 1'b0) held_cnt = held_cnt + 1;   // must be held
        end
        // drive to a granted clk edge in blanking (bounded)
        for (k = 0; k < 400; k = k + 1) begin
            @(posedge clk); #0; if (wait_od_n === 1'b1 && !active) k = 1000;  // granted
        end
        @(posedge clk); @(negedge clk); mreq_n = 1; wr_n = 1; #1;
        if (uut.fb[addr - 16'hD800] !== val) begin
            land_err = land_err + 1;
            $display("  LAND ERR fb[%h]=%h exp %h", addr, uut.fb[addr-16'hD800], val);
        end
    end endtask

    integer j;
    initial begin
        inv_err = 0; land_err = 0; held_cnt = 0;
        for (j = 0; j < (32'h1_0000 - 16'hD800); j = j + 1) uut.fb[j] = 8'h00;
        @(negedge dot_clk); reset_n = 1;
        for (j = 0; j < 24; j = j + 1) begin
            one_write(16'hD800 + j*3,       (j*29 + 5)  & 8'hFF, 1'b1);   // active -> held
            one_write(16'hD800 + 256 + j*3, (j*53 + 17) & 8'hFF, 1'b0);   // blanking
        end
        $display("  active-writes=24 held=%0d, blank-writes=24, inv=%0d land=%0d",
                 held_cnt, inv_err, land_err);
        if (inv_err == 0 && land_err == 0 && held_cnt == 24)
             $display("REVB-VIDEO-WAIT: PASS");
        else $display("REVB-VIDEO-WAIT: FAIL");
        $finish;
    end
endmodule
`default_nettype wire
