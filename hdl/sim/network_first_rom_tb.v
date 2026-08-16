`timescale 1ns/100ps
`default_nettype none

// Structural smoke test for the released network-first ROM. It exercises the
// real vm80a path, EPROM decode, scratch DRAM, PPI/PIC, D54/D55/D57, D11 and
// D104 up to the first target-ready C4 byte. Bulk V15/CP/M service remains in
// the faster C model; this boundary proves that the physical-chip model can
// execute the exact reset and quick-POST image rather than a synthetic stub.
module network_first_rom_tb;
  reg osc = 0;
  reg active = 0;
  integer failures = 0;
  integer io_writes = 0;
  integer mem_writes = 0;
  integer usart_data_writes = 0;
  reg post_ok_seen = 0;

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
               .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(1'b0));

  initial begin
    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    force dut.s_cts = 1'b0;
    force dut.s_sin = 1'b1;
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
    $display("NETWORK-FIRST-ROM-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  always @(negedge dut.memw_n) if (active) begin
    #1;
    mem_writes = mem_writes + 1;
    if (dut.BA == 16'hD610 && dut.DB == 8'h00) post_ok_seen = 1;
  end

  always @(negedge dut.iowr_n) if (active) begin
    #1;
    io_writes = io_writes + 1;
    if (dut.BA[7:0] == 8'h08) begin
      usart_data_writes = usart_data_writes + 1;
      if (usart_data_writes != 1) fail("unexpected byte before target ready");
      if (dut.DB !== 8'hC4) fail("first target-ready byte is not C4");
      if (!post_ok_seen) fail("POST did not store success before target ready");
      if (dut.ppi0_pc[1:0] !== 2'b01) fail("runtime memory mode is not 1");
      if (dut.U_INTR.mask !== 8'hFF) fail("PIC is not fully masked");
      if (dut.U_PIT2.mode[0] !== 3'd2 || dut.U_PIT2.reload[0] !== 17'd4)
        fail("D57 channel 0 is not mode 2/count 4");
      if (dut.U_SIO0.mode !== 8'h4E || dut.U_SIO0.command !== 8'h35)
        fail("D11 is not initialized for 19200/8N1 bootstrap");
      if (dut.U_CPU.u.core.inte !== 1'b0) fail("interrupts became enabled");
      if (failures == 0)
        $display("NETWORK-FIRST-ROM-HDL: PASS post=00 ready=C4 mode=1 pit=mode2/count4 usart=4E/35 io=%0d memw=%0d pc=%04h",
                 io_writes, mem_writes, dut.U_CPU.u.core.r16_pc);
      #20 $finish;
    end
  end

  initial begin
    #120000000;
    $display("NETWORK-FIRST-ROM-HDL: TIMEOUT pc=%04h io=%0d memw=%0d post=%0d pit_mode=%0d pit_reload=%0d usart=%02h/%02h",
             dut.U_CPU.u.core.r16_pc, io_writes, mem_writes, post_ok_seen,
             dut.U_PIT2.mode[0], dut.U_PIT2.reload[0],
             dut.U_SIO0.mode, dut.U_SIO0.command);
    fail("time cap before target-ready C4");
    $finish;
  end
endmodule

`default_nettype wire
