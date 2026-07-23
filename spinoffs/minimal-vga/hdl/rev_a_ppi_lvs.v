// VJUGA Rev A staged physical LVS: complete U30 82C55 PPI.
//
// U30 and C19 are complete owned instances. The remaining cells are exact
// boundary projections for all 28 non-power nets touched by U30. The downstream
// resistor-to-keyboard-connector network and remaining U31 pins stay staged.
`default_nettype none

module rev_a_ppi_pins2_lvs(inout wire P1, P2);
endmodule

module rev_a_ppi_pins40_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8,
    inout wire P9, P10, P11, P12, P13, P14, P15, P16,
    inout wire P17, P18, P19, P20, P21, P22, P23, P24,
    inout wire P25, P26, P27, P28, P29, P30, P31, P32,
    inout wire P33, P34, P35, P36, P37, P38, P39, P40
);
endmodule

module rev_a_ppi_cpu_boundary_lvs(
    inout wire P7, P8, P9, P10, P12, P13, P14, P15,
    inout wire P26, P30, P31
);
endmodule

module rev_a_ppi_rom_boundary_lvs(
    inout wire P9, P10, P11, P12, P13,
    inout wire P15, P16, P17, P18, P19
);
endmodule

module rev_a_ppi_dram_boundary_lvs(inout wire P2, P14);
endmodule

module rev_a_ppi_mux_boundary_lvs(inout wire P2, P5);
endmodule

module rev_a_ppi_u31_boundary_lvs(inout wire P6, P7, P9, P14);
endmodule

module rev_a_ppi_u41_boundary_lvs(
    inout wire P2, P3, P4, P5, P9, P10, P11, P12, P14
);
endmodule

module rev_a_ppi_decode_boundary_lvs(inout wire P16, P19, P20);
endmodule

module rev_a_ppi_inverter_boundary_lvs(inout wire P1, P3);
endmodule

module rev_a_ppi_j90_boundary_lvs(inout wire P1, P2);
endmodule

module rev_a_ppi_j91_boundary_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8, P10
);
endmodule

module rev_a_ppi_pin1_boundary_lvs(inout wire P1);
endmodule

module rev_a_ppi_pin2_boundary_lvs(inout wire P2);
endmodule

module rev_a_ppi_lvs_top;
    wire VCC, GND;
    wire A0, A1, D0, D1, D2, D3, D4, D5, D6, D7;
    wire RESET_N, IO_RD_N, IO_WR_N, PPI_CS_N;
    wire KBD_ROW_A0_N, KBD_ROW_A1_N, KBD_ROW_A2_N, KBD_GS_N;
    wire KBD_COL0_DRV, KBD_COL1_DRV, KBD_COL2_DRV, KBD_COL3_DRV;
    wire KBD_COL4_DRV, KBD_COL5_DRV, KBD_COL6_DRV, KBD_COL7_DRV;
    wire PC0, PC1;
    wire U30_P16_NC, U30_P17_NC;
    wire U30_P18_NC, U30_P19_NC, U30_P20_NC, U30_P21_NC;
    wire U30_P22_NC, U30_P23_NC, U30_P24_NC, U30_P25_NC;

    rev_a_ppi_pins40_lvs U_U30(
        .P1(KBD_COL3_DRV), .P2(KBD_COL2_DRV),
        .P3(KBD_COL1_DRV), .P4(KBD_COL0_DRV),
        .P5(IO_RD_N), .P6(PPI_CS_N), .P7(GND),
        .P8(A1), .P9(A0),
        .P10(KBD_GS_N), .P11(KBD_ROW_A2_N),
        .P12(KBD_ROW_A1_N), .P13(KBD_ROW_A0_N),
        .P14(PC0), .P15(PC1),
        .P16(U30_P16_NC), .P17(U30_P17_NC),
        .P18(U30_P18_NC), .P19(U30_P19_NC),
        .P20(U30_P20_NC), .P21(U30_P21_NC),
        .P22(U30_P22_NC), .P23(U30_P23_NC),
        .P24(U30_P24_NC), .P25(U30_P25_NC),
        .P26(VCC),
        .P27(D7), .P28(D6), .P29(D5), .P30(D4),
        .P31(D3), .P32(D2), .P33(D1), .P34(D0),
        .P35(RESET_N), .P36(IO_WR_N),
        .P37(KBD_COL7_DRV), .P38(KBD_COL6_DRV),
        .P39(KBD_COL5_DRV), .P40(KBD_COL4_DRV));
    rev_a_ppi_pins2_lvs U_C19(.P1(VCC), .P2(GND));

    rev_a_ppi_cpu_boundary_lvs U_CPU_BOUNDARY(
        .P7(D4), .P8(D3), .P9(D5), .P10(D6),
        .P12(D2), .P13(D7), .P14(D0), .P15(D1),
        .P26(RESET_N), .P30(A0), .P31(A1));
    rev_a_ppi_rom_boundary_lvs U_ROM_BOUNDARY(
        .P9(A1), .P10(A0),
        .P11(D0), .P12(D1), .P13(D2), .P15(D3),
        .P16(D4), .P17(D5), .P18(D6), .P19(D7));

    rev_a_ppi_dram_boundary_lvs U_U10_BOUNDARY(.P2(D0), .P14(D0));
    rev_a_ppi_dram_boundary_lvs U_U11_BOUNDARY(.P2(D1), .P14(D1));
    rev_a_ppi_dram_boundary_lvs U_U12_BOUNDARY(.P2(D2), .P14(D2));
    rev_a_ppi_dram_boundary_lvs U_U13_BOUNDARY(.P2(D3), .P14(D3));
    rev_a_ppi_dram_boundary_lvs U_U14_BOUNDARY(.P2(D4), .P14(D4));
    rev_a_ppi_dram_boundary_lvs U_U15_BOUNDARY(.P2(D5), .P14(D5));
    rev_a_ppi_dram_boundary_lvs U_U16_BOUNDARY(.P2(D6), .P14(D6));
    rev_a_ppi_dram_boundary_lvs U_U17_BOUNDARY(.P2(D7), .P14(D7));

    rev_a_ppi_mux_boundary_lvs U_U20_BOUNDARY(.P2(A0), .P5(A1));
    rev_a_ppi_pin2_boundary_lvs U_U24_BOUNDARY(.P2(RESET_N));
    rev_a_ppi_u31_boundary_lvs U_U31_BOUNDARY(
        .P6(KBD_ROW_A2_N), .P7(KBD_ROW_A1_N),
        .P9(KBD_ROW_A0_N), .P14(KBD_GS_N));
    rev_a_ppi_pin2_boundary_lvs U_U40_BOUNDARY(.P2(RESET_N));
    rev_a_ppi_u41_boundary_lvs U_U41_BOUNDARY(
        .P2(D0), .P3(D1), .P4(D2), .P5(D3), .P9(RESET_N),
        .P10(D4), .P11(D5), .P12(D6), .P14(D7));
    rev_a_ppi_decode_boundary_lvs U_U5_BOUNDARY(
        .P16(PPI_CS_N), .P19(IO_RD_N), .P20(IO_WR_N));
    rev_a_ppi_pin2_boundary_lvs U_U51_BOUNDARY(.P2(RESET_N));
    rev_a_ppi_inverter_boundary_lvs U_U6_BOUNDARY(.P1(PC0), .P3(PC1));

    rev_a_ppi_pin2_boundary_lvs U_R5_BOUNDARY(.P2(RESET_N));
    rev_a_ppi_pin1_boundary_lvs U_R16_BOUNDARY(.P1(KBD_COL0_DRV));
    rev_a_ppi_pin1_boundary_lvs U_R17_BOUNDARY(.P1(KBD_COL1_DRV));
    rev_a_ppi_pin1_boundary_lvs U_R18_BOUNDARY(.P1(KBD_COL2_DRV));
    rev_a_ppi_pin1_boundary_lvs U_R19_BOUNDARY(.P1(KBD_COL3_DRV));
    rev_a_ppi_pin1_boundary_lvs U_R20_BOUNDARY(.P1(KBD_COL4_DRV));
    rev_a_ppi_pin1_boundary_lvs U_R21_BOUNDARY(.P1(KBD_COL5_DRV));
    rev_a_ppi_pin1_boundary_lvs U_R22_BOUNDARY(.P1(KBD_COL6_DRV));
    rev_a_ppi_pin1_boundary_lvs U_R23_BOUNDARY(.P1(KBD_COL7_DRV));
    rev_a_ppi_pin1_boundary_lvs U_R27_BOUNDARY(.P1(RESET_N));
    rev_a_ppi_j90_boundary_lvs U_J90_BOUNDARY(.P1(A0), .P2(A1));
    rev_a_ppi_j91_boundary_lvs U_J91_BOUNDARY(
        .P1(D0), .P2(D1), .P3(D2), .P4(D3),
        .P5(D4), .P6(D5), .P7(D6), .P8(D7), .P10(RESET_N));
endmodule

`default_nettype wire
