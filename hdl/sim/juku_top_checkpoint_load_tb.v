// Load a cosim checkpoint RAM image into the LVS-checked juku_top DRAM planes.
//
// This is a pre-resume diagnostic: it proves the 64 KiB checkpoint RAM can be
// represented byte-for-byte in the bit-sliced D84..D91 DRAM instances without
// replaying the slow ROMBIOS framebuffer draw.
`timescale 1ns/100ps
`default_nettype none

module juku_top_checkpoint_load_tb();
  reg osc = 0;
  integer i, fd, a, load_state = 0;
  reg [1023:0] ram_file;
  reg [7:0] ram [0:65535];
  reg [7:0] b;
  integer state_fails = 0;

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
               .kbd_kcol(4'd0), .kbd_kbit(3'd0), .frame_tick(1'b0));

  initial forever begin osc = 0; #10; osc = 1; #10; end

  function [7:0] dram_byte(input integer addr); begin
    dram_byte = {dut.U_D91.mem[addr], dut.U_D90.mem[addr], dut.U_D89.mem[addr], dut.U_D88.mem[addr],
                 dut.U_D87.mem[addr], dut.U_D86.mem[addr], dut.U_D85.mem[addr], dut.U_D84.mem[addr]};
  end endfunction

  task write_dram_byte(input integer addr, input [7:0] value); begin
    dut.U_D84.mem[addr] = value[0];
    dut.U_D85.mem[addr] = value[1];
    dut.U_D86.mem[addr] = value[2];
    dut.U_D87.mem[addr] = value[3];
    dut.U_D88.mem[addr] = value[4];
    dut.U_D89.mem[addr] = value[5];
    dut.U_D90.mem[addr] = value[6];
    dut.U_D91.mem[addr] = value[7];
  end endtask

  task fail_state(input [1023:0] msg); begin
    $display("JUKU-TOP-CHECKPOINT-LOAD: FAIL %0s", msg);
    state_fails = state_fails + 1;
  end endtask

  task load_checkpoint_state; begin
    dut.U_CPU.u.core.r16_pc = 16'h0484;
    dut.U_CPU.u.core.r16_sp = 16'hD44C;
    dut.U_CPU.u.core.r16_bc = 16'hD7E7;
    // Empirically, this vm80a core's r16_de/r16_hl internal names are opposite
    // the architectural DE/HL values visible at the 30,000-write checkpoint.
    dut.U_CPU.u.core.r16_de = 16'hFD2F;
    dut.U_CPU.u.core.r16_hl = 16'h00A1;
    dut.U_CPU.u.core.acc = 8'hA1;
    dut.U_CPU.u.core.psw_s = 1'b1;
    dut.U_CPU.u.core.psw_z = 1'b0;
    dut.U_CPU.u.core.psw_ac = 1'b0;
    dut.U_CPU.u.core.psw_p = 1'b0;
    dut.U_CPU.u.core.psw_c = 1'b0;
    dut.U_CPU.u.core.inte = 1'b0;

    dut.U_PPI0.regs[0] = 8'h0F;
    dut.U_PPI0.regs[2] = 8'h80;
    dut.U_PPI0.portc = 8'h80;
    dut.U_PPI0.kbd_col_sel = 4'hF;

    dut.U_INTR.icw1 = 8'h00;
    dut.U_INTR.icw2 = 8'h00;
    dut.U_INTR.mask = 8'hFF;
    dut.U_INTR.expect_icw2 = 1'b0;
    dut.U_INTR.pending = 1'b0;
    dut.U_INTR.inta_idx = 0;

    dut.U_FDC.status = 8'h00;
    dut.U_FDC.track = 8'h00;
    dut.U_FDC.physical_track = 8'h00;
    dut.U_FDC.sector = 8'h01;
    dut.U_FDC.data = 8'h00;
    dut.U_FDC.command = 8'h00;
    dut.U_FDC.buffer_pos = 0;
    dut.U_FDC.buffer_len = 0;
  end endtask

  task verify_checkpoint_state; begin
    if (dut.U_CPU.u.core.r16_pc !== 16'h0484) fail_state("CPU PC mismatch");
    if (dut.U_CPU.u.core.r16_sp !== 16'hD44C) fail_state("CPU SP mismatch");
    if (dut.U_CPU.u.core.r16_bc !== 16'hD7E7) fail_state("CPU BC mismatch");
    if (dut.U_CPU.u.core.r16_de !== 16'hFD2F) fail_state("CPU HL latch mismatch");
    if (dut.U_CPU.u.core.r16_hl !== 16'h00A1) fail_state("CPU DE latch mismatch");
    if (dut.U_CPU.u.core.acc !== 8'hA1) fail_state("CPU A mismatch");
    if ({dut.U_CPU.u.core.psw_s, dut.U_CPU.u.core.psw_z, dut.U_CPU.u.core.psw_ac,
         dut.U_CPU.u.core.psw_p, dut.U_CPU.u.core.psw_c} !== 5'b10000) fail_state("CPU flags mismatch");
    if (dut.U_CPU.u.core.inte !== 1'b0) fail_state("CPU INTE mismatch");
    if (dut.U_PPI0.portc !== 8'h80) fail_state("PPI0 Port C mismatch");
    if (dut.U_PPI0.kbd_col_sel !== 4'hF) fail_state("PPI0 keyboard column mismatch");
    if (dut.U_INTR.mask !== 8'hFF) fail_state("PIC/intr mask mismatch");
    if (dut.U_INTR.icw1 !== 8'h00 || dut.U_INTR.icw2 !== 8'h00) fail_state("PIC/intr ICW mismatch");
    if (dut.U_FDC.status !== 8'h00) fail_state("FDC status mismatch");
    if (dut.U_FDC.track !== 8'h00) fail_state("FDC track mismatch");
    if (dut.U_FDC.physical_track !== 8'h00) fail_state("FDC physical track mismatch");
    if (dut.U_FDC.sector !== 8'h01) fail_state("FDC sector mismatch");
    if (state_fails == 0) $display("JUKU-TOP-CHECKPOINT-STATE: PASS");
  end endtask

  initial begin
    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    force dut.phi1 = 1'b0;
    force dut.phi2 = 1'b0;
    if (!$value$plusargs("checkpoint_ram=%s", ram_file)) begin
      $display("JUKU-TOP-CHECKPOINT-LOAD: FAIL missing +checkpoint_ram=<hex>");
      $finish;
    end
    if ($value$plusargs("load_checkpoint_state=%d", load_state)) ;

    $readmemh(ram_file, ram);
    for (i = 0; i < 65536; i = i + 1) write_dram_byte(i, ram[i]);
    if (load_state != 0) load_checkpoint_state();

    fd = $fopen("hdl/sim/checkpoint_ram_top.bin", "wb");
    for (a = 0; a < 65536; a = a + 1) begin
      b = dram_byte(a);
      $fwrite(fd, "%c", b);
      if (b !== ram[a]) begin
        $display("JUKU-TOP-CHECKPOINT-LOAD: FAIL addr=0x%04h got=0x%02h want=0x%02h", a[15:0], b, ram[a]);
        $finish;
      end
    end
    $fclose(fd);

    fd = $fopen("hdl/sim/checkpoint_vram_top.bin", "wb");
    for (a = 0; a < 40*241; a = a + 1) begin
      b = dram_byte(16'hD800 + a);
      $fwrite(fd, "%c", b);
    end
    $fclose(fd);

    if (load_state != 0) begin
      verify_checkpoint_state();
      if (state_fails != 0) $finish;
    end

    $display("JUKU-TOP-CHECKPOINT-LOAD: PASS");
    $finish;
  end
endmodule

`default_nettype wire
