// VJUGA Rev A staged physical LVS: complete Z80 CPU + ROM core.
//
// U1, U2, C1, and C2 are complete owned instances. Every other cell is an
// exact boundary projection for one of the 36 non-power nets touched by the
// core. This is structural connectivity only, independent of the board JSON.
`default_nettype none

module rev_a_core_pins2_lvs(inout wire P1, P2);
endmodule

module rev_a_core_pins28_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7,
    inout wire P8, P9, P10, P11, P12, P13, P14,
    inout wire P15, P16, P17, P18, P19, P20, P21,
    inout wire P22, P23, P24, P25, P26, P27, P28
);
endmodule

module rev_a_core_pins40_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8, P9, P10,
    inout wire P11, P12, P13, P14, P15, P16, P17, P18, P19, P20,
    inout wire P21, P22, P23, P24, P25, P26, P27, P28, P29, P30,
    inout wire P31, P32, P33, P34, P35, P36, P37, P38, P39, P40
);
endmodule

module rev_a_core_u3_boundary_lvs(
    inout wire P3, P4, P5, P6, P7
);
endmodule

module rev_a_core_u4_boundary_lvs(
    inout wire P10, P11, P12, P13, P14, P15
);
endmodule

module rev_a_core_u5_boundary_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7,
    inout wire P14, P17, P18
);
endmodule

module rev_a_core_dram_boundary_lvs(inout wire P2, P14);
endmodule

module rev_a_core_mux_boundary_lvs(inout wire P2, P5, P11, P14);
endmodule

module rev_a_core_pin1_boundary_lvs(inout wire P1);
endmodule

module rev_a_core_pin2_boundary_lvs(inout wire P2);
endmodule

module rev_a_core_pin8_boundary_lvs(inout wire P8);
endmodule

module rev_a_core_u24_boundary_lvs(
    inout wire P1, P2, P4, P5, P6, P18
);
endmodule

module rev_a_core_ppi_boundary_lvs(
    inout wire P8, P9,
    inout wire P27, P28, P29, P30, P31, P32, P33, P34, P35
);
endmodule

module rev_a_core_u41_boundary_lvs(
    inout wire P2, P3, P4, P5, P9, P10, P11, P12, P14
);
endmodule

module rev_a_core_j90_boundary_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8, P10
);
endmodule

module rev_a_core_j91_boundary_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8, P10
);
endmodule

module rev_a_core_j92_boundary_lvs(inout wire P8, P10);
endmodule

module rev_a_core_j97_boundary_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8, P9
);
endmodule

module rev_a_core_j98_boundary_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7
);
endmodule

module rev_a_cpu_rom_lvs_top;
    wire VCC, GND;
    wire A0, A1, A2, A3, A4, A5, A6, A7;
    wire A8, A9, A10, A11, A12, A13, A14, A15;
    wire D0, D1, D2, D3, D4, D5, D6, D7;
    wire CLK, RESET_N, WAIT_N;
    wire MREQ_N, IORQ_N, RD_N, WR_N, M1_N, RFSH_N;
    wire ROM_CE_N, MEM_RD_N, MEM_WR_N;
    wire U1_P18_NC, U1_P23_NC;

    rev_a_core_pins40_lvs U_CPU(
        .P1(A11), .P2(A12), .P3(A13), .P4(A14), .P5(A15),
        .P6(CLK), .P7(D4), .P8(D3), .P9(D5), .P10(D6),
        .P11(VCC), .P12(D2), .P13(D7), .P14(D0), .P15(D1),
        .P16(VCC), .P17(VCC), .P18(U1_P18_NC),
        .P19(MREQ_N), .P20(IORQ_N), .P21(RD_N), .P22(WR_N),
        .P23(U1_P23_NC), .P24(WAIT_N), .P25(VCC), .P26(RESET_N),
        .P27(M1_N), .P28(RFSH_N), .P29(GND),
        .P30(A0), .P31(A1), .P32(A2), .P33(A3), .P34(A4),
        .P35(A5), .P36(A6), .P37(A7), .P38(A8), .P39(A9), .P40(A10));

    rev_a_core_pins28_lvs U_ROM(
        .P1(A14), .P2(A12), .P3(A7), .P4(A6), .P5(A5), .P6(A4), .P7(A3),
        .P8(A2), .P9(A1), .P10(A0), .P11(D0), .P12(D1), .P13(D2),
        .P14(GND), .P15(D3), .P16(D4), .P17(D5), .P18(D6), .P19(D7),
        .P20(ROM_CE_N), .P21(A10), .P22(MEM_RD_N), .P23(A11),
        .P24(A9), .P25(A8), .P26(A13), .P27(MEM_WR_N), .P28(VCC));

    rev_a_core_pins2_lvs U_C1(.P1(VCC), .P2(GND));
    rev_a_core_pins2_lvs U_C2(.P1(VCC), .P2(GND));

    rev_a_core_u3_boundary_lvs U_U3_BOUNDARY(
        .P3(A11), .P4(A12), .P5(A15), .P6(A14), .P7(A13));
    rev_a_core_u4_boundary_lvs U_U4_BOUNDARY(
        .P10(A11), .P11(A12), .P12(A13),
        .P13(A14), .P14(A15), .P15(ROM_CE_N));
    rev_a_core_u5_boundary_lvs U_U5_BOUNDARY(
        .P1(MREQ_N), .P2(IORQ_N), .P3(RD_N), .P4(WR_N),
        .P5(A13), .P6(A14), .P7(A15),
        .P14(ROM_CE_N), .P17(MEM_RD_N), .P18(MEM_WR_N));

    rev_a_core_dram_boundary_lvs U_U10_BOUNDARY(.P2(D0), .P14(D0));
    rev_a_core_dram_boundary_lvs U_U11_BOUNDARY(.P2(D1), .P14(D1));
    rev_a_core_dram_boundary_lvs U_U12_BOUNDARY(.P2(D2), .P14(D2));
    rev_a_core_dram_boundary_lvs U_U13_BOUNDARY(.P2(D3), .P14(D3));
    rev_a_core_dram_boundary_lvs U_U14_BOUNDARY(.P2(D4), .P14(D4));
    rev_a_core_dram_boundary_lvs U_U15_BOUNDARY(.P2(D5), .P14(D5));
    rev_a_core_dram_boundary_lvs U_U16_BOUNDARY(.P2(D6), .P14(D6));
    rev_a_core_dram_boundary_lvs U_U17_BOUNDARY(.P2(D7), .P14(D7));

    rev_a_core_mux_boundary_lvs U_U20_BOUNDARY(
        .P2(A0), .P5(A1), .P11(A2), .P14(A3));
    rev_a_core_mux_boundary_lvs U_U21_BOUNDARY(
        .P2(A4), .P5(A5), .P11(A6), .P14(A7));
    rev_a_core_pin1_boundary_lvs U_U22_BOUNDARY(.P1(CLK));
    rev_a_core_pin1_boundary_lvs U_U23_BOUNDARY(.P1(CLK));
    rev_a_core_u24_boundary_lvs U_U24_BOUNDARY(
        .P1(CLK), .P2(RESET_N), .P4(MEM_RD_N),
        .P5(MEM_WR_N), .P6(RFSH_N), .P18(WAIT_N));

    rev_a_core_ppi_boundary_lvs U_U30_BOUNDARY(
        .P8(A1), .P9(A0),
        .P27(D7), .P28(D6), .P29(D5), .P30(D4),
        .P31(D3), .P32(D2), .P33(D1), .P34(D0), .P35(RESET_N));
    rev_a_core_pin2_boundary_lvs U_U40_BOUNDARY(.P2(RESET_N));
    rev_a_core_u41_boundary_lvs U_U41_BOUNDARY(
        .P2(D0), .P3(D1), .P4(D2), .P5(D3), .P9(RESET_N),
        .P10(D4), .P11(D5), .P12(D6), .P14(D7));
    rev_a_core_pin8_boundary_lvs U_U50_BOUNDARY(.P8(CLK));
    rev_a_core_pin2_boundary_lvs U_U51_BOUNDARY(.P2(RESET_N));

    rev_a_core_j90_boundary_lvs U_J90_BOUNDARY(
        .P1(A0), .P2(A1), .P3(A2), .P4(A3),
        .P5(A4), .P6(A5), .P7(A6), .P8(A7), .P10(CLK));
    rev_a_core_j91_boundary_lvs U_J91_BOUNDARY(
        .P1(D0), .P2(D1), .P3(D2), .P4(D3),
        .P5(D4), .P6(D5), .P7(D6), .P8(D7), .P10(RESET_N));
    rev_a_core_j92_boundary_lvs U_J92_BOUNDARY(.P8(WAIT_N), .P10(CLK));
    rev_a_core_j97_boundary_lvs U_J97_BOUNDARY(
        .P1(A8), .P2(A9), .P3(A10), .P4(A11), .P5(A12),
        .P6(A13), .P7(A14), .P8(A15), .P9(MEM_WR_N));
    rev_a_core_j98_boundary_lvs U_J98_BOUNDARY(
        .P1(MREQ_N), .P2(IORQ_N), .P3(RD_N), .P4(WR_N),
        .P5(M1_N), .P6(RFSH_N), .P7(WAIT_N));

    rev_a_core_pin1_boundary_lvs U_D6_BOUNDARY(.P1(M1_N));
    rev_a_core_pin1_boundary_lvs U_D7_BOUNDARY(.P1(RFSH_N));
    rev_a_core_pin2_boundary_lvs U_R5_BOUNDARY(.P2(RESET_N));
    rev_a_core_pin1_boundary_lvs U_R26_BOUNDARY(.P1(CLK));
    rev_a_core_pin1_boundary_lvs U_R27_BOUNDARY(.P1(RESET_N));
endmodule

`default_nettype wire
