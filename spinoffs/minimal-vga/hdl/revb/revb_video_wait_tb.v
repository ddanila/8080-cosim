// VJUGA rev B — Video /WAIT contention testbench (TI.2 gate c; D2.5).
// Scanout owns the framebuffer during phases 12..15 of every 16-dot byte group;
// a colliding CPU request must be held off and then land when FETCH falls.
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
        .H_ACTIVE(16), .H_FP(4), .H_SYNC(4), .H_BP(8), .H_TOTAL(32),
        .V_ACTIVE(4), .V_FP(1), .V_SYNC(1), .V_BP(1), .V_TOTAL(7),
        .vw_limit(0), .V_FIT(0)) uut (
        .dot_clk(dot_clk), .clk(clk), .reset_n(reset_n),
        .A(A), .D_in(D_in), .mreq_n(mreq_n), .rd_n(rd_n), .wr_n(wr_n),
        .MODE0(1'b0), .MODE1(1'b0), .D_out(D_out), .D_oe(D_oe), .wait_od_n(wait_od_n),
        .hsync_n(hsync_n), .vsync_n(vsync_n), .active(active), .pixel(pixel));

    always #2 dot_clk = ~dot_clk;
    always #3 clk     = ~clk;

    wire cpu_acc = (mreq_n==0) && (wr_n==0 || rd_n==0) && (A >= 16'hD800);
    integer land_err, held_cnt, k;
    always @(negedge dot_clk) if (reset_n && cpu_acc) begin
        if (wait_od_n !== ~(uut.hcount[3:2] == 2'b11)) begin
            land_err = land_err + 1;
            $display("  WAIT PHASE ERR h=%0d wait=%b", uut.hcount, wait_od_n);
        end
    end

    initial begin #200000; $display("REVB-VIDEO-WAIT: FAIL (watchdog)"); $finish; end

    // Launch a write at a chosen phase, obey WAIT like a real CPU, then verify it landed.
    task one_write(input [15:0] addr, input [7:0] val, input want_active); begin
        for (k = 0; k < 200 && (active != want_active); k = k + 1) @(posedge dot_clk);
        @(negedge clk); A = addr; D_in = val; mreq_n = 0; wr_n = 0;
        for (k = 0; k < 20 && wait_od_n === 1'b0; k = k + 1) begin
            @(posedge clk); held_cnt = held_cnt + 1;
        end
        repeat (2) @(posedge clk);
        @(negedge clk); mreq_n = 1; wr_n = 1; #1;
        if (uut.fb[addr - 16'hD800] !== val) begin
            land_err = land_err + 1;
            $display("  LAND ERR fb[%h]=%h exp %h", addr, uut.fb[addr-16'hD800], val);
        end
    end endtask

    task forced_collision(input [15:0] addr, input [7:0] val); begin
        while (uut.hcount[3:0] != 4'd12) @(negedge dot_clk);
        A=addr; D_in=val; mreq_n=0; wr_n=0; #0;
        if (wait_od_n !== 1'b0) begin
            land_err=land_err+1; $display("  forced collision did not assert WAIT");
        end else held_cnt=held_cnt+1;
        while (wait_od_n === 1'b0) @(negedge dot_clk);
        repeat (2) @(posedge clk);
        @(negedge clk); mreq_n=1; wr_n=1; #1;
        if (uut.fb[addr-16'hD800] !== val) begin
            land_err=land_err+1; $display("  forced collision write did not land");
        end
    end endtask

    integer j;
    initial begin
        land_err = 0; held_cnt = 0;
        for (j = 0; j < (32'h1_0000 - 16'hD800); j = j + 1) uut.fb[j] = 8'h00;
        @(negedge dot_clk); reset_n = 1;
        forced_collision(16'hD9F0,8'hA5);
        // sweep writes across active and blanking phases; EVERY write must land.
        for (j = 0; j < 40; j = j + 1) begin
            one_write(16'hD800 + j*3,       (j*29 + 5)  & 8'hFF, 1'b1);   // active phase
            one_write(16'hD800 + 256 + j*3, (j*53 + 17) & 8'hFF, 1'b0);   // blanking phase
        end
        $display("  writes=81, steal observations=%0d, land errors=%0d", held_cnt, land_err);
        // load-bearing: NO write is ever lost across any phase (cycle-steal correctness).
        if (land_err == 0 && held_cnt > 0) $display("REVB-VIDEO-WAIT: PASS");
        else               $display("REVB-VIDEO-WAIT: FAIL");
        $finish;
    end
endmodule
`default_nettype wire
