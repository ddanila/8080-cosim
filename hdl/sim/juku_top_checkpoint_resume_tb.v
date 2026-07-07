// Try to resume the LVS-checked juku_top from the cosim EKDOS/TDD checkpoint.
//
// This is intentionally narrower than juku_top_tb: it skips the slow banner draw by
// loading checkpoint RAM and visible latches, then seeds the vm80a core at an M1
// fetch boundary. The pass condition is the first post-checkpoint ROMBIOS I/O
// window, not the final EKDOS prompt.
`timescale 1ns/100ps
`default_nettype none

module juku_top_checkpoint_resume_tb();
  reg osc = 0;
  integer i;
  reg [1023:0] ram_file;
  reg [7:0] ram [0:65535];
  integer mcyc = 0, vram_writes = 30000, max_mcyc = 200000, timecap = 200000000;
  integer trace_resume = 0;
  integer pic_seen = 0, kbd_seen = 0, raw_ios = 0;
  integer traceirq = 0, tracekbd = 0, tracefdc = 0, stopfdc = 0;
  integer fdc_ios = 0, fdc_reads = 0, fdc_writes = 0;
  integer frameirq = 0, osc_n = 0, frame_ticks = 0, intr_edges = 0, inta_edges = 0;
  integer ekdoskeys = 0, ekdos_key = 0, keyat = 42000, khold = 900000, kgap = 900000, key_t = -1;
  reg frame_tick = 1'b0, intr_q = 1'b0, inta_q = 1'b1;
  reg kbd_en = 1'b1, kbd_pressed = 1'b0, kbd_shift = 1'b0, kbd_was_pressed = 1'b0;
  reg [3:0] kbd_kcol = 4'd0;
  reg [2:0] kbd_kbit = 3'd0;
  reg clk_run = 1'b1;
  reg resume_started = 1'b0;
  reg sq = 0;

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(kbd_en), .kbd_pressed(kbd_pressed), .kbd_shift(kbd_shift),
               .kbd_kcol(kbd_kcol), .kbd_kbit(kbd_kbit), .frame_tick(frame_tick));

  initial forever begin
    if (clk_run) begin
      force dut.phi1 = 1'b1; force dut.phi2 = 1'b0; osc = 0; #10; osc = 1; #10;
      force dut.phi1 = 1'b0; force dut.phi2 = 1'b1; osc = 0; #10; osc = 1; #10;
      force dut.phi2 = 1'b0;
    end else begin
      force dut.phi1 = 1'b0; force dut.phi2 = 1'b0; osc = 0; #10;
    end
  end

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

  task load_checkpoint_state; begin
    dut.U_CPU.u.core.r16_pc = 16'h0484;
    dut.U_CPU.u.core.r16_sp = 16'hD44C;
    dut.U_CPU.u.core.r16_bc = 16'hD7E7;
    dut.U_CPU.u.core.r16_de = 16'hFD2F;
    dut.U_CPU.u.core.r16_hl = 16'h00A1;
    dut.U_CPU.u.core.r16_wz = 16'h0000;
    dut.U_CPU.u.core.acc = 8'hA1;
    dut.U_CPU.u.core.psw_s = 1'b1;
    dut.U_CPU.u.core.psw_z = 1'b0;
    dut.U_CPU.u.core.psw_ac = 1'b0;
    dut.U_CPU.u.core.psw_p = 1'b0;
    dut.U_CPU.u.core.psw_c = 1'b0;
    dut.U_CPU.u.core.tmp_c = 1'b0;
    dut.U_CPU.u.core.inte = 1'b0;
    dut.U_CPU.u.core.inta = 1'b0;
    dut.U_CPU.u.core.intr = 1'b0;
    dut.U_CPU.u.core.minta = 1'b0;
    dut.U_CPU.u.core.mstart = 1'b0;
    dut.U_CPU.u.core.i = 8'h00;
    dut.U_CPU.u.core.di = 8'h00;
    dut.U_CPU.u.core.db = 8'h00;
    dut.U_CPU.u.core.a = 16'h0484;
    dut.U_CPU.u.core.abufena = 1'b1;
    dut.U_CPU.u.core.db_ena = 1'b0;
    dut.U_CPU.u.core.db_stb = 1'b0;
    dut.U_CPU.u.core.dbin_pin = 1'b0;
    dut.U_CPU.u.core.dbin_ext = 1'b0;
    dut.U_CPU.u.core.wr_n = 1'b1;
    dut.U_CPU.u.core.sync = 1'b0;
    dut.U_CPU.u.core.reset = 1'b0;
    dut.U_CPU.u.core.t404 = 1'b0;

    // Seed a clean end-of-machine state so the next clocks start an M1 fetch at PC.
    dut.U_CPU.u.core.t1 = 1'b0; dut.U_CPU.u.core.t2 = 1'b0; dut.U_CPU.u.core.tw = 1'b0;
    dut.U_CPU.u.core.t3 = 1'b0; dut.U_CPU.u.core.t4 = 1'b0; dut.U_CPU.u.core.t5 = 1'b0;
    dut.U_CPU.u.core.t1f1 = 1'b0; dut.U_CPU.u.core.t2f1 = 1'b0; dut.U_CPU.u.core.twf1 = 1'b0;
    dut.U_CPU.u.core.t3f1 = 1'b0; dut.U_CPU.u.core.t4f1 = 1'b0; dut.U_CPU.u.core.t5f1 = 1'b0;
    dut.U_CPU.u.core.m1 = 1'b1; dut.U_CPU.u.core.m2 = 1'b0; dut.U_CPU.u.core.m3 = 1'b0;
    dut.U_CPU.u.core.m4 = 1'b0; dut.U_CPU.u.core.m5 = 1'b0;
    dut.U_CPU.u.core.m1f1 = 1'b1; dut.U_CPU.u.core.m2f1 = 1'b0; dut.U_CPU.u.core.m3f1 = 1'b0;
    dut.U_CPU.u.core.m4f1 = 1'b0; dut.U_CPU.u.core.m5f1 = 1'b0;
    dut.U_CPU.u.core.eom = 1'b1;
    dut.U_CPU.u.core.t789 = 1'b0;
    dut.U_CPU.u.core.t887 = 1'b0;
    dut.U_CPU.u.core.t953 = 1'b0;
    dut.U_CPU.u.core.t976 = 1'b0;
    dut.U_CPU.u.core.t980 = 1'b0;
    dut.U_CPU.u.core.hold = 1'b0;
    dut.U_CPU.u.core.hlda_pin = 1'b0;

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

    dut.U_FDC.status = 8'h80;
    dut.U_FDC.track = 8'h00;
    dut.U_FDC.sector = 8'h01;
    dut.U_FDC.data = 8'h00;
    dut.U_FDC.command = 8'h00;
    dut.U_FDC.buffer_pos = 0;
    dut.U_FDC.buffer_len = 0;
  end endtask

  task set_ekdos_key(input integer idx); begin
    kbd_shift <= 1'b1;
    if (idx == 0) begin kbd_kcol <= 4; kbd_kbit <= 3; end   // T
    else begin kbd_kcol <= 6; kbd_kbit <= 5; end             // D
  end endtask

  always @(posedge osc) begin
    if (resume_started && dut.sync && !sq) begin
      if (trace_resume > 0) begin
        $display("[RESUME-TRACE] mcyc=%0d pc=0x%04h ba=0x%04h db=0x%02h i=0x%02h m=%b%b%b%b%b t=%b%b%b%b%b%b sync=%b memr_n=%b memw_n=%b iord_n=%b iowr_n=%b",
                 mcyc + 1,
                 dut.U_CPU.u.core.r16_pc,
                 dut.BA,
                 dut.DB,
                 dut.U_CPU.u.core.i,
                 dut.U_CPU.u.core.m1,
                 dut.U_CPU.u.core.m2,
                 dut.U_CPU.u.core.m3,
                 dut.U_CPU.u.core.m4,
                 dut.U_CPU.u.core.m5,
                 dut.U_CPU.u.core.t1,
                 dut.U_CPU.u.core.t2,
                 dut.U_CPU.u.core.tw,
                 dut.U_CPU.u.core.t3,
                 dut.U_CPU.u.core.t4,
                 dut.U_CPU.u.core.t5,
                 dut.sync,
                 dut.memr_n,
                 dut.memw_n,
                 dut.iord_n,
                 dut.iowr_n);
        trace_resume = trace_resume - 1;
      end
      mcyc <= mcyc + 1;
    end
    sq <= dut.sync;
    if (resume_started && mcyc >= max_mcyc) begin
      $display("JUKU-TOP-CHECKPOINT-RESUME: FAIL max_mcyc pc=0x%04h ios=%0d pic_seen=%0d kbd_seen=%0d fdc_ios=%0d",
               dut.U_CPU.u.core.r16_pc, raw_ios, pic_seen, kbd_seen, fdc_ios);
      $finish;
    end

    if (resume_started) begin
      if (ekdoskeys != 0) begin
        if (kbd_en && key_t < 0 && keyat != 0 && vram_writes >= keyat) begin
          key_t <= 0;
          ekdos_key <= 0;
          set_ekdos_key(0);
        end else if (key_t >= 0 && ekdos_key < 3) begin
          key_t <= key_t + 1;
          if (key_t >= khold + kgap - 1) begin
            ekdos_key <= ekdos_key + 1;
            key_t <= 0;
            set_ekdos_key(ekdos_key + 1);
          end
        end
        kbd_pressed <= (key_t >= 0 && key_t < khold && ekdos_key < 3);
      end
      if (tracekbd && kbd_pressed && !kbd_was_pressed)
        $display("[RESUME-KBD-STIM] press key=%0d col=%0d bit=%0d shift=%0d mcyc=%0d vram=%0d",
                 ekdos_key, kbd_kcol, kbd_kbit, kbd_shift, mcyc, vram_writes);
      if (tracekbd && !kbd_pressed && kbd_was_pressed)
        $display("[RESUME-KBD-STIM] release key=%0d mcyc=%0d vram=%0d", ekdos_key, mcyc, vram_writes);
      kbd_was_pressed <= kbd_pressed;

      osc_n <= osc_n + 1;
      frame_tick <= (frameirq != 0 && (osc_n % frameirq) == (frameirq - 1));
      if (frame_tick) begin
        frame_ticks = frame_ticks + 1;
        if (traceirq > 1) $display("[RESUME-IRQ] frame_tick count=%0d mcyc=%0d vram=%0d",
                                   frame_ticks, mcyc, vram_writes);
      end
      if (dut.intr && !intr_q) begin
        intr_edges = intr_edges + 1;
        if (traceirq) $display("[RESUME-IRQ] intr rise count=%0d mcyc=%0d vram=%0d",
                               intr_edges, mcyc, vram_writes);
      end
      if (!dut.inta_n && inta_q) begin
        inta_edges = inta_edges + 1;
        if (traceirq) $display("[RESUME-IRQ] inta fall count=%0d mcyc=%0d vram=%0d",
                               inta_edges, mcyc, vram_writes);
      end
      intr_q <= dut.intr;
      inta_q <= dut.inta_n;
    end
  end

  always @(negedge dut.memw_n) if (~dut.ram_sel_n && dut.BA >= 16'hD800) begin
    vram_writes = vram_writes + 1;
    if ((vram_writes % 100) == 0)
      $display("[RESUME-VRAM] writes=%0d mcyc=%0d pc=0x%04h", vram_writes, mcyc, dut.U_CPU.u.core.r16_pc);
  end

  always @(negedge dut.iowr_n) begin
    #1;
    raw_ios = raw_ios + 1;
    if (!dut.cs_pic_n) begin
      $display("[RESUME-PIC] OUT port=0x%02h data=0x%02h mcyc=%0d vram=%0d pc=0x%04h",
               dut.BA[7:0], dut.DB, mcyc, vram_writes, dut.U_CPU.u.core.r16_pc);
      if (dut.BA[0] == 1'b0 && dut.DB == 8'hD6) pic_seen = 1;
    end
    if (!dut.cs_fdc_n) begin
      fdc_ios = fdc_ios + 1;
      fdc_writes = fdc_writes + 1;
      if (tracefdc) $display("[RESUME-FDC] OUT port=0x%02h reg=%0d data=0x%02h mcyc=%0d vram=%0d ios=%0d",
                             dut.BA[7:0], dut.BA[1:0], dut.DB, mcyc, vram_writes, fdc_ios);
      if (stopfdc != 0 && fdc_ios >= stopfdc) begin
        $display("[RESUME-FDC] stop ios=%0d reads=%0d writes=%0d mcyc=%0d vram=%0d",
                 fdc_ios, fdc_reads, fdc_writes, mcyc, vram_writes);
        $finish;
      end
    end
  end

  always @(negedge dut.iord_n) begin
    #1;
    raw_ios = raw_ios + 1;
    if (!dut.cs_ppi0_n && dut.BA[1:0] == 2'd1) begin
      $display("[RESUME-KBD] IN port=0x%02h data=0x%02h mcyc=%0d vram=%0d pc=0x%04h",
               dut.BA[7:0], dut.DB, mcyc, vram_writes, dut.U_CPU.u.core.r16_pc);
      if (dut.DB == 8'hCF) kbd_seen = 1;
    end
    if (!dut.cs_fdc_n) begin
      fdc_ios = fdc_ios + 1;
      fdc_reads = fdc_reads + 1;
      if (tracefdc) $display("[RESUME-FDC] IN  port=0x%02h reg=%0d data=0x%02h mcyc=%0d vram=%0d ios=%0d",
                             dut.BA[7:0], dut.BA[1:0], dut.DB, mcyc, vram_writes, fdc_ios);
      if (stopfdc != 0 && fdc_ios >= stopfdc) begin
        $display("[RESUME-FDC] stop ios=%0d reads=%0d writes=%0d mcyc=%0d vram=%0d",
                 fdc_ios, fdc_reads, fdc_writes, mcyc, vram_writes);
        $finish;
      end
    end
    if (pic_seen && kbd_seen && stopfdc == 0) begin
      $display("JUKU-TOP-CHECKPOINT-RESUME: PASS pc=0x%04h mcyc=%0d vram=%0d ios=%0d",
               dut.U_CPU.u.core.r16_pc, mcyc, vram_writes, raw_ios);
      $finish;
    end
  end

  initial begin
    if (!$value$plusargs("checkpoint_ram=%s", ram_file)) begin
      $display("JUKU-TOP-CHECKPOINT-RESUME: FAIL missing +checkpoint_ram=<hex>");
      $finish;
    end
    if ($value$plusargs("max_mcyc=%d", max_mcyc)) ;
    if ($value$plusargs("timecap=%d", timecap)) ;
    if ($value$plusargs("trace_resume=%d", trace_resume)) ;
    if ($value$plusargs("frameirq=%d", frameirq)) ;
    if ($value$plusargs("ekdoskeys=%d", ekdoskeys)) ;
    if ($value$plusargs("keyat=%d", keyat)) ;
    if ($value$plusargs("khold=%d", khold)) ;
    if ($value$plusargs("kgap=%d", kgap)) ;
    if ($value$plusargs("traceirq=%d", traceirq)) ;
    if ($value$plusargs("tracekbd=%d", tracekbd)) ;
    if ($value$plusargs("tracefdc=%d", tracefdc)) ;
    if ($value$plusargs("stopfdc=%d", stopfdc)) ;

    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    #2000;
    force dut.reset_sys = 1'b0;
    #400;
    clk_run = 1'b0;
    #100;

    $readmemh(ram_file, ram);
    for (i = 0; i < 65536; i = i + 1) write_dram_byte(i, ram[i]);
    load_checkpoint_state();
    $display("[RESUME] loaded checkpoint pc=0x%04h sp=0x%04h", dut.U_CPU.u.core.r16_pc, dut.U_CPU.u.core.r16_sp);
    mcyc = 0;
    sq = 0;
    osc_n = 0;
    resume_started = 1'b1;
    #100;
    clk_run = 1'b1;
  end

  initial begin
    #(timecap);
    $display("JUKU-TOP-CHECKPOINT-RESUME: FAIL timecap pc=0x%04h mcyc=%0d vram=%0d ios=%0d pic_seen=%0d kbd_seen=%0d fdc_ios=%0d frame_ticks=%0d intr_edges=%0d inta_edges=%0d",
             dut.U_CPU.u.core.r16_pc, mcyc, vram_writes, raw_ios, pic_seen, kbd_seen,
             fdc_ios, frame_ticks, intr_edges, inta_edges);
    $finish;
  end
endmodule

`default_nettype wire
