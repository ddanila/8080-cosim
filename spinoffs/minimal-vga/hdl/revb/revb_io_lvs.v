// VJUGA rev B — I/O card structural LVS netlist (TD.9.2). Empty-bodied modules for
// the POPULATED logic ICs (8251 USART + I/O-select GAL); the B3 DNP parts
// (8255/8259/74148) are verified by D1.18 completeness + the D1.26 wiring assertion
// in check_revb_boards.py, not full LVS (D1.22). The compared nets between these two
// mapped instances are UART_CS_N and IO_RESET. Port names = CHIP_TYPES net names.
`default_nettype none

module usart_8251_lvs(
    inout  wire [7:0] D,
    input  wire       RX, BAUDCLK, WR_N, UART_CS_N, A0, RD_N, CLK, IO_RESET,
    output wire       SER_RXRDY, SER_TXRDY, TX
);
endmodule

module gal16v8_iosel_lvs(
    // scalar A2..A7 (a vector would canonicalize by position -> A0..A5 and mis-map)
    input  wire        IORQ_N, A2, A3, A4, A5, A6, A7, RESET_N, RD_N, WR_N, M1_N, PIC_INT,
    output wire        PIC_CS_N, PPI_CS_N, UART_CS_N, IO_RESET, INT_N, INTA_N
);
endmodule

module revb_io_lvs_top;
    wire [7:0] D;
    wire RX, BAUDCLK, WR_N, UART_CS_N, A0, RD_N, CLK, IO_RESET;
    wire SER_RXRDY, SER_TXRDY, TX;
    wire IORQ_N, A2, A3, A4, A5, A6, A7, RESET_N, M1_N, PIC_INT;
    wire PIC_CS_N, PPI_CS_N, INT_N, INTA_N;

    usart_8251_lvs U_UART(
        .D(D), .RX(RX), .BAUDCLK(BAUDCLK), .WR_N(WR_N), .UART_CS_N(UART_CS_N),
        .A0(A0), .RD_N(RD_N), .CLK(CLK), .IO_RESET(IO_RESET),
        .SER_RXRDY(SER_RXRDY), .SER_TXRDY(SER_TXRDY), .TX(TX));

    gal16v8_iosel_lvs U_IOSEL(
        .IORQ_N(IORQ_N), .A2(A2), .A3(A3), .A4(A4), .A5(A5), .A6(A6), .A7(A7),
        .RESET_N(RESET_N), .RD_N(RD_N), .WR_N(WR_N), .M1_N(M1_N), .PIC_INT(PIC_INT),
        .PIC_CS_N(PIC_CS_N), .PPI_CS_N(PPI_CS_N), .UART_CS_N(UART_CS_N),
        .IO_RESET(IO_RESET), .INT_N(INT_N), .INTA_N(INTA_N));
endmodule
`default_nettype wire
