// VJUGA rev B — Memory card.
// ROM (27C256 image, low 16 KiB defined) + main SRAM + decode. SRAM replaces the
// rev A DRAM+U24 chapter (build-plan C1). Owns everything EXCEPT the framebuffer
// window 0xD800-0xFFFF, which the Video card owns (bus contract). Decode/overlay
// logic reused verbatim from vjuga_juku_top.v (memory-technology-independent),
// including the real D6 К556РТ4 (decode_prom) / D8 К155РЕ3 (re3_prom) path so
// Mode B still self-tests those chips.
`default_nettype none
module revb_mem_card #(
    parameter rom_file    = "ekta37_z80.hex",
    parameter DECODE_MODE = 0    // 0 = Mode B (D6 РТ4), 1 = Mode A (GAL-internal)
) (
    input  wire        clk,
    input  wire        reset_n,
    input  wire [15:0] A,
    input  wire [7:0]  D_in,
    input  wire        mreq_n, rd_n, wr_n,
    input  wire        MODE0, MODE1,   // from I/O card (backplane defaults to 0)
    output reg  [7:0]  D_out,
    output wire        D_oe
);
    localparam [15:0] FB_BASE = 16'hD800;   // framebuffer window base (Video card owns)

    // ---- ROM image (Z80-patched firmware, low 16 KiB) ----
    reg [7:0] rom [0:16383];
    initial $readmemh(rom_file, rom);

    // ---- main SRAM (full 64K array; only <0xD800 RAM is used here) ----
    reg [7:0] sram [0:65535];
    integer k;
    initial for (k = 0; k < 65536; k = k + 1) sram[k] = 8'h00;

    wire [1:0] mode = {MODE1, MODE0};

    // ---- decode: real D6 (Mode B) or coarse GAL-internal (Mode A) ----
    tri1 d6_rom_n, d6_ram_n, d6_rev, d6_roe;
    decode_prom U_D6 (.a({1'b0, ~MODE1, ~MODE0, A[11], A[12], A[13], A[14], A[15]}),
                      .v_en_n(1'b0),
                      .rom_n(d6_rom_n), .ram_n(d6_ram_n), .rev(d6_rev), .roe_n(d6_roe));
    wire is_rom_promB = d6_rom_n;              // ~D0 provisional correction, matches vjuga
    wire is_rom_intA  = (A[15:14] == 2'b00);
    wire is_rom       = (DECODE_MODE == 1) ? is_rom_intA : is_rom_promB;
    wire rom_sel_n    = ~is_rom;
    tri1 [7:0] d8_d;
    re3_prom U_D8 (.a(A[15:11]), .e_n(rom_sel_n), .d(d8_d));   // observed only (chip test)

    wire is_cart = (mode == 2'b10) && (A >= 16'h4000 && A <= 16'hBFFF);
    // framebuffer window is RAM (Video card's) in modes 0 and 3; ROM overlay in 1/2.
    wire fb_is_ram = (mode == 2'b00) || (mode == 2'b11);

    function [13:0] rom_idx(input [15:0] a);
        rom_idx = (mode == 2'b00) ? a[13:0] : (14'h1800 + (a - FB_BASE));
    endfunction

    // This card owns every memory read the Video card does not (i.e. not a RAM
    // access inside the framebuffer window).
    wire video_owns_rd = (A >= FB_BASE) && fb_is_ram;
    assign D_oe = (mreq_n == 1'b0) && (rd_n == 1'b0) && !video_owns_rd;

    always @* begin
        if (is_rom)       D_out = rom[rom_idx(A)];
        else if (is_cart) D_out = 8'hFF;          // empty cartridge
        else              D_out = sram[A];
    end

    // Writes: RAM only, and never into the Video card's window.
    always @(posedge clk) begin
        if (reset_n && mreq_n == 1'b0 && wr_n == 1'b0
            && !(is_rom || is_cart) && (A < FB_BASE))
            sram[A] <= D_in;
    end
endmodule
`default_nettype wire
