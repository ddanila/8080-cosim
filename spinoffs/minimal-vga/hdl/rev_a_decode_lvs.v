// VJUGA Rev A staged physical LVS: decode PROM sockets and glue.
//
// Independently authored, empty-bodied physical connectivity. U1, U2, U24,
// U30, J97, and J98 are boundary projections only; their remaining pins belong
// to later stages. Intentional NC pads are declared in the companion map.
`default_nettype none

module rev_a_decode_pins2_lvs(inout wire P1, P2);
endmodule

module rev_a_decode_pins3_lvs(inout wire P1, P2, P3);
endmodule

module rev_a_decode_pins14_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7,
    inout wire P8, P9, P10, P11, P12, P13, P14
);
endmodule

module rev_a_decode_pins16_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8,
    inout wire P9, P10, P11, P12, P13, P14, P15, P16
);
endmodule

module rev_a_decode_pins24_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8,
    inout wire P9, P10, P11, P12, P13, P14, P15, P16,
    inout wire P17, P18, P19, P20, P21, P22, P23, P24
);
endmodule

module rev_a_decode_cpu_boundary_lvs(
    inout wire A11_P1, A12_P2, A13_P3, A14_P4, A15_P5,
    inout wire MREQ_N_P19, IORQ_N_P20, RD_N_P21, WR_N_P22
);
endmodule

module rev_a_decode_rom_boundary_lvs(
    inout wire A14_P1, A12_P2, ROM_CE_N_P20, MEM_RD_N_P22,
    inout wire A11_P23, A13_P26, MEM_WR_N_P27
);
endmodule

module rev_a_decode_u24_boundary_lvs(
    inout wire RAM_CE_N_P3, MEM_RD_N_P4,
    inout wire MEM_WR_N_P5, DECODE_WAIT_N_P13
);
endmodule

module rev_a_decode_ppi_boundary_lvs(
    inout wire IO_RD_N_P5, PPI_CS_N_P6,
    inout wire PC0_P14, PC1_P15, IO_WR_N_P36
);
endmodule

module rev_a_decode_j97_boundary_lvs(
    inout wire A11_P4, A12_P5, A13_P6,
    inout wire A14_P7, A15_P8, MEM_WR_N_P9
);
endmodule

module rev_a_decode_j98_boundary_lvs(
    inout wire MREQ_N_P1, IORQ_N_P2, RD_N_P3, WR_N_P4
);
endmodule

module rev_a_decode_lvs_top;
    wire VCC, GND;
    wire A11, A12, A13, A14, A15;
    wire MREQ_N, IORQ_N, RD_N, WR_N;
    wire ROM_CE_N, RAM_CE_N, PPI_CS_N;
    wire MEM_RD_N, MEM_WR_N, IO_RD_N, IO_WR_N, DECODE_WAIT_N;
    wire DEC_ROM_N, DEC_RAM_N, DEC_REV, DEC_ROE_N, REV_OUT;
    wire RE3_D0, RE3_D1, RE3_D2, RE3_D3;
    wire RE3_D4, RE3_D5, RE3_D6, RE3_D7;
    wire PC0, PC1, PC0_N, PC1_N, MODE_B;
    wire U5_P23_NC, U6_P6_NC, U6_P8_NC, U6_P10_NC, U6_P12_NC;

    rev_a_decode_pins24_lvs U_U5(
        .P1(MREQ_N), .P2(IORQ_N), .P3(RD_N), .P4(WR_N),
        .P5(A13), .P6(A14), .P7(A15), .P8(MODE_B),
        .P9(DEC_ROM_N), .P10(DEC_RAM_N), .P11(DEC_REV), .P12(GND),
        .P13(DEC_ROE_N), .P14(ROM_CE_N), .P15(RAM_CE_N), .P16(PPI_CS_N),
        .P17(MEM_RD_N), .P18(MEM_WR_N), .P19(IO_RD_N), .P20(IO_WR_N),
        .P21(REV_OUT), .P22(DECODE_WAIT_N), .P23(U5_P23_NC), .P24(VCC));

    rev_a_decode_pins16_lvs U_U3(
        .P1(PC1_N), .P2(PC0_N), .P3(A11), .P4(A12),
        .P5(A15), .P6(A14), .P7(A13), .P8(GND),
        .P9(DEC_ROE_N), .P10(DEC_REV), .P11(DEC_RAM_N), .P12(DEC_ROM_N),
        .P13(GND), .P14(GND), .P15(GND), .P16(VCC));

    rev_a_decode_pins16_lvs U_U4(
        .P1(RE3_D0), .P2(RE3_D1), .P3(RE3_D2), .P4(RE3_D3),
        .P5(RE3_D4), .P6(RE3_D5), .P7(RE3_D6), .P8(GND),
        .P9(RE3_D7), .P10(A11), .P11(A12), .P12(A13),
        .P13(A14), .P14(A15), .P15(ROM_CE_N), .P16(VCC));

    rev_a_decode_pins14_lvs U_U6(
        .P1(PC0), .P2(PC0_N), .P3(PC1), .P4(PC1_N),
        .P5(GND), .P6(U6_P6_NC), .P7(GND), .P8(U6_P8_NC),
        .P9(GND), .P10(U6_P10_NC), .P11(GND), .P12(U6_P12_NC),
        .P13(GND), .P14(VCC));

    rev_a_decode_pins3_lvs U_J94(.P1(VCC), .P2(MODE_B), .P3(GND));
    rev_a_decode_pins14_lvs U_J95(
        .P1(DEC_ROM_N), .P2(DEC_RAM_N), .P3(DEC_REV), .P4(DEC_ROE_N),
        .P5(RE3_D0), .P6(RE3_D1), .P7(RE3_D2), .P8(RE3_D3),
        .P9(RE3_D4), .P10(RE3_D5), .P11(RE3_D6), .P12(RE3_D7),
        .P13(REV_OUT), .P14(GND));

    rev_a_decode_pins2_lvs U_R32(.P1(VCC), .P2(DEC_ROM_N));
    rev_a_decode_pins2_lvs U_R33(.P1(VCC), .P2(DEC_RAM_N));
    rev_a_decode_pins2_lvs U_R34(.P1(VCC), .P2(DEC_REV));
    rev_a_decode_pins2_lvs U_R35(.P1(VCC), .P2(DEC_ROE_N));
    rev_a_decode_pins2_lvs U_R36(.P1(VCC), .P2(RE3_D0));
    rev_a_decode_pins2_lvs U_R37(.P1(VCC), .P2(RE3_D1));
    rev_a_decode_pins2_lvs U_R38(.P1(VCC), .P2(RE3_D2));
    rev_a_decode_pins2_lvs U_R39(.P1(VCC), .P2(RE3_D3));
    rev_a_decode_pins2_lvs U_R40(.P1(VCC), .P2(RE3_D4));
    rev_a_decode_pins2_lvs U_R41(.P1(VCC), .P2(RE3_D5));
    rev_a_decode_pins2_lvs U_R42(.P1(VCC), .P2(RE3_D6));
    rev_a_decode_pins2_lvs U_R43(.P1(VCC), .P2(RE3_D7));
    rev_a_decode_pins2_lvs U_R44(.P1(MODE_B), .P2(GND));
    rev_a_decode_pins2_lvs U_C26(.P1(VCC), .P2(GND));
    rev_a_decode_pins2_lvs U_C27(.P1(VCC), .P2(GND));
    rev_a_decode_pins2_lvs U_C28(.P1(VCC), .P2(GND));

    rev_a_decode_cpu_boundary_lvs U_CPU_BOUNDARY(
        .A11_P1(A11), .A12_P2(A12), .A13_P3(A13), .A14_P4(A14), .A15_P5(A15),
        .MREQ_N_P19(MREQ_N), .IORQ_N_P20(IORQ_N), .RD_N_P21(RD_N), .WR_N_P22(WR_N));
    rev_a_decode_rom_boundary_lvs U_ROM_BOUNDARY(
        .A14_P1(A14), .A12_P2(A12), .ROM_CE_N_P20(ROM_CE_N),
        .MEM_RD_N_P22(MEM_RD_N), .A11_P23(A11), .A13_P26(A13),
        .MEM_WR_N_P27(MEM_WR_N));
    rev_a_decode_u24_boundary_lvs U_U24_BOUNDARY(
        .RAM_CE_N_P3(RAM_CE_N), .MEM_RD_N_P4(MEM_RD_N),
        .MEM_WR_N_P5(MEM_WR_N), .DECODE_WAIT_N_P13(DECODE_WAIT_N));
    rev_a_decode_ppi_boundary_lvs U_PPI_BOUNDARY(
        .IO_RD_N_P5(IO_RD_N), .PPI_CS_N_P6(PPI_CS_N),
        .PC0_P14(PC0), .PC1_P15(PC1), .IO_WR_N_P36(IO_WR_N));
    rev_a_decode_j97_boundary_lvs U_J97_BOUNDARY(
        .A11_P4(A11), .A12_P5(A12), .A13_P6(A13),
        .A14_P7(A14), .A15_P8(A15), .MEM_WR_N_P9(MEM_WR_N));
    rev_a_decode_j98_boundary_lvs U_J98_BOUNDARY(
        .MREQ_N_P1(MREQ_N), .IORQ_N_P2(IORQ_N), .RD_N_P3(RD_N), .WR_N_P4(WR_N));
endmodule

`default_nettype wire
