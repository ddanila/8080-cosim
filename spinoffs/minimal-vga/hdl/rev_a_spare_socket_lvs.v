// VJUGA Rev A staged physical LVS: complete empty U23 spare socket.
//
// U23 and C17 are complete owned instances. The remaining cells are exact
// boundary projections for CLK. The eight U23 output pads deliberately remain
// one-ended here and are independently required to be physical NC declarations.
`default_nettype none

module rev_a_spare_pins2_lvs(inout wire P1, P2);
endmodule

module rev_a_spare_pins14_lvs(
    inout wire P1, P2, P3, P4, P5, P6, P7,
    inout wire P8, P9, P10, P11, P12, P13, P14
);
endmodule

module rev_a_spare_pin1_boundary_lvs(inout wire P1);
endmodule

module rev_a_spare_pin6_boundary_lvs(inout wire P6);
endmodule

module rev_a_spare_pin8_boundary_lvs(inout wire P8);
endmodule

module rev_a_spare_pin10_boundary_lvs(inout wire P10);
endmodule

module rev_a_spare_socket_lvs_top;
    wire VCC, GND, CLK;
    wire U23_P3_NC, U23_P4_NC, U23_P5_NC, U23_P6_NC;
    wire U23_P8_NC, U23_P9_NC, U23_P10_NC, U23_P11_NC;

    // The spare footprint retains the 74HCT393 DIP-14 pinout so a probe-only
    // part can be fitted deliberately. In production U23 is DNP: the first
    // clock remains observable, both resets and the second clock are grounded,
    // and every counter output is NC.
    rev_a_spare_pins14_lvs U_U23(
        .P1(CLK), .P2(GND),
        .P3(U23_P3_NC), .P4(U23_P4_NC),
        .P5(U23_P5_NC), .P6(U23_P6_NC),
        .P7(GND),
        .P8(U23_P8_NC), .P9(U23_P9_NC),
        .P10(U23_P10_NC), .P11(U23_P11_NC),
        .P12(GND), .P13(GND), .P14(VCC));
    rev_a_spare_pins2_lvs U_C17(.P1(VCC), .P2(GND));

    rev_a_spare_pin6_boundary_lvs U_CPU_BOUNDARY(.P6(CLK));
    rev_a_spare_pin1_boundary_lvs U_U22_BOUNDARY(.P1(CLK));
    rev_a_spare_pin1_boundary_lvs U_U24_BOUNDARY(.P1(CLK));
    rev_a_spare_pin8_boundary_lvs U_U50_BOUNDARY(.P8(CLK));
    rev_a_spare_pin1_boundary_lvs U_R26_BOUNDARY(.P1(CLK));
    rev_a_spare_pin10_boundary_lvs U_J90_BOUNDARY(.P10(CLK));
    rev_a_spare_pin10_boundary_lvs U_J92_BOUNDARY(.P10(CLK));
endmodule

`default_nettype wire
