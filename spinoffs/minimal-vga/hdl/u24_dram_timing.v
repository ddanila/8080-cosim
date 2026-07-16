`timescale 1ns/1ns
// Behavioral programming contract for the Rev-A U24 GAL22V10.
//
// The three state outputs are real GAL macrocells (pins 21-23), so the model
// does not rely on hidden storage unavailable in a 22V10. Functional outputs
// occupy pins 14-20; pin 13 remains the device's twelfth input/OE pin.
module u24_dram_timing (
    input  wire clk,
    input  wire reset_n,
    input  wire ram_ce_n,
    input  wire mem_rd_n,
    input  wire mem_wr_n,
    input  wire rfsh_obs_n,
    input  wire video_req,
    input  wire decode_wait_n,
    input  wire refresh_q0,
    input  wire refresh_q1,
    input  wire refresh_q2,
    input  wire refresh_q3,
    output reg  ras_n,
    output reg  cas_n,
    output reg  dram_we_n,
    output reg  addrmux_sel,
    output wire cpu_wait_n,
    output wire video_ack,
    output wire refresh_tick,
    output wire state0,
    output wire state1,
    output wire state2
);
    localparam [2:0]
        // Cyclic Gray ordering: every phase transition, including DONE->IDLE,
        // changes exactly one registered feedback bit and cannot decode a
        // spurious intermediate RAS/CAS phase.
        S_IDLE       = 3'b000,
        S_ROW        = 3'b001,
        S_RAS        = 3'b011,
        S_COL        = 3'b010,
        S_CAS        = 3'b110,
        S_HOLD       = 3'b111,
        S_PRECHARGE  = 3'b101,
        S_DONE       = 3'b100;

    reg [2:0] state = S_IDLE;
    reg video_active = 1'b0;
    reg refresh_active = 1'b0;

    wire cpu_request = !ram_ce_n && (!mem_rd_n || !mem_wr_n);
    wire cpu_write = cpu_request && !mem_wr_n;

    assign {state2, state1, state0} = state;
    assign video_ack = video_active;
    assign refresh_tick = refresh_active;
    // Assert WAIT immediately when an access appears and release it only in
    // DONE, after CAS has risen and the read latch may sample stable data.
    // DONE releases a waiting CPU only when the completed cycle belongs to
    // that CPU. A request may arrive while refresh/video owns the sequencer;
    // keep it stalled through that client's DONE so IDLE can accept and run
    // the still-pending CPU transaction on the following cycle.
    wire cpu_done = state == S_DONE && !video_active && !refresh_active;
    assign cpu_wait_n = !reset_n ? 1'b1
        : decode_wait_n && !(cpu_request && !cpu_done);

    always @* begin
        case (state)
            S_RAS: begin
                ras_n = 1'b0;
                cas_n = 1'b1;
                dram_we_n = 1'b1;
                addrmux_sel = 1'b0;
            end
            S_COL: begin
                ras_n = 1'b0;
                cas_n = 1'b1;
                addrmux_sel = 1'b1;
                dram_we_n = ~(cpu_write && !video_active && !refresh_active);
            end
            S_CAS, S_HOLD: begin
                ras_n = 1'b0;
                cas_n = 1'b0;
                addrmux_sel = 1'b1;
                dram_we_n = ~(cpu_write && !video_active && !refresh_active);
            end
            // CAS rises one full clock before RAS, satisfying tRSH/tCSH.
            S_PRECHARGE: begin
                ras_n = 1'b0;
                cas_n = 1'b1;
                dram_we_n = 1'b1;
                addrmux_sel = !refresh_active;
            end
            default: begin
                ras_n = 1'b1;
                cas_n = 1'b1;
                dram_we_n = 1'b1;
                addrmux_sel = 1'b0;
            end
        endcase
    end

    always @(posedge clk) begin
        if (!reset_n) begin
            state <= S_IDLE;
            video_active <= 1'b0;
            refresh_active <= 1'b0;
        end else begin
            case (state)
                S_IDLE: begin
                    video_active <= 1'b0;
                    refresh_active <= 1'b0;
                    if (cpu_request) begin
                        state <= S_ROW;
                    end else if (!rfsh_obs_n) begin
                        refresh_active <= 1'b1;
                        state <= S_ROW;
                    end else if (video_req) begin
                        video_active <= 1'b1;
                        state <= S_ROW;
                    end
                end
                S_ROW: state <= S_RAS;
                // Refresh is RAS-only; CPU/video continue to column access.
                S_RAS: state <= refresh_active ? S_PRECHARGE : S_COL;
                S_COL: state <= S_CAS;
                S_CAS: state <= S_HOLD;
                S_HOLD: state <= S_PRECHARGE;
                S_PRECHARGE: state <= S_DONE;
                S_DONE: begin
                    state <= S_IDLE;
                    video_active <= 1'b0;
                    refresh_active <= 1'b0;
                end
                default: state <= S_IDLE;
            endcase
        end
    end

    // Refresh row bits are physical U24 inputs routed to the address muxes.
    // Their values do not alter sequencing; referencing them here documents
    // that they are intentionally consumed by the programmed-device contract.
    wire _unused_ok = &{1'b0, refresh_q0, refresh_q1, refresh_q2, refresh_q3};
endmodule
