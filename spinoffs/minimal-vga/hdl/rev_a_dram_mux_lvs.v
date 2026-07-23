// VJUGA Rev A staged physical LVS: complete 74HCT157 DRAM address muxes.
//
// U20/U21 and C14/C15 are complete owned instances. The remaining cells are
// exact boundary projections for all 25 non-power nets touched by the muxes.
`default_nettype none

module rev_a_mux_pins2_lvs(inout wire P1, P2);
endmodule

module rev_a_mux_pins16_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8,
    inout wire P9, P10, P11, P12, P13, P14, P15, P16
);
endmodule

module rev_a_mux_cpu_boundary_lvs(
    inout wire P30, P31, P32, P33, P34, P35, P36, P37
);
endmodule

module rev_a_mux_rom_boundary_lvs(
    inout wire P3, P4, P5, P6, P7, P8, P9, P10
);
endmodule

module rev_a_mux_ppi_boundary_lvs(inout wire P8, P9);
endmodule

module rev_a_mux_j90_boundary_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8
);
endmodule

module rev_a_mux_dram_boundary_lvs(
    inout wire P5, P6, P7, P9, P10, P11, P12, P13
);
endmodule

module rev_a_mux_u22_boundary_lvs(
    inout wire P3, P4, P5, P6, P8, P9, P10, P11
);
endmodule

module rev_a_mux_u24_boundary_lvs(
    inout wire P8, P9, P10, P11, P17
);
endmodule

module rev_a_mux_j92_boundary_lvs(inout wire P4);
endmodule

module rev_a_dram_mux_lvs_top;
    wire VCC, GND;
    wire A0, A1, A2, A3, A4, A5, A6, A7;
    wire DRAM_A0, DRAM_A1, DRAM_A2, DRAM_A3;
    wire DRAM_A4, DRAM_A5, DRAM_A6, DRAM_A7;
    wire ADDRMUX_SEL;
    wire REFRESH_ROW0, REFRESH_ROW1, REFRESH_ROW2, REFRESH_ROW3;
    wire REFRESH_ROW4, REFRESH_ROW5, REFRESH_ROW6, REFRESH_ROW7;

    // 74HCT157 DIP-16: pin 1 select, A/B/Y groups on 2-14,
    // active-low enable on pin 15, and GND/VCC on pins 8/16.
    rev_a_mux_pins16_lvs U_U20(
        .P1(ADDRMUX_SEL),
        .P2(A0), .P3(REFRESH_ROW0), .P4(DRAM_A0),
        .P5(A1), .P6(REFRESH_ROW1), .P7(DRAM_A1),
        .P8(GND),
        .P9(DRAM_A2), .P10(REFRESH_ROW2), .P11(A2),
        .P12(DRAM_A3), .P13(REFRESH_ROW3), .P14(A3),
        .P15(GND), .P16(VCC));
    rev_a_mux_pins16_lvs U_U21(
        .P1(ADDRMUX_SEL),
        .P2(A4), .P3(REFRESH_ROW4), .P4(DRAM_A4),
        .P5(A5), .P6(REFRESH_ROW5), .P7(DRAM_A5),
        .P8(GND),
        .P9(DRAM_A6), .P10(REFRESH_ROW6), .P11(A6),
        .P12(DRAM_A7), .P13(REFRESH_ROW7), .P14(A7),
        .P15(GND), .P16(VCC));

    rev_a_mux_pins2_lvs U_C14(.P1(VCC), .P2(GND));
    rev_a_mux_pins2_lvs U_C15(.P1(VCC), .P2(GND));

    rev_a_mux_cpu_boundary_lvs U_CPU_BOUNDARY(
        .P30(A0), .P31(A1), .P32(A2), .P33(A3),
        .P34(A4), .P35(A5), .P36(A6), .P37(A7));
    rev_a_mux_rom_boundary_lvs U_ROM_BOUNDARY(
        .P3(A7), .P4(A6), .P5(A5), .P6(A4),
        .P7(A3), .P8(A2), .P9(A1), .P10(A0));
    rev_a_mux_ppi_boundary_lvs U_PPI_BOUNDARY(.P8(A1), .P9(A0));
    rev_a_mux_j90_boundary_lvs U_J90_BOUNDARY(
        .P1(A0), .P2(A1), .P3(A2), .P4(A3),
        .P5(A4), .P6(A5), .P7(A6), .P8(A7));

    rev_a_mux_dram_boundary_lvs U_U10_BOUNDARY(
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P9(DRAM_A7),
        .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3), .P13(DRAM_A6));
    rev_a_mux_dram_boundary_lvs U_U11_BOUNDARY(
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P9(DRAM_A7),
        .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3), .P13(DRAM_A6));
    rev_a_mux_dram_boundary_lvs U_U12_BOUNDARY(
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P9(DRAM_A7),
        .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3), .P13(DRAM_A6));
    rev_a_mux_dram_boundary_lvs U_U13_BOUNDARY(
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P9(DRAM_A7),
        .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3), .P13(DRAM_A6));
    rev_a_mux_dram_boundary_lvs U_U14_BOUNDARY(
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P9(DRAM_A7),
        .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3), .P13(DRAM_A6));
    rev_a_mux_dram_boundary_lvs U_U15_BOUNDARY(
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P9(DRAM_A7),
        .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3), .P13(DRAM_A6));
    rev_a_mux_dram_boundary_lvs U_U16_BOUNDARY(
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P9(DRAM_A7),
        .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3), .P13(DRAM_A6));
    rev_a_mux_dram_boundary_lvs U_U17_BOUNDARY(
        .P5(DRAM_A0), .P6(DRAM_A2), .P7(DRAM_A1), .P9(DRAM_A7),
        .P10(DRAM_A5), .P11(DRAM_A4), .P12(DRAM_A3), .P13(DRAM_A6));

    rev_a_mux_u22_boundary_lvs U_U22_BOUNDARY(
        .P3(REFRESH_ROW0), .P4(REFRESH_ROW1),
        .P5(REFRESH_ROW2), .P6(REFRESH_ROW3),
        .P8(REFRESH_ROW7), .P9(REFRESH_ROW6),
        .P10(REFRESH_ROW5), .P11(REFRESH_ROW4));
    rev_a_mux_u24_boundary_lvs U_U24_BOUNDARY(
        .P8(REFRESH_ROW0), .P9(REFRESH_ROW1),
        .P10(REFRESH_ROW2), .P11(REFRESH_ROW3),
        .P17(ADDRMUX_SEL));
    rev_a_mux_j92_boundary_lvs U_J92_BOUNDARY(.P4(ADDRMUX_SEL));
endmodule

`default_nettype wire
