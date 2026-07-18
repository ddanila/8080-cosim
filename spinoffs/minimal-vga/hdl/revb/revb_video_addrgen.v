// VJUGA rev B — Video scanout address generator (D2.7 option a, row-base accumulator).
// The framebuffer is stride-40 packed (0xD800 + src_row*40 + byte_col), so scanout must
// read src_row*40 + byte_col. Real hardware can't multiply free, so this is the standard
// accumulator, modelled at the register/counter granularity it maps to in the netlist:
//   * SCAN_ADDR (14-bit loadable up-counter, 4x '161): the live SRAM scanout address;
//     +1 per fetched byte, reloaded to the row base at each line wrap.
//   * ROW_BASE  (14-bit register, 2x '374): the current source row's base = src_row*40.
// No adder: because rows are contiguous stride-40, a line that starts at ROW_BASE and
// counts its 40 bytes ends at ROW_BASE+40 — so on the 2nd (odd) doubled line we just
// capture SCAN_ADDR as the next ROW_BASE. Even lines reload the same base (v-doubling).
// All control fires on the LAST dot of the line (line_end) so the load lands exactly as
// hcount wraps to 0, aligned with the first byte's fetch window. Validated by
// revb_video_addrgen_tb.v against the golden src_row*40+byte_col.
`default_nettype none
module revb_video_addrgen #(
    parameter integer FB_COLS = 40
) (
    input  wire        dot_clk,
    input  wire        reset_n,
    input  wire        line_end,     // hcount == H_TOTAL-1 (pulse; this edge wraps the line)
    input  wire        frame_last,   // vcount == V_TOTAL-1 (this edge wraps the frame)
    input  wire        vcount0,      // vcount[0] of the ENDING line (1 = odd = 2nd doubled)
    input  wire        byte_tick,    // one pulse per fetched byte, active region only
    output reg  [13:0] scan_addr
);
    reg  [13:0] row_base;
    wire [13:0] next_base = vcount0 ? scan_addr : row_base;  // advance on the odd line

    always @(posedge dot_clk or negedge reset_n) begin
        if (!reset_n) begin
            row_base  <= 14'd0;
            scan_addr <= 14'd0;
        end else if (line_end) begin
            if (frame_last) begin              // next line is the frame top
                row_base  <= 14'd0;
                scan_addr <= 14'd0;
            end else begin
                row_base  <= next_base;        // hold on even lines, +FB_COLS on odd
                scan_addr <= next_base;        // load the new line's base
            end
        end else if (byte_tick) begin
            scan_addr <= scan_addr + 14'd1;    // next byte
        end
    end
endmodule
`default_nettype wire
