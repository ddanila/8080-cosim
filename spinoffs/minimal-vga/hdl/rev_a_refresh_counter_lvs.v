// VJUGA Rev A staged physical LVS: complete U22 74HCT393 refresh counter.
//
// U22 and C16 are complete owned instances. The remaining cells are exact
// boundary projections for CLK and all eight refresh-row nets.
`default_nettype none

module rev_a_refresh_pins2_lvs(inout wire P1, P2);
endmodule

module rev_a_refresh_pins14_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7,
    inout wire P8, P9, P10, P11, P12, P13, P14
);
endmodule

module rev_a_refresh_cpu_boundary_lvs(inout wire P6);
endmodule

module rev_a_refresh_mux_boundary_lvs(inout wire P3, P6, P10, P13);
endmodule

module rev_a_refresh_u23_boundary_lvs(inout wire P1);
endmodule

module rev_a_refresh_u24_boundary_lvs(
    inout wire P1, P8, P9, P10, P11
);
endmodule

module rev_a_refresh_u50_boundary_lvs(inout wire P8);
endmodule

module rev_a_refresh_r26_boundary_lvs(inout wire P1);
endmodule

module rev_a_refresh_header_boundary_lvs(inout wire P10);
endmodule

module rev_a_refresh_counter_lvs_top;
    wire VCC, GND, CLK;
    wire REFRESH_ROW0, REFRESH_ROW1, REFRESH_ROW2, REFRESH_ROW3;
    wire REFRESH_ROW4, REFRESH_ROW5, REFRESH_ROW6, REFRESH_ROW7;

    // 74HCT393 DIP-14: first clock/reset on pins 1/2, first Q0-Q3 on
    // pins 3-6, GND on pin 7, second Q3-Q0 on pins 8-11, second
    // reset/clock on pins 12/13, and VCC on pin 14.
    rev_a_refresh_pins14_lvs U_U22(
        .P1(CLK), .P2(GND),
        .P3(REFRESH_ROW0), .P4(REFRESH_ROW1),
        .P5(REFRESH_ROW2), .P6(REFRESH_ROW3),
        .P7(GND),
        .P8(REFRESH_ROW7), .P9(REFRESH_ROW6),
        .P10(REFRESH_ROW5), .P11(REFRESH_ROW4),
        .P12(GND), .P13(REFRESH_ROW3), .P14(VCC));
    rev_a_refresh_pins2_lvs U_C16(.P1(VCC), .P2(GND));

    rev_a_refresh_cpu_boundary_lvs U_CPU_BOUNDARY(.P6(CLK));
    rev_a_refresh_mux_boundary_lvs U_U20_BOUNDARY(
        .P3(REFRESH_ROW0), .P6(REFRESH_ROW1),
        .P10(REFRESH_ROW2), .P13(REFRESH_ROW3));
    rev_a_refresh_mux_boundary_lvs U_U21_BOUNDARY(
        .P3(REFRESH_ROW4), .P6(REFRESH_ROW5),
        .P10(REFRESH_ROW6), .P13(REFRESH_ROW7));
    rev_a_refresh_u23_boundary_lvs U_U23_BOUNDARY(.P1(CLK));
    rev_a_refresh_u24_boundary_lvs U_U24_BOUNDARY(
        .P1(CLK),
        .P8(REFRESH_ROW0), .P9(REFRESH_ROW1),
        .P10(REFRESH_ROW2), .P11(REFRESH_ROW3));
    rev_a_refresh_u50_boundary_lvs U_U50_BOUNDARY(.P8(CLK));
    rev_a_refresh_r26_boundary_lvs U_R26_BOUNDARY(.P1(CLK));
    rev_a_refresh_header_boundary_lvs U_J90_BOUNDARY(.P10(CLK));
    rev_a_refresh_header_boundary_lvs U_J92_BOUNDARY(.P10(CLK));
endmodule

`default_nettype wire
