// Device module SHELLS for juku_top.v.
// Port lists are the contract LVS cares about; bodies are stubs to be replaced
// with behavioral models (or a vendored 8080 core) for simulation.
`default_nettype none

// ---- bare i8080A CPU (КР580ВМ80) ----
module cpu_8080 (
    input  wire        phi1, phi2, ready, reset, hold, intr,
    output wire [15:0] A,
    inout  wire [7:0]  D,        // multiplexed data + status byte
    output wire        dbin, wr_n, sync, hlda, inte, wait_o
);
    // TODO: vendor an open Verilog 8080 core.
    assign A = 16'b0;
    assign D = 8'bz;
    assign {dbin, wr_n, sync, hlda, inte, wait_o} = 6'b011000;
endmodule

// NOTE: no clk_8224 module — this board generates the clock discretely
// (crystal + ЛН1 oscillator D59 + phase gates D33/D35/D36/D38). To be modeled
// as its own clock subsystem; the CPU core treats Φ1/Φ2/RESET/READY as boundary nets.

// ---- i8238 system controller (КР580ВК38) ----
module sysctl_8238 (
    inout  wire [7:0] D,         // CPU data/status side
    inout  wire [7:0] DB,        // buffered system data bus side
    input  wire       dbin, wr_n, hlda, ststb_n, busen_n,
    output wire       memr_n, memw_n, iord_n, iowr_n, inta_n
);
    assign D = 8'bz; assign DB = 8'bz;
    assign {memr_n, memw_n, iord_n, iowr_n, inta_n} = 5'b11111;
endmodule

// ---- i8286 octal bus transceiver (КР580ВА86), used as address buffer ----
module buf_8286 (
    inout wire [7:0] Ain, Aout,
    input wire       oe_n, t
);
    assign Ain = 8'bz; assign Aout = 8'bz;
endmodule

// ---- I/O port decoder (board glue: 74xx138-style) ----
module io_decode (
    input  wire [7:0] A,
    input  wire       ior_n, iow_n,
    output wire       cs_pic_n, cs_ppi0_n, cs_sio0_n, cs_ppi1_n,
    output wire       cs_pit0_n, cs_pit1_n, cs_pit2_n, cs_fdc_n
);
    wire active = ~(ior_n & iow_n);          // some I/O cycle in progress
    wire [2:0] grp = A[4:2];                  // chip group select
    assign cs_pic_n  = ~(active & (grp == 3'd0) & (A[7:5] == 0)); // 0x00..0x03
    assign cs_ppi0_n = ~(active & (grp == 3'd1) & (A[7:5] == 0)); // 0x04..0x07
    assign cs_sio0_n = ~(active & (grp == 3'd2) & (A[7:5] == 0)); // 0x08..0x0B
    assign cs_ppi1_n = ~(active & (grp == 3'd3) & (A[7:5] == 0)); // 0x0C..0x0F
    assign cs_pit0_n = ~(active & (grp == 3'd4) & (A[7:5] == 0)); // 0x10..0x13
    assign cs_pit1_n = ~(active & (grp == 3'd5) & (A[7:5] == 0)); // 0x14..0x17
    assign cs_pit2_n = ~(active & (grp == 3'd6) & (A[7:5] == 0)); // 0x18..0x1B
    assign cs_fdc_n  = ~(active & (grp == 3'd7) & (A[7:5] == 0)); // 0x1C..0x1F
endmodule

// ---- memory bank decode: 4-mode ROM/RAM overlay (PPI0 PortC[1:0]) ----
module mem_decode (
    input  wire [15:0] A,
    input  wire        memr_n, memw_n,
    input  wire [1:0]  mode,
    output wire        rom_oe_n, ram_oe_n, ram_we_n
);
    // mode0: ROM 0x0000-0x3FFF ; mode1/2: ROM 0xD800-0xFFFF ; mode3: all RAM
    wire rom_lo = (mode == 2'd0) && (A <= 16'h3FFF);
    wire rom_hi = (mode == 2'd1 || mode == 2'd2) && (A >= 16'hD800);
    wire rom_sel = rom_lo || rom_hi;
    assign rom_oe_n = ~(rom_sel & ~memr_n);
    assign ram_oe_n = ~(~rom_sel & ~memr_n);
    assign ram_we_n = ~(~rom_sel & ~memw_n);   // writes under ROM overlay are dropped
endmodule

// ---- memory map decoder: К556РТ4 256x4 bipolar PROM (D6) ----
// decodes high address byte A8..A15 -> ROM/RAM/REV/ROE selects (contents from the
// emulator-recovered map). Enabled by V (from the D7 gate = mode/strobe).
module decode_prom (input wire [15:8] a, input wire v_en_n,
                    output wire rom_n, ram_n, rev, roe_n);
    assign {rom_n, ram_n, rev, roe_n} = 4'b1111;   // stub; truth-table = PROM contents
endmodule

// ---- ЛА3 NAND gate section (D7) gating the PROM enable ----
module la3_gate (input wire a, b, output wire y);
    assign y = ~(a & b);
endmodule

// ---- EPROM 8Kx8 (К573РФ4-class, D15..D22) ----
module eprom_8k (input wire [12:0] a, inout wire [7:0] d, input wire cs_n, oe_n);
    assign d = 8'bz;   // TODO: $readmemh; drive d when selected
endmodule

// ===== clock subsystem (discrete; replaces the non-existent 8224) =====
module ln1_osc   (input wire xin, output wire osc);                  // D59 ЛН1 crystal oscillator
    assign osc = 1'bz; endmodule
module clk_phase (input wire osc, output wire phi1, phi2, phi2ttl);  // D35 ЛН5 phase generator
    assign {phi1, phi2, phi2ttl} = 3'bz; endmodule
module stb_gen   (input wire osc, output wire stb);                  // D38 (legacy stub, unused)
    assign stb = 1'bz; endmodule
// clock divider + gate mesh (scan: docs/transcription/clock-subsystem.md). Z1 -> D59 osc ->
// D40 divider -> D33/D39/D36 gates -> D38 (ЛА1) = STB and D35 (ЛН5) = Φ1/Φ2.
module ct16_ctr  (input wire clk, r_n, ep, et, pe_n, input wire [3:0] d,  // D40 СТ16 (74161-class)
                  output wire [3:0] q, output wire co);
    assign q = 4'bz; assign co = 1'bz; endmodule
module ln1_inv   (input wire a, output wire y); assign y = 1'bz; endmodule   // D33 ЛН1 inverter gate
module la12_gate (input wire a, b, output wire y); assign y = 1'bz; endmodule // D36 ЛА12 NAND gate
module la1_gate  (input wire i0, i1, i2, i3, output wire y);                  // D38 ЛА1 4-input NAND
    assign y = 1'bz; endmodule

// ===== I/O chip-select decoder: К555ИД7 (74138) =====
module io_dec138 (input wire a, b, c, g1, g2a_n, g2b_n, output wire [7:0] y_n);
    assign y_n = 8'hFF; endmodule

// ===== video address generation + address mux (closes РУ5 MA/RAS/CAS) =====
module ie7_ctr   (input wire clk, load_n, input wire [3:0] d, output wire [3:0] q, output wire co); // D44-47 ИЕ7
    assign q = 4'bz; assign co = 1'bz; endmodule
module kp14_mux  (input wire [3:0] a, b, input wire sel, en_n, output wire [3:0] y);  // D48-50 КП14 quad 2:1
    assign y = 4'bz; endmodule
module rascas_dec (input wire a, b, c, input wire g, output wire [3:0] y_n);  // D53 ИД7 RAS/CAS/bank
    assign y_n = 4'bz; endmodule
// ---- video dot-clock chain (scan: docs/transcription/dram-video-timing.md, sheet-2 BR) ----
module ag3_oneshot (input wire a_n, b, clr_n, output wire q, q_n);  // D56 АГ3 (74123) RC -> 16 MHz
    assign q = 1'bz; assign q_n = 1'bz; endmodule
module ie10_ctr (input wire clk, clr_n, load_n, input wire [3:0] d,  // D103 ИЕ10 (СТ16): /N -> 1.23 MHz
                 output wire [3:0] q, output wire co);
    assign q = 4'bz; assign co = 1'bz; endmodule

// ---- К565РУ5 64Kx1 DRAM (one chip = one data bit); array from D60 ----
module dram_64kx1 (input wire [7:0] ma,            // multiplexed row/col address
                   input wire ras_n, cas_n, we_n, di,
                   output wire do_);
    assign do_ = 1'bz;   // behavioral 64Kx1 array TODO
endmodule

// ---- peripheral shells ----
module ppi_8255 (input wire [1:0] A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n, reset,
                 output wire [1:0] portc_lo);
    assign D = 8'bz; assign portc_lo = 2'b00;
endmodule

module pit_8253 (input wire [1:0] A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n, clk);
    assign D = 8'bz;
endmodule

module usart_8251 (input wire A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n, clk);
    assign D = 8'bz;
endmodule

module fdc_1793 (input wire [1:0] A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n, clk);
    assign D = 8'bz;
endmodule

module pic_8259 (input wire A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n,
                 output wire intr, input wire inta_n);
    assign D = 8'bz; assign intr = 1'b0;
endmodule
`default_nettype wire
