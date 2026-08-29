// VJUGA rev B expanded I/O-card behavioral twin.
// Models the M1-qualified decode GAL, PPI mode latch, real 8251/8253 cells,
// physical baud-divider choices, channel-1 sound observation, and independent
// write-only POST latch. POST_ALIAS_FAULT and BAD_PIT_TAP are negative controls.
`default_nettype none
module revb_io_card #(
    parameter USART_REAL = 0,
    parameter PIT_REAL = 1,
    parameter integer CLK_SOURCE = 1, // 0=direct /16, 1=PIT normal, 2=direct /32
    parameter BAD_PIT_TAP = 0,
    parameter POST_ALIAS_FAULT = 0
) (
    input  wire        clk,
    input  wire        baud_master,
    input  wire        reset_n,
    input  wire [15:0] A,
    input  wire [7:0]  D_in,
    input  wire        m1_n,
    input  wire        iorq_n, rd_n, wr_n,
    input  wire        uart_rxd,
    output wire        uart_txd,
    output wire [7:0]  D_out,
    output wire        D_oe,
    output wire        MODE0,
    output wire        MODE1,
    output wire        PIT_OUT0,
    output wire        PIT_OUT1,
    output wire        PIT_OUT2,
    output wire        BAUDCLK_OUT,
    output reg  [7:0]  POST_CODE
);
    wire ordinary_io = !iorq_n && m1_n;
    wire pic_sel  = ordinary_io && (A[7:2] == 6'b000000); // 00h-03h
    wire ppi_sel  = ordinary_io && (A[7:2] == 6'b000001); // 04h-07h
    wire uart_sel = ordinary_io && (A[7:2] == 6'b000010); // 08h-0Bh
    wire pit_sel  = ordinary_io && (A[7:2] == 6'b000110); // 18h-1Bh
    wire post_sel = ordinary_io &&
                    (A[7:2] == (POST_ALIAS_FAULT ? 6'b000110 : 6'b001000));

    reg [7:0] out_last [0:255];
    reg [7:0] portc;
    reg [1:0] mode;
    integer k;
    initial begin
        for (k = 0; k < 256; k = k + 1) out_last[k] = 8'h00;
        portc = 8'h00;
        mode = 2'b00;
        POST_CODE = 8'h00;
    end

    // U7 is a cascaded 74HC393. Bit 1 is /4 for D57 CLK0, bit 3 is
    // the direct /16 recovery clock, and bit 4 is direct /32.
    reg [7:0] baud_div = 8'h00;
    always @(posedge baud_master or negedge reset_n) begin
        if (!reset_n) baud_div <= 8'h00;
        else baud_div <= baud_div + 8'h01;
    end
    wire pit_clk0 = BAD_PIT_TAP ? baud_div[0] : baud_div[1];
    wire direct_clk = (CLK_SOURCE == 2) ? baud_div[4] : baud_div[3];

    wire [7:0] pit_d;
    wire pit_wr = pit_sel && !wr_n;
    assign pit_d = pit_wr ? D_in : 8'bz;
    generate
      if (PIT_REAL) begin : g_pit
        pit_8253 U_PIT (
            .A(A[1:0]), .D(pit_d), .cs_n(~pit_sel), .rd_n(rd_n), .wr_n(wr_n),
            .clk(clk), .clk0(pit_clk0), .gate0(1'b1),
            .clk1(clk), .gate1(1'b1), .clk2(1'b0), .gate2(1'b1),
            .out0(PIT_OUT0), .out1(PIT_OUT1), .out2(PIT_OUT2));
      end else begin : g_nopit
        assign PIT_OUT0 = 1'b0;
        assign PIT_OUT1 = 1'b0;
        assign PIT_OUT2 = 1'b0;
      end
    endgenerate

    assign BAUDCLK_OUT = (CLK_SOURCE == 1) ? PIT_OUT0 : direct_clk;

    // The root 8251 model advances one serial bit per clock edge. Physical
    // BAUDCLK_OUT is x16, so this simulation-only adapter supplies bit timing.
    reg [3:0] uart_div = 4'h0;
    always @(posedge BAUDCLK_OUT or negedge reset_n) begin
        if (!reset_n) uart_div <= 4'h0;
        else uart_div <= uart_div + 4'h1;
    end
    wire uart_bit_clk = uart_div[3];

    wire [7:0] sio_d;
    wire uart_wr = uart_sel && !wr_n;
    assign sio_d = uart_wr ? D_in : 8'bz;
    wire uart_oe;
    wire [7:0] uart_do;
    generate
      if (USART_REAL) begin : g_uart
        usart_8251 U_SIO (
            .A(A[0]), .D(sio_d), .cs_n(~uart_sel), .rd_n(rd_n), .wr_n(wr_n),
            .clk(clk), .rxc(uart_bit_clk), .txc(uart_bit_clk),
            .vss_gnd(1'b0), .vcc_5v(1'b1), .txd(uart_txd),
            .rts(), .dtr(), .rxrdy(), .txrdy(), .syndet(), .txempty(),
            .rxd(uart_rxd), .cts_n(1'b0), .reset(~reset_n), .dsr_n(1'b0));
        assign uart_oe = uart_sel && !rd_n;
        assign uart_do = sio_d;
      end else begin : g_nouart
        assign uart_txd = 1'b1;
        assign uart_oe = 1'b0;
        assign uart_do = 8'h00;
      end
    endgenerate

    // Positive-edge ACT273 clock: capture data at the start of the active-low
    // write pulse, commit it as the pulse ends, then retain through halt/failure.
    wire post_clk = !(post_sel && !wr_n);
    reg [7:0] post_pending = 8'h00;
    always @(negedge post_clk or negedge reset_n) begin
        if (!reset_n) post_pending <= 8'h00;
        else post_pending <= D_in;
    end
    always @(posedge post_clk or negedge reset_n) begin
        if (!reset_n) POST_CODE <= 8'h00;
        else POST_CODE <= post_pending;
    end

    wire behavioral_oe = !rd_n && (pic_sel || ppi_sel);
    wire pit_oe = PIT_REAL && pit_sel && !rd_n;
    assign D_out = uart_oe ? uart_do : pit_oe ? pit_d : out_last[A[7:0]];
    assign D_oe = uart_oe || pit_oe || behavioral_oe;
    assign MODE0 = mode[0];
    assign MODE1 = mode[1];

    always @(posedge clk) begin
        if (!reset_n) begin
            portc <= 8'h00;
            mode <= 2'b00;
        end else if (ordinary_io && !wr_n) begin
            out_last[A[7:0]] <= D_in;
            if (A[7:0] == 8'h06) begin
                portc <= D_in;
                mode <= D_in[1:0];
            end else if (A[7:0] == 8'h07) begin
                if (D_in[7]) begin
                    portc <= 8'h00;
                    mode <= 2'b00;
                end else begin
                    portc[D_in[3:1]] <= D_in[0];
                    if (D_in[3:1] == 3'd0) mode[0] <= D_in[0];
                    if (D_in[3:1] == 3'd1) mode[1] <= D_in[0];
                end
            end
        end
    end
endmodule
`default_nettype wire
