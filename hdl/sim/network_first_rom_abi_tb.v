`timescale 1ns/100ps
`default_nettype none

// Execute the ROM's test-only ABI entry through the structural machine. The
// production resident bytes and public vectors are preserved; only reset
// dispatch is redirected. Exact framebuffer bytes remain checked by the C oracle, while
// this test proves the physical bus/mode path, keyboard matrix and serial pins.
module network_first_rom_abi_tb;
  reg osc = 0;
  reg active = 0;
  reg serial_in = 1;
  integer failures = 0;
  integer tx_bytes = 0;
  integer rx_reads = 0;
  integer vram_writes = 0;
  integer key_reads = 0;
  reg mode3_seen = 0;
  reg mode1_after_helper = 0;
  reg self_pass_seen = 0;
  reg [7:0] self_status_value = 0;
  reg netdisk_fixture = 0;
  reg require_pof_release = 0;
  integer dma_fill_writes = 0;

  juku_top #(.S21_CONFIG(8'h08)) dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(1'b1), .kbd_pressed(1'b1), .kbd_shift(1'b1),
               .kbd_kcol(4'd4), .kbd_kbit(3'd3), .frame_tick(1'b0));

  initial begin
    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    force dut.s_cts = 1'b0;
    force dut.s_sin = serial_in;
    #2000;
    force dut.reset_sys = 1'b0;
    active = 1;
  end

  initial forever begin
    force dut.phi1 = 1'b1; force dut.phi2 = 1'b0; osc = 0; #10; osc = 1; #10;
    force dut.phi1 = 1'b0; force dut.phi2 = 1'b1; osc = 0; #10; osc = 1; #10;
    force dut.phi2 = 1'b0;
  end

  initial forever begin
    force dut.xtal16m_w = 1'b0; #2;
    force dut.xtal16m_w = 1'b1; #2;
  end

  task fail(input [1023:0] message); begin
    $display("NETWORK-FIRST-ROM-ABI-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  task check_tx(input integer index, input [7:0] value); begin
    case (index)
      1: if (value !== "A") fail("serial byte 1");
      2: if (value !== "B") fail("serial byte 2");
      3: if (value !== "I") fail("serial byte 3");
      4: if (value !== "1") fail("serial byte 4");
      5: if (!netdisk_fixture || value !== "J") fail("NetDisk sync 1");
      6: if (!netdisk_fixture || value !== "D") fail("NetDisk sync 2");
      7: if (!netdisk_fixture || value !== 8'h14) fail("NetDisk operation");
      8: if (!netdisk_fixture || value !== 8'h01) fail("NetDisk sequence");
      9: if (!netdisk_fixture || value !== 8'h00) fail("NetDisk drive");
      10: if (!netdisk_fixture || value !== 8'h02) fail("NetDisk track low");
      11: if (!netdisk_fixture || value !== 8'h00) fail("NetDisk track high");
      12: if (!netdisk_fixture || value !== 8'h01) fail("NetDisk sector");
      13: if (!netdisk_fixture || value !== 8'h18) fail("NetDisk XOR");
      default: fail("extra serial byte");
    endcase
  end endtask

  task send_serial_byte(input [7:0] value); integer bit_index; begin
    @(negedge dut.pit_baud); serial_in = 1'b0;
    @(posedge dut.pit_baud);
    for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
      @(negedge dut.pit_baud); serial_in = value[bit_index];
      @(posedge dut.pit_baud);
    end
    @(negedge dut.pit_baud); serial_in = 1'b1;
    @(posedge dut.pit_baud);
    wait (dut.U_SIO0.rx_ready == 1'b1);
    wait (dut.U_SIO0.rx_ready == 1'b0);
  end endtask

  always @(negedge dut.memw_n) if (active) begin
    #1;
    if (dut.BA >= 16'hD800) vram_writes = vram_writes + 1;
    if (dut.BA >= 16'h0300 && dut.BA < 16'h0380 && dut.DB == 8'h5A)
      dma_fill_writes = dma_fill_writes + 1;
    if (dut.BA == 16'hD783) begin
      self_status_value = dut.DB;
      if (dut.DB == 8'hA5) self_pass_seen = 1;
    end
  end

  always @(negedge dut.iowr_n) if (active) begin
    #1;
    if (dut.BA[7:0] == 8'h06) begin
      if (dut.DB[1:0] == 2'b11) mode3_seen = 1;
      if (mode3_seen && dut.DB[1:0] == 2'b01) mode1_after_helper = 1;
    end
    if (dut.BA[7:0] == 8'h08) begin
      tx_bytes = tx_bytes + 1;
      check_tx(tx_bytes, dut.DB);
    end
  end

  always @(negedge dut.iord_n) if (active) begin
    #1;
    if (dut.BA[7:0] == 8'h05) key_reads = key_reads + 1;
    if (dut.BA[7:0] == 8'h08) rx_reads = rx_reads + 1;
  end

  initial begin
    wait (active && tx_bytes == 4);
    wait (dut.U_SIO0.tx_buffer_full == 1'b0 && dut.U_SIO0.tx_busy == 1'b0);
    send_serial_byte(8'hC3);
  end

  initial begin
    wait (active && netdisk_fixture && tx_bytes == 13);
    wait (dut.U_SIO0.tx_buffer_full == 1'b0 && dut.U_SIO0.tx_busy == 1'b0);
    wait (dut.U_SIO0.command == 8'h34);
    send_serial_byte("D");
    send_serial_byte("J");
    send_serial_byte(8'h01);
    send_serial_byte(8'h00);
    send_serial_byte(8'h01);
    send_serial_byte(8'h02);
    send_serial_byte(8'h00);
    send_serial_byte(8'h01);
    send_serial_byte(8'h01);
    send_serial_byte(8'h5A);
    send_serial_byte(8'hD4);
    send_serial_byte(8'h65);
  end

  always @(posedge osc) if (active && dut.U_CPU.u.core.thalt) begin
    if (!self_pass_seen) begin
      $display("NETWORK-FIRST-ROM-ABI-HDL: observed resident status=%02h",
               self_status_value);
      fail("resident self-test status is not A5");
    end
    if (!mode3_seen || !mode1_after_helper) fail("mode-3 helper did not restore mode 1");
    if (vram_writes < 9600) fail("framebuffer clear/draw traffic is incomplete");
    if (key_reads == 0) fail("keyboard matrix was not scanned");
    if (tx_bytes != (netdisk_fixture ? 13 : 4) || rx_reads == 0)
      fail("serial ABI traffic is incomplete");
    if (netdisk_fixture && dma_fill_writes != 128)
      fail("NetDisk fill did not reach all 128 DMA bytes");
    if (dut.ppi0_pc[1:0] !== 2'b01) fail("final memory mode is not 1");
    if (require_pof_release && dut.ppi0_pc !== 8'h01)
      fail("final Port C is not mode 1 with PC7/POF released");
    if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
    if (failures == 0)
      $display("NETWORK-FIRST-ROM-ABI-HDL: PASS status=A5 mode=1 mode3-helper vram=%0d key_reads=%0d tx=%0d rx=%0d netdisk_dma=%0d pc=%04h",
               vram_writes, key_reads, tx_bytes, rx_reads, dma_fill_writes,
               dut.U_CPU.u.core.r16_pc);
    #20 $finish;
  end

  initial begin
    netdisk_fixture = $test$plusargs("netdisk");
    require_pof_release = $test$plusargs("pof_release");
  end

  initial begin
    #300000000;
    $display("NETWORK-FIRST-ROM-ABI-HDL: TIMEOUT pc=%04h status=%0d mode3=%0d vram=%0d key=%0d tx=%0d rx=%0d",
             dut.U_CPU.u.core.r16_pc, self_pass_seen, mode3_seen,
             vram_writes, key_reads, tx_bytes, rx_reads);
    fail("time cap before resident HLT");
    $finish;
  end
endmodule

`default_nettype wire
