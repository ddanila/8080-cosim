`timescale 1ns/1ns
module u24_dram_timing_tb;
    reg clk = 0;
    always #125 clk = ~clk; // owner-selected 4 MHz Z80 clock

    reg reset_n = 0;
    reg ram_ce_n = 1, mem_rd_n = 1, mem_wr_n = 1;
    reg rfsh_obs_n = 1, video_req = 0, decode_wait_n = 1;
    reg [3:0] refresh_q = 0;
    wire ras_n, cas_n, dram_we_n, addrmux_sel, cpu_wait_n;
    wire video_ack, refresh_tick, state0, state1, state2;

    u24_dram_timing dut (
        .clk(clk), .reset_n(reset_n), .ram_ce_n(ram_ce_n),
        .mem_rd_n(mem_rd_n), .mem_wr_n(mem_wr_n),
        .rfsh_obs_n(rfsh_obs_n), .video_req(video_req),
        .decode_wait_n(decode_wait_n),
        .refresh_q0(refresh_q[0]), .refresh_q1(refresh_q[1]),
        .refresh_q2(refresh_q[2]), .refresh_q3(refresh_q[3]),
        .ras_n(ras_n), .cas_n(cas_n), .dram_we_n(dram_we_n),
        .addrmux_sel(addrmux_sel), .cpu_wait_n(cpu_wait_n),
        .video_ack(video_ack), .refresh_tick(refresh_tick),
        .state0(state0), .state1(state1), .state2(state2)
    );

    integer ras_fall, ras_rise, cas_fall, cas_rise;
    always @(negedge ras_n) ras_fall = $time;
    always @(posedge ras_n) if (reset_n) ras_rise = $time;
    always @(negedge cas_n) cas_fall = $time;
    always @(posedge cas_n) if (reset_n) cas_rise = $time;

    task step; begin @(posedge clk); #1; end endtask
    task check(input condition, input [8*96-1:0] message); begin
        if (!condition) begin
            $display("U24-DRAM-TIMING: FAIL: %0s at %0t ns", message, $time);
            $finish_and_return(1);
        end
    end endtask

    initial begin
        repeat (2) step;
        reset_n = 1;
        step;
        check(ras_n && cas_n && dram_we_n && cpu_wait_n,
              "reset/idle outputs are not safe");

        // CPU read: ROW setup, RAS, COL setup, two CAS states, CAS-before-RAS
        // recovery, DONE. WAIT spans the whole access and releases at DONE.
        @(negedge clk); ram_ce_n = 0; mem_rd_n = 0;
        #1; check(!cpu_wait_n, "CPU read did not assert WAIT immediately");
        step; check(ras_n && cas_n && !addrmux_sel, "ROW setup phase drifted");
        step; check(!ras_n && cas_n && !addrmux_sel, "RAS phase drifted");
        step; check(!ras_n && cas_n && addrmux_sel, "column setup phase drifted");
        step; check(!ras_n && !cas_n && addrmux_sel && dram_we_n,
                    "read CAS phase drifted");
        step; check(!ras_n && !cas_n, "read CAS hold phase drifted");
        step; check(!ras_n && cas_n, "CAS did not recover before RAS");
        step; check(ras_n && cas_n && cpu_wait_n, "read DONE did not release WAIT");
        $display("U24 read timing ns: RAS fall=%0d CAS fall=%0d CAS rise=%0d RAS rise=%0d",
                 ras_fall, cas_fall, cas_rise, ras_rise);
        check(cas_fall - ras_fall >= 45, "RAS-to-CAS delay violates MK4564-12");
        check(cas_rise - cas_fall >= 75, "CAS pulse violates MK4564-12");
        check(ras_rise - ras_fall >= 120, "RAS pulse violates MK4564-12");
        check(ras_rise - cas_rise >= 75, "RAS hold after CAS violates MK4564-12");
        @(negedge clk); ram_ce_n = 1; mem_rd_n = 1;
        step;

        // CPU write: WE becomes active in the column-setup phase, a full clock
        // before CAS, and returns inactive before RAS rises.
        @(negedge clk); ram_ce_n = 0; mem_wr_n = 0;
        step; step;
        step; check(!dram_we_n && cas_n, "write setup is not early-write safe");
        step; check(!dram_we_n && !cas_n, "write CAS phase lost WE");
        step; check(!dram_we_n, "write hold phase lost WE");
        step; check(dram_we_n && cas_n && !ras_n, "WE did not recover before RAS");
        step; check(ras_n && cpu_wait_n, "write DONE did not release WAIT");
        @(negedge clk); ram_ce_n = 1; mem_wr_n = 1;
        step;

        // Refresh is a RAS-only cycle. The tick doubles as the registered
        // refresh-client flag and no CPU wait is asserted.
        @(negedge clk); rfsh_obs_n = 0; refresh_q = 4'ha;
        step; check(refresh_tick && cpu_wait_n, "refresh was not accepted");
        step; check(!ras_n && cas_n, "refresh did not assert RAS only");
        step; check(!ras_n && cas_n, "refresh recovery lost RAS hold");
        step; check(ras_n && refresh_tick, "refresh DONE drifted");
        @(negedge clk); rfsh_obs_n = 1;
        step; check(!refresh_tick, "refresh flag did not clear");

        // A CPU request can arrive while refresh owns the sequencer. It must
        // remain stalled through refresh DONE, then receive a complete CPU
        // row/column cycle before WAIT is released.
        @(negedge clk); rfsh_obs_n = 0;
        step; check(refresh_tick, "collision refresh was not accepted");
        @(negedge clk); rfsh_obs_n = 1; ram_ce_n = 0; mem_rd_n = 0;
        #1; check(!cpu_wait_n, "CPU/refresh collision did not assert WAIT");
        repeat (3) begin
            step; check(!cpu_wait_n, "refresh DONE released an unserved CPU request");
        end
        step; check(!cpu_wait_n && !refresh_tick,
                    "pending CPU request was lost after refresh");
        repeat (7) step;
        check(cpu_wait_n && ras_n && cas_n,
              "colliding CPU request did not complete before WAIT release");
        @(negedge clk); ram_ce_n = 1; mem_rd_n = 1;
        step;

        // Video uses the full read cycle, acknowledges its registered client,
        // never asserts CPU WAIT, and cannot activate WE.
        @(negedge clk); video_req = 1;
        step; check(video_ack && cpu_wait_n, "video request was not accepted");
        repeat (3) step;
        check(!cas_n && dram_we_n && cpu_wait_n, "video CAS phase is unsafe");
        repeat (3) step;
        @(negedge clk); video_req = 0;
        step; check(!video_ack, "video acknowledgement did not clear");

        decode_wait_n = 0; #1;
        check(!cpu_wait_n, "decode wait input does not dominate");
        decode_wait_n = 1; #1;
        check(cpu_wait_n, "decode wait release does not propagate");

        $display("U24-DRAM-TIMING: PASS: 4 MHz FSM meets vendored MK4564-12 minima; CPU read/write, RAS-only refresh, collision handling, and video arbitration guarded");
        $finish;
    end
endmodule
