`timescale 1ns/1ps
// R5.S3: actual usart_8251 model through the protected backplane console boundary.
// The physical 8251 sees x16 clocks; the repository's deliberately minimal USART
// samples one bit per clock, so div[7]/div[8] are its simulation adapters while
// div[3]/div[4] remain the checked physical 307.2/153.6 kHz pins.
module revb_serial_console_tb;
  reg master = 0;
  reg [8:0] div = 0;
  always #1 master = ~master;
  always @(posedge master) div <= div + 1'b1;

  reg baud_fallback = 0;
  wire baud_x16 = baud_fallback ? div[4] : div[3];
  wire uart_bitclk = baud_fallback ? div[8] : div[7];

  reg A = 0, cs_n = 1, rd_n = 1, wr_n = 1;
  reg cpu_drive = 0;
  reg [7:0] cpu_dout = 0;
  wire [7:0] D;
  assign D = cpu_drive ? cpu_dout : 8'bz;

  reg reset_n = 0;
  wire io_reset = ~reset_n;
  reg shunt_tx = 0, shunt_rx = 0, ext_loopback = 0;
  reg host_tx = 1;
  reg inject_isolation_fault = 0;
  wire uart_txd;

  // Digital-value model of U_CON + divider/series network. Pull-ups make both
  // sides idle-high with JP_S5 open. ext_loopback is a temporary J_TTL 2-3 link.
  wire con_tx_src = shunt_tx ? uart_txd : 1'b1;
  wire board_tx = con_tx_src;
  wire board_rx = ext_loopback ? board_tx : host_tx;
  wire con_rx_drive = board_rx;
  wire uart_rxd = shunt_rx ? con_rx_drive : (inject_isolation_fault ? host_tx : 1'b1);

  wire rts, dtr, rxrdy, txrdy, syndet, txempty;
  usart_8251 U_SIO(
    .A(A), .D(D), .cs_n(cs_n), .rd_n(rd_n), .wr_n(wr_n), .clk(master),
    .rxc(uart_bitclk), .txc(uart_bitclk), .vss_gnd(1'b0), .vcc_5v(1'b1),
    .txd(uart_txd), .rts(rts), .dtr(dtr), .rxrdy(rxrdy), .txrdy(txrdy),
    .syndet(syndet), .txempty(txempty), .rxd(uart_rxd), .cts_n(1'b0),
    .reset(io_reset), .dsr_n(1'b0)
  );

  reg [7:0] request [0:16];
  reg [7:0] reply [0:19];
  reg [1023:0] request_file, reply_file;
  integer i, edge_a, edge_b, master_edges = 0;
  reg [7:0] value, captured;
  always @(posedge master) master_edges <= master_edges + 1;

  task fail(input [1023:0] why); begin
    $display("REVB-SERIAL-CONSOLE: FAIL %0s", why);
    $finish;
  end endtask

  task write_reg(input addr, input [7:0] data); begin
    @(negedge master); A = addr; cpu_dout = data; cpu_drive = 1; cs_n = 0;
    #1 wr_n = 0; #1 wr_n = 1; #1 cs_n = 1; cpu_drive = 0;
  end endtask

  task read_reg(input addr, output [7:0] data); begin
    @(negedge master); A = addr; cpu_drive = 0; cs_n = 0;
    #1 rd_n = 0; #1 data = D; rd_n = 1; #1 cs_n = 1;
  end endtask

  task bit_tick; begin
    @(posedge uart_bitclk); #0.1;
  end endtask

  task host_send(input [7:0] data); integer bitn; begin
    host_tx = 0; bit_tick();
    for (bitn = 0; bitn < 8; bitn = bitn + 1) begin
      host_tx = data[bitn]; bit_tick();
    end
    host_tx = 1; bit_tick();
  end endtask

  task cpu_send_capture(input [7:0] data, output [7:0] got); integer bitn; begin
    write_reg(0, data);
    bit_tick();
    if (board_tx !== 0) fail("missing TX start bit at J_TTL pin 2");
    for (bitn = 0; bitn < 8; bitn = bitn + 1) begin
      bit_tick(); got[bitn] = board_tx;
    end
    bit_tick();
    if (board_tx !== 1) fail("missing TX stop bit at J_TTL pin 2");
  end endtask

  task init_8251; begin
    write_reg(1, 8'h4e); // async, x16, 8-bit, one stop bit
    write_reg(1, 8'h37); // TxEN, RxEN, DTR, RTS, error reset
  end endtask

  task check_x16_period(input integer expected); begin
    @(posedge baud_x16); edge_a = master_edges;
    @(posedge baud_x16); edge_b = master_edges;
    if (edge_b - edge_a != expected) fail("selected physical x16 clock divider is wrong");
  end endtask

  initial begin
    if (!$value$plusargs("request=%s", request_file)) fail("missing request vector");
    if (!$value$plusargs("reply=%s", reply_file)) fail("missing reply vector");
    if ($test$plusargs("inject_isolation_fault")) inject_isolation_fault = 1;
    $readmemh(request_file, request);
    $readmemh(reply_file, reply);

    // External reset polarity reaches 8251 pin 25 through the I/O GAL.
    if (io_reset !== 1) fail("IO_RESET is not active high while RESET_N is low");
    repeat (4) @(posedge master);
    reset_n = 1;
    #0.1;
    if (io_reset !== 0) fail("IO_RESET did not release with RESET_N");

    // Open jumpers: neither external activity nor an isolated UART may float or
    // drive the other side.
    host_tx = 0; #1;
    if (uart_rxd !== 1 || board_tx !== 1) fail("JP_S5 isolation is not idle-high/no-contention");
    host_tx = 1; shunt_tx = 1; shunt_rx = 1;

    check_x16_period(16);
    init_8251();

    // Host sends one real C10 ABI-1.4 PROBE request. The CPU consumes every byte
    // through the real 8251 RX register and checks the exact framed vector.
    for (i = 0; i < 17; i = i + 1) begin
      host_send(request[i]);
      read_reg(1, value);
      if ((value & 8'h02) == 0) fail("RxRDY absent after host request byte");
      read_reg(0, value);
      if (value !== request[i]) fail("C10 request byte changed across J_TTL/8251 RX");
    end

    // VJUGA's adapter response is a C10-compatible DATA echo. Capture it at the
    // external board-TX pin rather than at the USART's internal txd node.
    for (i = 0; i < 20; i = i + 1) begin
      cpu_send_capture(reply[i], captured);
      if (captured !== reply[i]) fail("C10 reply byte changed across 8251/J_TTL TX");
    end

    // Genuine external loopback with the header pins linked.
    ext_loopback = 1;
    cpu_send_capture(8'hA6, captured);
    if (captured !== 8'hA6) fail("external loopback TX capture failed");
    bit_tick(); // the minimal USART commits RX on the edge after its eight data samples
    read_reg(1, value);
    if ((value & 8'h02) == 0) fail("external loopback did not raise RxRDY");
    read_reg(0, value);
    if (value !== 8'hA6) fail("external loopback byte mismatch");
    ext_loopback = 0;

    // Internal-reset command, then select and prove the 9,600 fallback clock.
    write_reg(1, 8'h40);
    baud_fallback = 1;
    check_x16_period(32);
    init_8251();
    ext_loopback = 1;
    cpu_send_capture(8'h96, captured);
    bit_tick();
    read_reg(1, value);
    if ((value & 8'h02) == 0) fail("9,600 fallback loopback did not raise RxRDY");
    read_reg(0, value);
    if (value !== 8'h96) fail("9,600 fallback loopback byte mismatch");

    $display("REVB-SERIAL-CONSOLE: PASS reset, isolation, 19,200/9,600, C10 request/reply, bidirectional bytes, external loopback");
    $finish;
  end
endmodule
