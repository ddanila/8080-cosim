// VJUGA rev B — Video card structural LVS netlist (TI.3). Empty-bodied modules for the
// LVS'd logic ICs: the three decode/control GAL22V10s and the framebuffer SRAM. The
// standard 74xx (counters/mux/register/shifter/buffer/adder) are verified by D1.18
// completeness, not full LVS (D1.22), exactly as the io card's discrete parts. Port
// names = the CHIP_TYPES net names. Full ranges are vectors (HC[9:0], SA[13:0], like the
// mem SRAM's A[15:0]); the A11..A15 subset stays SCALAR (a [15:11] vector would
// canonicalize by position to A0..A4 and mis-map — the mem/io lesson).
`default_nettype none

module gal22v10_hdec_lvs(
    input  wire        DOTCLK,
    input  wire [9:0]  HC,      // HC0..HC9
    output wire        H_END, HSYNC_N, H_BLANK, BYTE_TICK, FI_LOAD_N, SR_LOAD_N, SR_INH
);
endmodule

module gal22v10_vdec_lvs(
    input  wire        H_BLANK, H_END,
    input  wire [9:0]  VC,      // VC0..VC9
    output wire        V_END, VSYNC_N, ACTIVE, FRAME_TOP_N, FRAME_TICK, RB_CLK
);
endmodule

module gal22v10_ctrl_lvs(
    input  wire        DOTCLK,
    input  wire        A11, A12, A13, A14, A15,   // scalar subset (position trap)
    input  wire        MREQ_N, RD_N, WR_N, MODE0, MODE1, ACTIVE,
    output wire        WAIT_N, MUX_SEL, D245_DIR, D245_OE, FB_CE_N, FB_WE_N, FB_OE_N
);
endmodule

module sram_fb_lvs(
    input  wire [13:0] SA,      // SA0..SA13 scanout/CPU address
    inout  wire [7:0]  FD,      // framebuffer data
    input  wire        FB_CE_N, FB_OE_N, FB_WE_N
);
endmodule

module revb_video_lvs_top;
    wire DOTCLK;
    wire [9:0] HC, VC;
    wire H_END, HSYNC_N, H_BLANK, BYTE_TICK, FI_LOAD_N, SR_LOAD_N, SR_INH;
    wire V_END, VSYNC_N, ACTIVE, FRAME_TOP_N, FRAME_TICK, RB_CLK;
    wire A11, A12, A13, A14, A15, MREQ_N, RD_N, WR_N, MODE0, MODE1;
    wire WAIT_N, MUX_SEL, D245_DIR, D245_OE, FB_CE_N, FB_WE_N, FB_OE_N;
    wire [13:0] SA;
    wire [7:0]  FD;

    gal22v10_hdec_lvs U_HDEC(
        .DOTCLK(DOTCLK), .HC(HC),
        .H_END(H_END), .HSYNC_N(HSYNC_N), .H_BLANK(H_BLANK), .BYTE_TICK(BYTE_TICK),
        .FI_LOAD_N(FI_LOAD_N), .SR_LOAD_N(SR_LOAD_N), .SR_INH(SR_INH));

    gal22v10_vdec_lvs U_VDEC(
        .H_BLANK(H_BLANK), .H_END(H_END), .VC(VC),
        .V_END(V_END), .VSYNC_N(VSYNC_N), .ACTIVE(ACTIVE), .FRAME_TOP_N(FRAME_TOP_N),
        .FRAME_TICK(FRAME_TICK), .RB_CLK(RB_CLK));

    gal22v10_ctrl_lvs U_CTRL(
        .DOTCLK(DOTCLK), .A11(A11), .A12(A12), .A13(A13), .A14(A14), .A15(A15),
        .MREQ_N(MREQ_N), .RD_N(RD_N), .WR_N(WR_N), .MODE0(MODE0), .MODE1(MODE1),
        .ACTIVE(ACTIVE), .WAIT_N(WAIT_N), .MUX_SEL(MUX_SEL), .D245_DIR(D245_DIR),
        .D245_OE(D245_OE), .FB_CE_N(FB_CE_N), .FB_WE_N(FB_WE_N), .FB_OE_N(FB_OE_N));

    sram_fb_lvs U_FB(
        .SA(SA), .FD(FD), .FB_CE_N(FB_CE_N), .FB_OE_N(FB_OE_N), .FB_WE_N(FB_WE_N));
endmodule
`default_nettype wire
