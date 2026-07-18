// VJUGA rev B — address-generator validation (D2.7). Drives the row-base accumulator with
// scanout raster timing and asserts scan_addr == src_row*40 + byte_col at every active
// byte across several source rows. Proves the counter/register hardware reproduces the
// stride-40 framebuffer address the behavioral twin computed directly. Small raster
// (640 active dots = 40 byte-cols, a few rows) keeps it fast; correctness is scale-free.
`default_nettype none
module revb_video_addrgen_tb;
    localparam integer FB_COLS = 40;
    localparam integer H_ACTIVE = 640, H_TOTAL = 672;   // 640/16 = 40 byte cols
    localparam integer V_ACTIVE = 8,   V_TOTAL = 10;    // 4 source rows (v-doubled)

    reg dot_clk = 0, reset_n = 0;
    reg [11:0] hcount = 0, vcount = 0;
    wire [13:0] scan_addr;

    wire line_end   = (hcount == H_TOTAL-1);
    wire frame_last = (vcount == V_TOTAL-1);
    wire h_active   = (hcount < H_ACTIVE);
    wire v_active   = (vcount < V_ACTIVE);
    wire active     = h_active & v_active;
    // tick on the LAST dot of each byte column so scan_addr steps as hcount crosses into
    // the next column (registered +1 lands aligned with the fetch window)
    wire byte_tick  = active && (hcount[3:0] == 4'd15);

    revb_video_addrgen #(.FB_COLS(FB_COLS)) uut (
        .dot_clk(dot_clk), .reset_n(reset_n),
        .line_end(line_end), .frame_last(frame_last),
        .vcount0(vcount[0]), .byte_tick(byte_tick),
        .scan_addr(scan_addr));

    always #1 dot_clk = ~dot_clk;

    integer errors, checks;
    // raster position counter (mirrors the '393 chain)
    always @(posedge dot_clk) if (reset_n) begin
        if (hcount == H_TOTAL-1) begin
            hcount <= 0;
            vcount <= (vcount == V_TOTAL-1) ? 12'd0 : vcount + 12'd1;
        end else hcount <= hcount + 12'd1;
    end

    integer exp;
    initial begin
        errors = 0; checks = 0;
        @(negedge dot_clk); reset_n = 1;
        // two full frames (let the accumulator settle + repeat)
        repeat (2*H_TOTAL*V_TOTAL) begin
            @(posedge dot_clk); #0;
            if (active) begin
                exp = (vcount/2)*FB_COLS + (hcount>>4);   // src_row*40 + byte_col
                checks = checks + 1;
                if (scan_addr !== exp[13:0]) begin
                    errors = errors + 1;
                    if (errors <= 6)
                        $display("  ADDR MISMATCH @(h=%0d v=%0d): got %0d exp %0d",
                                 hcount, vcount, scan_addr, exp);
                end
            end
        end
        $display("  active bytes checked=%0d, errors=%0d", checks, errors);
        if (errors == 0) $display("REVB-VIDEO-ADDRGEN: PASS");
        else             $display("REVB-VIDEO-ADDRGEN: FAIL");
        $finish;
    end
endmodule
`default_nettype wire
