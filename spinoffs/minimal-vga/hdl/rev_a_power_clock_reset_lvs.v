// VJUGA Rev A staged physical LVS: POWER + CLOCK_RESET blocks.
//
// This is an independently authored, empty-bodied structural netlist. It
// describes physical pin connectivity only; the booting twin remains
// vjuga_juku_top.v. U_CPU_BOUNDARY supplies representative board-side boundary
// endpoints so CLK and RESET_N cannot vanish as one-ended projected nets.
`default_nettype none

module rev_a_two_pin_lvs(inout wire P1, P2);
endmodule

module rev_a_power_terminal_lvs(inout wire P1, P2);
endmodule

module rev_a_usb_c_power_lvs(
    inout wire CC1_A5, CC2_B5,
    inout wire VBUS_A9, VBUS_B9,
    inout wire GND_A12, GND_B12, SHIELD_S1
);
endmodule

module rev_a_power_debug_lvs(
    inout wire VCC_P1, GND_P2, PWR_OK_P3, VCC_RAW_P4
);
endmodule

module rev_a_oscillator_lvs(
    inout wire OE_P1, GND_P7, CLK_P8, VCC_P14
);
endmodule

module rev_a_reset_supervisor_lvs(
    inout wire GND_P1, RESET_N_P2, VCC_P3
);
endmodule

module rev_a_cpu_boundary_lvs(
    inout wire CLK_P6, VCC_P11, RESET_N_P26, GND_P29
);
endmodule

module rev_a_power_clock_reset_lvs_top;
    wire VCC_RAW, VCC, GND;
    wire USB_CC1, USB_CC2, PWR_OK;
    wire OSC_OE_N, CLK, RESET_N;

    rev_a_power_terminal_lvs U_J1(
        .P1(VCC_RAW), .P2(GND));

    rev_a_usb_c_power_lvs U_J3(
        .CC1_A5(USB_CC1), .CC2_B5(USB_CC2),
        .VBUS_A9(VCC_RAW), .VBUS_B9(VCC_RAW),
        .GND_A12(GND), .GND_B12(GND), .SHIELD_S1(GND));

    rev_a_two_pin_lvs U_R30(.P1(USB_CC1), .P2(GND));
    rev_a_two_pin_lvs U_R31(.P1(USB_CC2), .P2(GND));
    rev_a_two_pin_lvs U_F1(.P1(VCC_RAW), .P2(VCC));
    rev_a_two_pin_lvs U_D1(.P1(VCC), .P2(GND));
    rev_a_two_pin_lvs U_C50(.P1(VCC), .P2(GND));
    rev_a_two_pin_lvs U_R6(.P1(VCC), .P2(PWR_OK));

    rev_a_power_debug_lvs U_J93(
        .VCC_P1(VCC), .GND_P2(GND),
        .PWR_OK_P3(PWR_OK), .VCC_RAW_P4(VCC_RAW));

    rev_a_oscillator_lvs U_U50(
        .OE_P1(OSC_OE_N), .GND_P7(GND), .CLK_P8(CLK), .VCC_P14(VCC));
    rev_a_reset_supervisor_lvs U_U51(
        .GND_P1(GND), .RESET_N_P2(RESET_N), .VCC_P3(VCC));
    rev_a_two_pin_lvs U_R4(.P1(VCC), .P2(OSC_OE_N));
    rev_a_two_pin_lvs U_R5(.P1(VCC), .P2(RESET_N));
    rev_a_two_pin_lvs U_J96(.P1(OSC_OE_N), .P2(GND));
    rev_a_two_pin_lvs U_C24(.P1(VCC), .P2(GND));
    rev_a_two_pin_lvs U_C25(.P1(VCC), .P2(GND));

    rev_a_cpu_boundary_lvs U_CPU_BOUNDARY(
        .CLK_P6(CLK), .VCC_P11(VCC),
        .RESET_N_P26(RESET_N), .GND_P29(GND));
endmodule

`default_nettype wire
