// VJUGA rev B — Video card, CHIP-LEVEL twin (Phase B2 / TI.2).
//
// Models the real BOM at 74xx granularity so the oracle gates exercise the actual
// hardware behaviour and the structure maps to LVS (TI.3). Contents:
//   * framebuffer SRAM (AS6C1008, D2.3) — 0xD800..0xFFFF window, shared CPU/scanout
//   * VGA 640x480@60 sync/blank timing chain adopted from mengstr/TTL640x480
//     (MIT (c) 2019 SmallRoomLabs; the '393 counters + NAND-decode topology) — the
//     numbers come from video-timing.json (kept in sync by revb_video_timing_check.py)
//   * scanout address path ('157 mux + counters) and pixel shifter ('166)
//   * mono resistor-DAC drive (R=G=B = pixel)
//   * GAL22V10 contention: scanout has priority; a CPU framebuffer access during the
//     active region is held off with open-drain WAIT_N and serviced in blanking (D2.5)
//
// Two clock domains, as on the real card: dot_clk = 25.175 MHz scanout; clk = CPU bus
// clock (few MHz). Drop-in bus-compatible with revb_video_card (same CPU-facing ports)
// plus the scanout outputs + wait_od_n; also keeps the boot-oracle framebuffer dump so
// it can substitute the behavioural card in revb_boot_check.sh.
`default_nettype none
module revb_video_card_ttl #(
    // Timing (MUST equal video-timing.json — revb_video_timing_check.py enforces it).
    parameter integer H_ACTIVE = 640, H_FP = 16, H_SYNC = 96, H_BP = 48, H_TOTAL = 800,
    parameter integer V_ACTIVE = 480, V_FP = 10, V_SYNC = 2,  V_BP = 33, V_TOTAL = 525,
    // Framebuffer.
    parameter [15:0]  FB_BASE  = 16'hD800,
    parameter integer FB_COLS  = 40,   // bytes per row
    parameter integer FB_ROWS  = 241,
    // Vertical fit for the 482>480 overhang: 0 = crop bottom, 1 = letterbox (D2.4;
    // frozen by the scanout checker at TI.2).
    parameter integer V_FIT    = 0,
    // Boot-oracle dump (same contract as the behavioural card).
    parameter integer vw_limit  = 0,
    parameter dump_file = "revb_vram_ttl.bin"
) (
    input  wire        dot_clk,     // 25.175 MHz scanout clock
    input  wire        clk,         // CPU bus clock
    input  wire        reset_n,
    // CPU bus face (identical to revb_video_card)
    input  wire [15:0] A,
    input  wire [7:0]  D_in,
    input  wire        mreq_n, rd_n, wr_n,
    input  wire        MODE0, MODE1,
    output wire [7:0]  D_out,
    output wire        D_oe,
    output wire        wait_od_n,   // open-drain /WAIT (1 = released; 0 = hold CPU)
    // VGA scanout face (to the DSUB via the DAC)
    output wire        hsync_n,
    output wire        vsync_n,
    output wire        active,      // h_active & v_active (RGB valid)
    output wire        pixel,       // 1-bit mono video (R=G=B through the DAC)
    output wire        frame_tick   // 60 Hz frame pulse to the bus (keyboard-scan anchor)
);
    localparam integer H_SYNC_START = H_ACTIVE + H_FP;                 // 656
    localparam integer H_SYNC_END   = H_ACTIVE + H_FP + H_SYNC;        // 752
    localparam integer V_SYNC_START = V_ACTIVE + V_FP;                 // 490
    localparam integer V_SYNC_END   = V_ACTIVE + V_FP + V_SYNC;        // 492
    localparam integer FB_SPAN      = 32'h1_0000 - FB_BASE;            // 0x2800
    localparam integer FB_BYTES     = FB_COLS * FB_ROWS;               // 9640

    // ---- framebuffer SRAM (AS6C1008; only the low window is modelled) ----
    reg [7:0] fb [0:FB_SPAN-1];
    integer ii;
    initial for (ii = 0; ii < FB_SPAN; ii = ii + 1) fb[ii] = 8'h00;

    // ================= scanout domain (dot_clk) =================
    // '393 dot + line counters.
    reg [11:0] hcount = 0;
    reg [11:0] vcount = 0;
    always @(posedge dot_clk or negedge reset_n) begin
        if (!reset_n) begin
            hcount <= 0; vcount <= 0;
        end else if (hcount == H_TOTAL - 1) begin
            hcount <= 0;
            vcount <= (vcount == V_TOTAL - 1) ? 12'd0 : vcount + 12'd1;
        end else begin
            hcount <= hcount + 12'd1;
        end
    end

    wire h_active = (hcount < H_ACTIVE);
    wire v_active = (vcount < V_ACTIVE);
    assign active  = h_active & v_active;
    // FRAME_TICK: one dot-wide pulse at the start of each frame (60 Hz) — the firmware's
    // keyboard-scan timing anchor. Derived from the vsync counter (start of line 0).
    assign frame_tick = (hcount == 0) && (vcount == 0);
    // NAND-decode sync windows (active-low, negative polarity per the contract).
    assign hsync_n = ~((hcount >= H_SYNC_START) && (hcount < H_SYNC_END));
    assign vsync_n = ~((vcount >= V_SYNC_START) && (vcount < V_SYNC_END));

    // scanout source address: pixel-double x2 both axes.
    wire [11:0] src_col = hcount[11:1];                 // 0..319 during h_active
    wire [11:0] byte_col = src_col / 8;                 // 0..39
    wire [2:0]  bit_idx  = 3'd7 - src_col[2:0];         // MSB-first
    // vertical fit: crop (V_FIT=0) shows source rows 0..239; letterbox (V_FIT=1)
    // shifts by one doubled line so the 240th source row's pair straddles the edges.
    wire [11:0] src_row = (V_FIT == 0) ? vcount[11:1]
                                       : (vcount + 12'd1) >> 1;
    wire [31:0] fb_index = src_row * FB_COLS + byte_col;
    wire        in_fb    = (fb_index < FB_BYTES);

    // '157 scanout-address mux feeds the SRAM read; '166 loads the fetched byte and
    // shifts one bit per 2 dots. Modelled as a direct fetch (observable = the bit).
    reg [7:0] scan_byte;
    always @* scan_byte = in_fb ? fb[fb_index] : 8'h00;
    assign pixel = active & in_fb & scan_byte[bit_idx];

    // ================= CPU domain (clk) =================
    wire [1:0] mode      = {MODE1, MODE0};
    wire       fb_is_ram = (mode == 2'b00) || (mode == 2'b11);   // facts overlay table
    wire       in_window = (A >= FB_BASE) && fb_is_ram;
    wire       cpu_rd    = (mreq_n == 1'b0) && (rd_n == 1'b0) && in_window;
    wire       cpu_wr    = (mreq_n == 1'b0) && (wr_n == 1'b0) && in_window;
    wire       cpu_acc   = cpu_rd | cpu_wr;

    // GAL contention (D2.5): scanout owns the SRAM during the active region, so a CPU
    // framebuffer access there is held (WAIT_N low) until blanking. Open-drain: release
    // = high-Z (modelled as 1); assert = 0.
    assign wait_od_n = ~(cpu_acc & active);
    wire   cpu_grant = cpu_acc & ~active;    // serviced only in blanking

    reg [7:0] D_out_r;
    always @* D_out_r = fb[A - FB_BASE];
    assign D_out = D_out_r;
    assign D_oe  = cpu_rd & ~active;         // drive only when actually granted

    // write + boot-oracle dump (edge-gated, one store per granted CPU write)
    reg        prev_wr = 1'b0;
    reg [31:0] vw = 0;
    reg        dumped = 0;
    integer fo, i;
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            vw <= 0; prev_wr <= 1'b0; dumped <= 0;
        end else begin
            if (cpu_wr && cpu_grant && !prev_wr) begin
                fb[A - FB_BASE] <= D_in;
                vw <= vw + 1;
            end
            prev_wr <= (cpu_wr && cpu_grant);
            if (vw_limit > 0 && vw == vw_limit && !dumped) begin
                dumped <= 1;
                fo = $fopen(dump_file, "wb");
                for (i = 0; i < FB_BYTES; i = i + 1) $fwrite(fo, "%c", fb[i]);
                $fclose(fo);
            end
        end
    end
endmodule
`default_nettype wire
