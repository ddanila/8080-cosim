// VJUGA rev B — Memory card structural LVS netlist (TD.6.2).
// EMPTY-BODIED chip modules wired per the mem card's design intent; this is the
// INDEPENDENT artifact LVS compares against the generated mem.board.json (via
// sync/revb_mem_map.json). It is NOT a behavioral model -- the booting model stays
// hdl/revb/revb_mem_card.v (rev A `minimal_vga_lvs.v` pattern). Port names match the
// CHIP_TYPES net names so hdl_pin canonicalization (A[0]->A0) lines up with the pinmap.
`default_nettype none

module rom_27c256_lvs(
    input  wire [14:0] A,      // A0..A14
    inout  wire [7:0]  D,
    input  wire        ROM_CE_N, MEM_RD_N
);
endmodule

module sram_as6c1008_lvs(
    input  wire [15:0] A,      // A0..A15
    inout  wire [7:0]  D,
    input  wire        RAM_CE_N, MEM_RD_N, MEM_WR_N
);
endmodule

module gal22v10_memdec_lvs(
    input  wire        MREQ_N, RD_N, WR_N,
    // Scalar A11..A15 (not a [15:11] vector: hdl_pin canonicalizes vector bits by
    // POSITION, so [15:11] would become A0..A4 and mis-map).
    input  wire        A11, A12, A13, A14, A15,
    input  wire        MODE0, MODE1,
    output wire        ROM_CE_N, RAM_CE_N, MEM_RD_N, MEM_WR_N
);
endmodule

module revb_mem_lvs_top;
    wire [15:0] A;
    wire [7:0]  D;
    wire MREQ_N, RD_N, WR_N, MODE0, MODE1;
    wire ROM_CE_N, RAM_CE_N, MEM_RD_N, MEM_WR_N;

    rom_27c256_lvs U_ROM(
        .A(A[14:0]), .D(D), .ROM_CE_N(ROM_CE_N), .MEM_RD_N(MEM_RD_N));

    sram_as6c1008_lvs U_SRAM(
        .A(A[15:0]), .D(D), .RAM_CE_N(RAM_CE_N), .MEM_RD_N(MEM_RD_N), .MEM_WR_N(MEM_WR_N));

    gal22v10_memdec_lvs U_DEC(
        .MREQ_N(MREQ_N), .RD_N(RD_N), .WR_N(WR_N),
        .A11(A[11]), .A12(A[12]), .A13(A[13]), .A14(A[14]), .A15(A[15]),
        .MODE0(MODE0), .MODE1(MODE1),
        .ROM_CE_N(ROM_CE_N), .RAM_CE_N(RAM_CE_N), .MEM_RD_N(MEM_RD_N), .MEM_WR_N(MEM_WR_N));
endmodule
`default_nettype wire
