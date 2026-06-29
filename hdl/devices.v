// Device module SHELLS for juku_top.v.
// Port lists are the contract LVS cares about; bodies are stubs to be replaced
// with behavioral models (or a vendored 8080 core) for simulation.
`default_nettype none

// ---- CPU + bus control (i8080 + 8228/8224-equivalent) ----
module cpu_8080 (
    input  wire        clk, reset_n,
    output wire [15:0] A,
    inout  wire [7:0]  D,
    output wire        memr_n, memw_n, ior_n, iow_n,
    input  wire        intr,
    output wire        inta_n
);
    // TODO: vendor an open Verilog 8080 core + 8228 status decode here.
    assign A = 16'b0;
    assign D = 8'bz;
    assign {memr_n, memw_n, ior_n, iow_n, inta_n} = 5'b11111;
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

// ---- memory ----
module rom_16k (input wire [13:0] A, inout wire [7:0] D, input wire oe_n);
    assign D = 8'bz; // TODO: $readmemh(ekta43) and drive D when ~oe_n
endmodule

module ram_64k (input wire [15:0] A, inout wire [7:0] D, input wire we_n, oe_n);
    assign D = 8'bz; // TODO: behavioral 64Kx8 (board = 20x dram_64kx1)
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
