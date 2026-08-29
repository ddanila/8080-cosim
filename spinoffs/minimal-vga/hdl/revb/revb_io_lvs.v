// VJUGA rev B expanded I/O card structural LVS netlist (R5.I4).
// Independently states every populated digital package connection U1..U9.
`default_nettype none

module usart_8251_lvs(inout wire [7:0] D, input wire RX, BAUDCLK, WR_N,
    UART_CS_N, A0, RD_N, CLK, IO_RESET, output wire SER_RXRDY, SER_TXRDY, TX); endmodule
module gal22v10_iosel_lvs(input wire IORQ_N,A2,A3,A4,A5,A6,A7,RESET_N,M1_N,WR_N,PIC_INT,
    output wire PIC_CS_N,PPI_CS_N,UART_CS_N,PIT_CS_N,POST_CLK,IO_RESET,INT_N,INTA_N); endmodule
module osc_baud_lvs(output wire BAUD_MASTER); endmodule
module ppi_8255_lvs(inout wire [7:0] D, input wire RD_N,PPI_CS_N,A1,A0,IO_RESET,WR_N,
    output wire MODE0,MODE1,KBD_COL0,KBD_COL1,KBD_COL2,KBD_COL3,KBD_COL4,KBD_COL5,KBD_COL6,KBD_COL7,
    input wire KBD_ENC0,KBD_ENC1,KBD_ENC2,KBD_ENC_GS); endmodule
module enc_74148_lvs(input wire KBD_ROW0,KBD_ROW1,KBD_ROW2,KBD_ROW3,KBD_ROW4,KBD_ROW5,KBD_ROW6,KBD_ROW7,
    output wire KBD_ENC0,KBD_ENC1,KBD_ENC2,KBD_ENC_GS); endmodule
module pic_8259_lvs(inout wire [7:0] D, input wire PIC_CS_N,WR_N,RD_N,FRAME_TICK,
    SER_TXRDY,SER_RXRDY,IRQ_B,IRQ_A,INTA_N,A0, output wire PIC_INT); endmodule
module ttl_393_baud_lvs(input wire BAUD_MASTER, output wire PIT_CLK0,BAUD_19200,BAUD_9600); endmodule
module pit_8253_lvs(inout wire [7:0] D, input wire PIT_CLK0,CLK,A0,A1,PIT_CS_N,RD_N,WR_N,
    output wire PIT_BAUD,PIT_SOUND,PIT_OUT2_TP); endmodule
module act_273_post_lvs(input wire RESET_N,POST_CLK,input wire [7:0] D,output wire [7:0] POST_Q); endmodule

module revb_io_lvs_top;
    wire [7:0] D, POST_Q;
    wire [7:0] KBD_COL, KBD_ROW;
    wire [2:0] KBD_ENC;
    wire A0,A1,A2,A3,A4,A5,A6,A7,CLK,RESET_N,M1_N,IORQ_N,RD_N,WR_N;
    wire RX,TX,FRAME_TICK,IRQ_A,IRQ_B,INT_N;
    wire BAUD_MASTER,PIT_CLK0,BAUD_19200,BAUD_9600,BAUDCLK;
    wire PIC_CS_N,PPI_CS_N,UART_CS_N,PIT_CS_N,POST_CLK,IO_RESET,INTA_N,PIC_INT;
    wire SER_RXRDY,SER_TXRDY,MODE0,MODE1,KBD_ENC_GS;
    wire PIT_BAUD,PIT_SOUND,PIT_OUT2_TP;

    usart_8251_lvs U_UART(.D(D),.RX(RX),.BAUDCLK(BAUDCLK),.WR_N(WR_N),
        .UART_CS_N(UART_CS_N),.A0(A0),.RD_N(RD_N),.CLK(CLK),.IO_RESET(IO_RESET),
        .SER_RXRDY(SER_RXRDY),.SER_TXRDY(SER_TXRDY),.TX(TX));
    gal22v10_iosel_lvs U_IOSEL(.IORQ_N(IORQ_N),.A2(A2),.A3(A3),.A4(A4),.A5(A5),
        .A6(A6),.A7(A7),.RESET_N(RESET_N),.M1_N(M1_N),.WR_N(WR_N),.PIC_INT(PIC_INT),
        .PIC_CS_N(PIC_CS_N),.PPI_CS_N(PPI_CS_N),.UART_CS_N(UART_CS_N),
        .PIT_CS_N(PIT_CS_N),.POST_CLK(POST_CLK),.IO_RESET(IO_RESET),.INT_N(INT_N),.INTA_N(INTA_N));
    osc_baud_lvs U_BAUD_OSC(.BAUD_MASTER(BAUD_MASTER));
    ppi_8255_lvs U_PPI(.D(D),.RD_N(RD_N),.PPI_CS_N(PPI_CS_N),.A1(A1),.A0(A0),
        .IO_RESET(IO_RESET),.WR_N(WR_N),.MODE0(MODE0),.MODE1(MODE1),
        .KBD_COL0(KBD_COL[0]),.KBD_COL1(KBD_COL[1]),.KBD_COL2(KBD_COL[2]),.KBD_COL3(KBD_COL[3]),
        .KBD_COL4(KBD_COL[4]),.KBD_COL5(KBD_COL[5]),.KBD_COL6(KBD_COL[6]),.KBD_COL7(KBD_COL[7]),
        .KBD_ENC0(KBD_ENC[0]),.KBD_ENC1(KBD_ENC[1]),.KBD_ENC2(KBD_ENC[2]),.KBD_ENC_GS(KBD_ENC_GS));
    enc_74148_lvs U_KENC(.KBD_ROW0(KBD_ROW[0]),.KBD_ROW1(KBD_ROW[1]),.KBD_ROW2(KBD_ROW[2]),
        .KBD_ROW3(KBD_ROW[3]),.KBD_ROW4(KBD_ROW[4]),.KBD_ROW5(KBD_ROW[5]),
        .KBD_ROW6(KBD_ROW[6]),.KBD_ROW7(KBD_ROW[7]),.KBD_ENC0(KBD_ENC[0]),
        .KBD_ENC1(KBD_ENC[1]),.KBD_ENC2(KBD_ENC[2]),.KBD_ENC_GS(KBD_ENC_GS));
    pic_8259_lvs U_PIC(.D(D),.PIC_CS_N(PIC_CS_N),.WR_N(WR_N),.RD_N(RD_N),
        .FRAME_TICK(FRAME_TICK),.SER_TXRDY(SER_TXRDY),.SER_RXRDY(SER_RXRDY),
        .IRQ_B(IRQ_B),.IRQ_A(IRQ_A),.INTA_N(INTA_N),.A0(A0),.PIC_INT(PIC_INT));
    ttl_393_baud_lvs U_BAUD_DIV(.BAUD_MASTER(BAUD_MASTER),.PIT_CLK0(PIT_CLK0),
        .BAUD_19200(BAUD_19200),.BAUD_9600(BAUD_9600));
    pit_8253_lvs U_PIT(.D(D),.PIT_CLK0(PIT_CLK0),.CLK(CLK),.A0(A0),.A1(A1),
        .PIT_CS_N(PIT_CS_N),.RD_N(RD_N),.WR_N(WR_N),.PIT_BAUD(PIT_BAUD),
        .PIT_SOUND(PIT_SOUND),.PIT_OUT2_TP(PIT_OUT2_TP));
    act_273_post_lvs U_POST(.RESET_N(RESET_N),.POST_CLK(POST_CLK),.D(D),.POST_Q(POST_Q));
endmodule
`default_nettype wire
