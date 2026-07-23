// VJUGA Rev A staged physical LVS: complete U24 DRAM-timing GAL.
//
// U24 and C18 are complete owned instances. The remaining cells are exact
// boundary projections for all 19 non-power nets touched by U24. Functional
// behavior remains guarded independently by u24_dram_timing.v and its testbench.
`default_nettype none

module rev_a_timing_pins2_lvs(inout wire P1, P2);
endmodule

module rev_a_timing_pins24_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8,
    inout wire P9, P10, P11, P12, P13, P14, P15, P16,
    inout wire P17, P18, P19, P20, P21, P22, P23, P24
);
endmodule

module rev_a_timing_cpu_boundary_lvs(inout wire P6, P24, P26, P28);
endmodule

module rev_a_timing_rom_boundary_lvs(inout wire P22, P27);
endmodule

module rev_a_timing_decode_boundary_lvs(
    inout wire P15, P17, P18, P22
);
endmodule

module rev_a_timing_dram_boundary_lvs(inout wire P3, P4, P15);
endmodule

module rev_a_timing_u20_boundary_lvs(
    inout wire P1, P3, P6, P10, P13
);
endmodule

module rev_a_timing_u22_boundary_lvs(
    inout wire P1, P3, P4, P5, P6, P13
);
endmodule

module rev_a_timing_u40_boundary_lvs(inout wire P2, P7, P8);
endmodule

module rev_a_timing_j92_boundary_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7, P8, P10
);
endmodule

module rev_a_timing_j98_boundary_lvs(inout wire P6, P7);
endmodule

module rev_a_timing_pin1_boundary_lvs(inout wire P1);
endmodule

module rev_a_timing_pin2_boundary_lvs(inout wire P2);
endmodule

module rev_a_timing_pin8_boundary_lvs(inout wire P8);
endmodule

module rev_a_timing_pin9_boundary_lvs(inout wire P9);
endmodule

module rev_a_timing_pin10_boundary_lvs(inout wire P10);
endmodule

module rev_a_timing_pin35_boundary_lvs(inout wire P35);
endmodule

module rev_a_dram_timing_lvs_top;
    wire VCC, GND;
    wire CLK, RESET_N, RAM_CE_N, MEM_RD_N, MEM_WR_N, RFSH_N;
    wire VIDEO_REQ, VIDEO_ACK, DECODE_WAIT_N, WAIT_N;
    wire REFRESH_ROW0, REFRESH_ROW1, REFRESH_ROW2, REFRESH_ROW3;
    wire RAS_N, CAS_N, DRAM_WE_N, ADDRMUX_SEL, REFRESH_TICK;
    wire U24_P21_NC, U24_P22_NC, U24_P23_NC;

    // GAL22V10 DIP-24: twelve inputs occupy pins 1-11 and 13; ten output
    // macrocells occupy pins 14-23. The state-feedback macrocells on pins
    // 21-23 have no external loads and are explicit PCB no-connects.
    rev_a_timing_pins24_lvs U_U24(
        .P1(CLK), .P2(RESET_N), .P3(RAM_CE_N),
        .P4(MEM_RD_N), .P5(MEM_WR_N), .P6(RFSH_N),
        .P7(VIDEO_REQ),
        .P8(REFRESH_ROW0), .P9(REFRESH_ROW1),
        .P10(REFRESH_ROW2), .P11(REFRESH_ROW3),
        .P12(GND), .P13(DECODE_WAIT_N),
        .P14(RAS_N), .P15(CAS_N), .P16(DRAM_WE_N),
        .P17(ADDRMUX_SEL), .P18(WAIT_N), .P19(VIDEO_ACK),
        .P20(REFRESH_TICK),
        .P21(U24_P21_NC), .P22(U24_P22_NC), .P23(U24_P23_NC),
        .P24(VCC));
    rev_a_timing_pins2_lvs U_C18(.P1(VCC), .P2(GND));

    rev_a_timing_cpu_boundary_lvs U_CPU_BOUNDARY(
        .P6(CLK), .P24(WAIT_N), .P26(RESET_N), .P28(RFSH_N));
    rev_a_timing_rom_boundary_lvs U_ROM_BOUNDARY(
        .P22(MEM_RD_N), .P27(MEM_WR_N));
    rev_a_timing_decode_boundary_lvs U_U5_BOUNDARY(
        .P15(RAM_CE_N), .P17(MEM_RD_N),
        .P18(MEM_WR_N), .P22(DECODE_WAIT_N));

    rev_a_timing_dram_boundary_lvs U_U10_BOUNDARY(
        .P3(DRAM_WE_N), .P4(RAS_N), .P15(CAS_N));
    rev_a_timing_dram_boundary_lvs U_U11_BOUNDARY(
        .P3(DRAM_WE_N), .P4(RAS_N), .P15(CAS_N));
    rev_a_timing_dram_boundary_lvs U_U12_BOUNDARY(
        .P3(DRAM_WE_N), .P4(RAS_N), .P15(CAS_N));
    rev_a_timing_dram_boundary_lvs U_U13_BOUNDARY(
        .P3(DRAM_WE_N), .P4(RAS_N), .P15(CAS_N));
    rev_a_timing_dram_boundary_lvs U_U14_BOUNDARY(
        .P3(DRAM_WE_N), .P4(RAS_N), .P15(CAS_N));
    rev_a_timing_dram_boundary_lvs U_U15_BOUNDARY(
        .P3(DRAM_WE_N), .P4(RAS_N), .P15(CAS_N));
    rev_a_timing_dram_boundary_lvs U_U16_BOUNDARY(
        .P3(DRAM_WE_N), .P4(RAS_N), .P15(CAS_N));
    rev_a_timing_dram_boundary_lvs U_U17_BOUNDARY(
        .P3(DRAM_WE_N), .P4(RAS_N), .P15(CAS_N));

    rev_a_timing_u20_boundary_lvs U_U20_BOUNDARY(
        .P1(ADDRMUX_SEL), .P3(REFRESH_ROW0), .P6(REFRESH_ROW1),
        .P10(REFRESH_ROW2), .P13(REFRESH_ROW3));
    rev_a_timing_pin1_boundary_lvs U_U21_BOUNDARY(.P1(ADDRMUX_SEL));
    rev_a_timing_u22_boundary_lvs U_U22_BOUNDARY(
        .P1(CLK), .P3(REFRESH_ROW0), .P4(REFRESH_ROW1),
        .P5(REFRESH_ROW2), .P6(REFRESH_ROW3), .P13(REFRESH_ROW3));
    rev_a_timing_pin1_boundary_lvs U_U23_BOUNDARY(.P1(CLK));

    rev_a_timing_pin35_boundary_lvs U_U30_BOUNDARY(.P35(RESET_N));
    rev_a_timing_u40_boundary_lvs U_U40_BOUNDARY(
        .P2(RESET_N), .P7(VIDEO_REQ), .P8(VIDEO_ACK));
    rev_a_timing_pin9_boundary_lvs U_U41_BOUNDARY(.P9(RESET_N));
    rev_a_timing_pin8_boundary_lvs U_U50_BOUNDARY(.P8(CLK));
    rev_a_timing_pin2_boundary_lvs U_U51_BOUNDARY(.P2(RESET_N));

    rev_a_timing_pin1_boundary_lvs U_D7_BOUNDARY(.P1(RFSH_N));
    rev_a_timing_pin1_boundary_lvs U_R26_BOUNDARY(.P1(CLK));
    rev_a_timing_pin1_boundary_lvs U_R27_BOUNDARY(.P1(RESET_N));
    rev_a_timing_pin2_boundary_lvs U_R5_BOUNDARY(.P2(RESET_N));
    rev_a_timing_pin10_boundary_lvs U_J90_BOUNDARY(.P10(CLK));
    rev_a_timing_pin10_boundary_lvs U_J91_BOUNDARY(.P10(RESET_N));
    rev_a_timing_j92_boundary_lvs U_J92_BOUNDARY(
        .P1(RAS_N), .P2(CAS_N), .P3(DRAM_WE_N),
        .P4(ADDRMUX_SEL), .P5(REFRESH_TICK),
        .P6(VIDEO_REQ), .P7(VIDEO_ACK), .P8(WAIT_N), .P10(CLK));
    rev_a_timing_pin9_boundary_lvs U_J97_BOUNDARY(.P9(MEM_WR_N));
    rev_a_timing_j98_boundary_lvs U_J98_BOUNDARY(
        .P6(RFSH_N), .P7(WAIT_N));
endmodule

`default_nettype wire
