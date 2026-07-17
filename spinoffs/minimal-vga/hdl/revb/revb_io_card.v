// VJUGA rev B — I/O card (B0 scope: 8255 output latch + memory-overlay mode bits).
// Full population (UART, PIC, keyboard matrix) is Phases B1/B3; for the banner
// boot oracle only the Port-C mode handling and the output-latch readback matter
// (no interrupts, no keyboard before 42000 writes). Drives MODE0/MODE1 onto the
// bus (base pins 38/39) for the Memory-card decode; backplane pulls them to boot
// mode when this card is absent (bus contract S11). Logic mirrors vjuga_juku_top.v.
`default_nettype none
module revb_io_card #(parameter USART_REAL = 0) (
    input  wire        clk,
    input  wire        reset_n,
    input  wire [15:0] A,
    input  wire [7:0]  D_in,
    input  wire        iorq_n, rd_n, wr_n,
    output wire [7:0]  D_out,
    output wire        D_oe,
    output wire        MODE0,
    output wire        MODE1
);
    reg [7:0] out_last [0:255];
    reg [7:0] portc;
    reg [1:0] mode;
    integer k;
    initial begin
        for (k = 0; k < 256; k = k + 1) out_last[k] = 8'h00;
        portc = 8'h00; mode = 2'b00;
    end

    // Optional real 8251 USART at 0x08-0x0B for the minimum-tier bring-up twin
    // (T1.2). Default off, so the ekta37 boot check keeps the simple latch model.
    wire        uart_oe;
    wire [7:0]  uart_do;
    generate
      if (USART_REAL) begin : g_uart
        wire uart_sel  = (A[7:2] == 6'b000010);            // 0x08-0x0B
        wire uart_cs_n = ~((iorq_n == 1'b0) && uart_sel);
        wire uart_wr   = (iorq_n == 1'b0) && (wr_n == 1'b0) && uart_sel;
        wire [7:0] sio_d;
        assign sio_d = uart_wr ? D_in : 8'bz;              // CPU drives on write; 8251 on read
        reg [2:0] bdiv = 3'b000;
        always @(posedge clk) bdiv <= bdiv + 3'd1;         // local baud clock (D1.8)
        usart_8251 U_SIO (.A(A[0]), .D(sio_d), .cs_n(uart_cs_n),
                          .rd_n(rd_n), .wr_n(wr_n), .clk(clk),
                          .rxc(bdiv[2]), .txc(bdiv[2]), .vss_gnd(1'b0), .vcc_5v(1'b1),
                          .txd(), .rts(), .dtr(), .rxrdy(), .txrdy(), .syndet(), .txempty(),
                          .rxd(1'b1), .cts_n(1'b0), .reset(1'b0), .dsr_n(1'b0));
        assign uart_oe = (iorq_n == 1'b0) && (rd_n == 1'b0) && uart_sel;
        assign uart_do = sio_d;
      end else begin : g_nouart
        assign uart_oe = 1'b0;
        assign uart_do = 8'h00;
      end
    endgenerate

    assign D_out = uart_oe ? uart_do : out_last[A[7:0]];
    assign D_oe  = (iorq_n == 1'b0) && (rd_n == 1'b0);
    assign MODE0 = mode[0];
    assign MODE1 = mode[1];

    always @(posedge clk) begin
        if (!reset_n) begin
            portc <= 8'h00; mode <= 2'b00;
        end else if (iorq_n == 1'b0 && wr_n == 1'b0) begin
            out_last[A[7:0]] <= D_in;
            if (A[7:0] == 8'h06) begin
                portc <= D_in; mode <= D_in[1:0];
            end else if (A[7:0] == 8'h07) begin
                if (D_in[7]) begin
                    portc <= 8'h00; mode <= 2'b00;
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
