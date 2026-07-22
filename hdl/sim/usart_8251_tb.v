module usart_8251_tb;
  reg A = 0, cs_n = 1, rd_n = 1, wr_n = 1, baud = 0, cts_n = 1;
  reg drive = 0;
  reg [7:0] dout = 8'h00;
  wire [7:0] D;
  wire txd, rts, dtr, txrdy;

  assign D = drive ? dout : 8'bz;

  usart_8251 UUT(.A(A), .D(D), .cs_n(cs_n), .rd_n(rd_n), .wr_n(wr_n),
                 .clk(1'b0), .rxc(baud), .txc(baud),
                 .txd(txd), .rts(rts), .dtr(dtr), .txrdy(txrdy),
                 .rxd(txd), .cts_n(cts_n));

  task write_reg(input reg addr, input reg [7:0] value); begin
    A = addr; dout = value; drive = 1; cs_n = 0; #1 wr_n = 0; #1 wr_n = 1; #1 cs_n = 1; drive = 0; #1;
  end endtask

  task read_reg(input reg addr, output reg [7:0] value); begin
    A = addr; drive = 0; cs_n = 0; #1 rd_n = 0; #1 value = D; rd_n = 1; #1 cs_n = 1; #1;
  end endtask

  task baud_tick; begin
    #1 baud = 1; #1 baud = 0; #1;
  end endtask

  integer i;
  reg [7:0] status;
  reg [7:0] rx;

  initial begin
    write_reg(1'b1, 8'h4e);  // async mode, 8-bit character shape for the minimal model.
    write_reg(1'b1, 8'h37);  // TxEN, RxEN, DTR, RTS, error reset.

    if (rts !== 1'b0 || dtr !== 1'b0) begin
      $display("USART8251: FAIL command outputs rts=%b dtr=%b", rts, dtr);
      $finish;
    end

    read_reg(1'b1, status);
    if ((status & 8'h05) != 8'h05 || (status & 8'h02) != 8'h00) begin
      $display("USART8251: FAIL initial status %02x", status);
      $finish;
    end

    write_reg(1'b0, 8'ha5);
    read_reg(1'b1, status);
    if ((status & 8'h05) != 8'h00) begin
      $display("USART8251: FAIL busy status %02x", status);
      $finish;
    end

    baud_tick();
    read_reg(1'b1, status);
    if ((status & 8'h05) != 8'h00 || txrdy !== 1'b0) begin
      $display("USART8251: FAIL inactive-CTS status %02x txrdy=%b", status, txrdy);
      $finish;
    end

    cts_n = 0;
    baud_tick();
    read_reg(1'b1, status);
    if ((status & 8'h05) != 8'h01 || txrdy !== 1'b1) begin
      $display("USART8251: FAIL holding-to-shift status %02x txrdy=%b", status, txrdy);
      $finish;
    end

    for (i = 0; i < 11; i = i + 1) baud_tick();

    read_reg(1'b1, status);
    if ((status & 8'h07) != 8'h07) begin
      $display("USART8251: FAIL loopback-ready status %02x", status);
      $finish;
    end

    read_reg(1'b0, rx);
    if (rx !== 8'ha5) begin
      $display("USART8251: FAIL loopback byte got=%02x", rx);
      $finish;
    end

    read_reg(1'b1, status);
    if ((status & 8'h02) != 8'h00) begin
      $display("USART8251: FAIL rx ready did not clear status=%02x", status);
      $finish;
    end

    $display("USART8251: PASS loopback byte=%02x final_status=%02x", rx, status);
    $finish;
  end
endmodule
