// VJUGA Rev A staged physical LVS: complete eight-chip 4164 DRAM bank.
//
// U10-U17 and C6-C13 are complete owned instances. The remaining cells are
// exact boundary projections for all 19 non-power nets touched by the bank.
`default_nettype none

module rev_a_dram_pins2_lvs(inout wire P1, P2);
endmodule

module rev_a_dram_pins16_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8,
    inout wire P9, P10, P11, P12, P13, P14, P15, P16
);
endmodule

module rev_a_dram_cpu_boundary_lvs(
    inout wire P7, P8, P9, P10, P12, P13, P14, P15
);
endmodule

module rev_a_dram_rom_boundary_lvs(
    inout wire P11, P12, P13, P15, P16, P17, P18, P19
);
endmodule

module rev_a_dram_mux_boundary_lvs(inout wire P4, P7, P9, P12);
endmodule

module rev_a_dram_u24_boundary_lvs(inout wire P14, P15, P16);
endmodule

module rev_a_dram_ppi_boundary_lvs(
    inout wire P27, P28, P29, P30, P31, P32, P33, P34
);
endmodule

module rev_a_dram_u41_boundary_lvs(
    inout wire P2, P3, P4, P5, P10, P11, P12, P14
);
endmodule

module rev_a_dram_j91_boundary_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8
);
endmodule

module rev_a_dram_j92_boundary_lvs(inout wire P1, P2, P3);
endmodule

module rev_a_dram_bank_lvs_top;
    wire VCC, GND;
    wire D0, D1, D2, D3, D4, D5, D6, D7;
    wire DRAM_A0, DRAM_A1, DRAM_A2, DRAM_A3;
    wire DRAM_A4, DRAM_A5, DRAM_A6, DRAM_A7;
    wire RAS_N, CAS_N, DRAM_WE_N;
    wire U10_P1_NC, U11_P1_NC, U12_P1_NC, U13_P1_NC;
    wire U14_P1_NC, U15_P1_NC, U16_P1_NC, U17_P1_NC;

    rev_a_dram_pins16_lvs U_U10(
        .P1(U10_P1_NC), .P2(D0), .P3(DRAM_WE_N), .P4(RAS_N),
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P8(VCC),
        .P9(DRAM_A7), .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3),
        .P13(DRAM_A6), .P14(D0), .P15(CAS_N), .P16(GND));
    rev_a_dram_pins16_lvs U_U11(
        .P1(U11_P1_NC), .P2(D1), .P3(DRAM_WE_N), .P4(RAS_N),
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P8(VCC),
        .P9(DRAM_A7), .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3),
        .P13(DRAM_A6), .P14(D1), .P15(CAS_N), .P16(GND));
    rev_a_dram_pins16_lvs U_U12(
        .P1(U12_P1_NC), .P2(D2), .P3(DRAM_WE_N), .P4(RAS_N),
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P8(VCC),
        .P9(DRAM_A7), .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3),
        .P13(DRAM_A6), .P14(D2), .P15(CAS_N), .P16(GND));
    rev_a_dram_pins16_lvs U_U13(
        .P1(U13_P1_NC), .P2(D3), .P3(DRAM_WE_N), .P4(RAS_N),
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P8(VCC),
        .P9(DRAM_A7), .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3),
        .P13(DRAM_A6), .P14(D3), .P15(CAS_N), .P16(GND));
    rev_a_dram_pins16_lvs U_U14(
        .P1(U14_P1_NC), .P2(D4), .P3(DRAM_WE_N), .P4(RAS_N),
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P8(VCC),
        .P9(DRAM_A7), .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3),
        .P13(DRAM_A6), .P14(D4), .P15(CAS_N), .P16(GND));
    rev_a_dram_pins16_lvs U_U15(
        .P1(U15_P1_NC), .P2(D5), .P3(DRAM_WE_N), .P4(RAS_N),
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P8(VCC),
        .P9(DRAM_A7), .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3),
        .P13(DRAM_A6), .P14(D5), .P15(CAS_N), .P16(GND));
    rev_a_dram_pins16_lvs U_U16(
        .P1(U16_P1_NC), .P2(D6), .P3(DRAM_WE_N), .P4(RAS_N),
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P8(VCC),
        .P9(DRAM_A7), .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3),
        .P13(DRAM_A6), .P14(D6), .P15(CAS_N), .P16(GND));
    rev_a_dram_pins16_lvs U_U17(
        .P1(U17_P1_NC), .P2(D7), .P3(DRAM_WE_N), .P4(RAS_N),
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P8(VCC),
        .P9(DRAM_A7), .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3),
        .P13(DRAM_A6), .P14(D7), .P15(CAS_N), .P16(GND));

    rev_a_dram_pins2_lvs U_C6(.P1(VCC), .P2(GND));
    rev_a_dram_pins2_lvs U_C7(.P1(VCC), .P2(GND));
    rev_a_dram_pins2_lvs U_C8(.P1(VCC), .P2(GND));
    rev_a_dram_pins2_lvs U_C9(.P1(VCC), .P2(GND));
    rev_a_dram_pins2_lvs U_C10(.P1(VCC), .P2(GND));
    rev_a_dram_pins2_lvs U_C11(.P1(VCC), .P2(GND));
    rev_a_dram_pins2_lvs U_C12(.P1(VCC), .P2(GND));
    rev_a_dram_pins2_lvs U_C13(.P1(VCC), .P2(GND));

    rev_a_dram_cpu_boundary_lvs U_CPU_BOUNDARY(
        .P7(D4), .P8(D3), .P9(D5), .P10(D6),
        .P12(D2), .P13(D7), .P14(D0), .P15(D1));
    rev_a_dram_rom_boundary_lvs U_ROM_BOUNDARY(
        .P11(D0), .P12(D1), .P13(D2), .P15(D3),
        .P16(D4), .P17(D5), .P18(D6), .P19(D7));
    rev_a_dram_mux_boundary_lvs U_U20_BOUNDARY(
        .P4(DRAM_A0), .P7(DRAM_A1), .P9(DRAM_A2), .P12(DRAM_A3));
    rev_a_dram_mux_boundary_lvs U_U21_BOUNDARY(
        .P4(DRAM_A4), .P7(DRAM_A5), .P9(DRAM_A6), .P12(DRAM_A7));
    rev_a_dram_u24_boundary_lvs U_U24_BOUNDARY(
        .P14(RAS_N), .P15(CAS_N), .P16(DRAM_WE_N));
    rev_a_dram_ppi_boundary_lvs U_U30_BOUNDARY(
        .P27(D7), .P28(D6), .P29(D5), .P30(D4),
        .P31(D3), .P32(D2), .P33(D1), .P34(D0));
    rev_a_dram_u41_boundary_lvs U_U41_BOUNDARY(
        .P2(D0), .P3(D1), .P4(D2), .P5(D3),
        .P10(D4), .P11(D5), .P12(D6), .P14(D7));
    rev_a_dram_j91_boundary_lvs U_J91_BOUNDARY(
        .P1(D0), .P2(D1), .P3(D2), .P4(D3),
        .P5(D4), .P6(D5), .P7(D6), .P8(D7));
    rev_a_dram_j92_boundary_lvs U_J92_BOUNDARY(
        .P1(RAS_N), .P2(CAS_N), .P3(DRAM_WE_N));
endmodule

`default_nettype wire
