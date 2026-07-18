// VJUGA rev B — Video scanout self-checking testbench (TI.2 gate b).
// Loads a deterministic pattern into the framebuffer, runs one full VGA frame on the
// dot clock, and asserts: (1) hsync/vsync pulse start + width match the timing contract;
// (2) the active-region pixel stream equals the framebuffer bit at every sampled dot
// (pixel-doubled, MSB-first) — i.e. the scanout faithfully renders the framebuffer.
`default_nettype none
module revb_video_scanout_tb;
    localparam integer H_ACTIVE=640, H_FP=16, H_SYNC=96, H_BP=48, H_TOTAL=800;
    localparam integer V_ACTIVE=480, V_FP=10, V_SYNC=2,  V_BP=33, V_TOTAL=525;
    localparam integer FB_COLS=40, FB_ROWS=241;

    reg dot_clk = 0, clk = 0, reset_n = 0;
    wire hsync_n, vsync_n, active, pixel, wait_od_n, dvoe;
    wire [7:0] dvo;

    revb_video_card_ttl #(.vw_limit(0), .V_FIT(0)) uut (
        .dot_clk(dot_clk), .clk(clk), .reset_n(reset_n),
        .A(16'h0000), .D_in(8'h00), .mreq_n(1'b1), .rd_n(1'b1), .wr_n(1'b1),
        .MODE0(1'b0), .MODE1(1'b0), .D_out(dvo), .D_oe(dvoe), .wait_od_n(wait_od_n),
        .hsync_n(hsync_n), .vsync_n(vsync_n), .active(active), .pixel(pixel));

    always #1 dot_clk = ~dot_clk;

    integer i, errors;
    // deterministic pattern: fb[k] = (k*37 + 11) & 0xFF (well-mixed, both bit values)
    function [7:0] pat; input integer k; pat = (k*37 + 11) & 8'hFF; endfunction

    // expected pixel at (hc, vc) for the crop fit, MSB-first, pixel-doubled x2.
    function expected_pixel; input integer hc; input integer vc; integer sc, bc, bidx, sr, idx; begin
        if (hc >= H_ACTIVE || vc >= V_ACTIVE) expected_pixel = 1'b0;
        else begin
            sc = hc/2; bc = sc/8; bidx = 7 - (sc%8); sr = vc/2;
            idx = sr*FB_COLS + bc;
            expected_pixel = (idx < FB_COLS*FB_ROWS) ? pat(idx) >> bidx & 1'b1 : 1'b0;
        end
    end endfunction

    // sync-pulse measurement over the frame
    integer hs_start, hs_len, vs_start, vs_len, hc, vc, sampled;
    initial begin
        for (i = 0; i < (32'h1_0000 - 16'hD800); i = i + 1) uut.fb[i] = 8'h00;
        for (i = 0; i < FB_COLS*FB_ROWS; i = i + 1) uut.fb[i] = pat(i);
        errors = 0; sampled = 0;
        hs_start = -1; hs_len = 0; vs_start = -1; vs_len = 0;
        @(negedge dot_clk); reset_n = 1;

        // run one full frame, sampling
        for (vc = 0; vc < V_TOTAL; vc = vc + 1) begin
            for (hc = 0; hc < H_TOTAL; hc = hc + 1) begin
                @(posedge dot_clk); #0;
                // pixel fidelity: sample a sparse lattice across the active region
                if ((hc % 17 == 0) && (vc % 13 == 0)) begin
                    sampled = sampled + 1;
                    if (pixel !== expected_pixel(hc, vc)) begin
                        errors = errors + 1;
                        if (errors <= 5)
                            $display("  PIXEL MISMATCH @(h=%0d,v=%0d): got %b exp %b",
                                     hc, vc, pixel, expected_pixel(hc, vc));
                    end
                end
                // measure hsync on the first line
                if (vc == 0) begin
                    if (!hsync_n && hs_start < 0) hs_start = hc;
                    if (!hsync_n) hs_len = hs_len + 1;
                end
            end
            // measure vsync (first hcount of each line)
            if (!vsync_n && vs_start < 0) vs_start = vc;
            if (!vsync_n) vs_len = vs_len + 1;
        end

        $display("  hsync: start=%0d (exp %0d) len=%0d (exp %0d)",
                 hs_start, H_ACTIVE+H_FP, hs_len, H_SYNC);
        $display("  vsync: start=%0d (exp %0d) len=%0d (exp %0d)",
                 vs_start, V_ACTIVE+V_FP, vs_len, V_SYNC);
        if (hs_start !== H_ACTIVE+H_FP || hs_len !== H_SYNC) errors = errors + 1;
        if (vs_start !== V_ACTIVE+V_FP || vs_len !== V_SYNC) errors = errors + 1;

        $display("  pixels sampled=%0d, errors=%0d", sampled, errors);
        if (errors == 0) $display("REVB-VIDEO-SCANOUT: PASS");
        else             $display("REVB-VIDEO-SCANOUT: FAIL (%0d)", errors);
        $finish;
    end
endmodule
`default_nettype wire
