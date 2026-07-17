// VJUGA rev B — Video card (B0 scope: framebuffer memory + boot oracle dump).
// Owns the framebuffer window 0xD800-0xFFFF as on-card SRAM (build-plan C1/C4/C5).
// VGA scanout timing and /WAIT generation are Phase B2 work; here the card just
// serves the framebuffer to the CPU and, for the boot oracle, counts video writes
// (exactly as cosim's g_vw: any landed CPU write with A>=0xD800) and dumps the
// 40x241 = 9640-byte image so sim/revb_boot_check.sh can cmp it against cosim.
`default_nettype none
module revb_video_card #(
    parameter vw_limit  = 6000,
    parameter dump_file = "revb_vram.bin"
) (
    input  wire        clk,
    input  wire        reset_n,
    input  wire [15:0] A,
    input  wire [7:0]  D_in,
    input  wire        mreq_n, rd_n, wr_n,
    input  wire        MODE0, MODE1,
    output wire [7:0]  D_out,
    output wire        D_oe
);
    localparam [15:0]  FB_BASE  = 16'hD800;         // canonical framebuffer base (facts file)
    localparam integer FB_SPAN  = 32'h1_0000 - 16'hD800;  // 0x2800 = 0xD800..0xFFFF (32-bit lhs: no truncation)
    localparam integer FB_BYTES = 40*241;           // 9640 dumped bytes

    reg [7:0] fb [0:FB_SPAN-1];
    integer k;
    initial for (k = 0; k < FB_SPAN; k = k + 1) fb[k] = 8'h00;

    wire [1:0] mode = {MODE1, MODE0};
    wire fb_is_ram  = (mode == 2'b00) || (mode == 2'b11);
    wire in_window  = (A >= FB_BASE) && fb_is_ram;

    // NB: a variable-index continuous `assign D_out = fb[A-FB_BASE]` corrupts the
    // array under iverilog (same quirk vjuga_juku_top.v documents for the РУ5
    // video read). Read procedurally instead.
    reg [7:0] D_out_r;
    always @* D_out_r = fb[A - FB_BASE];
    assign D_out = D_out_r;
    assign D_oe  = (mreq_n == 1'b0) && (rd_n == 1'b0) && in_window;

    wire write_now = (mreq_n == 1'b0) && (wr_n == 1'b0) && in_window;
    reg  prev_write = 1'b0;
    reg [31:0] vw = 0;
    reg dumped = 0;

    integer fo, i;
    always @(posedge clk) begin
        if (!reset_n) begin
            vw <= 0; prev_write <= 1'b0; dumped <= 0;
        end else begin
            // Edge-gate: one count + one store per CPU write cycle.
            if (write_now && !prev_write) begin
                fb[A - FB_BASE] <= D_in;
                vw <= vw + 1;
            end
            prev_write <= write_now;

            if (vw_limit > 0 && vw == vw_limit && !dumped) begin
                dumped <= 1;
                fo = $fopen(dump_file, "wb");
                for (i = 0; i < FB_BYTES; i = i + 1) $fwrite(fo, "%c", fb[i]);
                $fclose(fo);
                $display("REVB-V: framebuffer dumped after %0d video writes (mode=%0d)", vw_limit, mode);
                $finish;
            end
        end
    end
endmodule
`default_nettype wire
