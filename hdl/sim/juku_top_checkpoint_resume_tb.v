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
  integer state_vram_writes = 30000;
  integer state_pc = 16'h0484, state_sp = 16'hD44C, state_bc = 16'hD7E7;
  integer state_de = 16'h00A1, state_hl = 16'hFD2F, state_wz = 16'h0000;
  integer state_a = 8'hA1, state_sf = 1, state_zf = 0, state_hf = 0, state_pf = 0, state_cf = 0;
  integer state_iff = 0, state_portc = 8'h80, state_kbd_col = 8'h0F;
  integer state_pic_icw1 = 8'h00, state_pic_icw2 = 8'h00, state_pic_mask = 8'hFF, state_pic_expect_icw2 = 0;
  integer state_fdc_status = 8'h80, state_fdc_track = 8'h00, state_fdc_sector = 8'h01;
  integer state_fdc_data = 8'h00, state_fdc_command = 8'h00;
  integer state_fdc_buffer_pos = 0, state_fdc_buffer_len = 0;
  integer trace_resume = 0;
  integer pic_seen = 0, kbd_seen = 0, raw_ios = 0;
  integer traceirq = 0, tracekbd = 0, tracefdc = 0, stopfdc = 0, stopfdc_data_read = 0, stopfdc_data_reads = 0;
  integer stopprompt = 0, prompt_seen = 0, cursorstop = 0, cursor_seen = 0;
  integer fdc_ios = 0, fdc_reads = 0, fdc_writes = 0, fdc_data_reads = 0;
  integer frameirq = 0, osc_n = 0, frame_ticks = 0, intr_edges = 0, inta_edges = 0;
  integer ekdoskeys = 0, ekdos_key = 0, keyat = 42000, khold = 900000, kgap = 900000, key_t = -1;
  integer state_kbd_pos = 0, state_kbd_phase = 0;
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

  function [7:0] dram_byte(input integer addr); begin
    dram_byte = {dut.U_D91.mem[addr], dut.U_D90.mem[addr], dut.U_D89.mem[addr], dut.U_D88.mem[addr],
                 dut.U_D87.mem[addr], dut.U_D86.mem[addr], dut.U_D85.mem[addr], dut.U_D84.mem[addr]};
  end endfunction

  function [15:0] ekdos_prompt_row(input integer row); begin
    case (row)
      0: ekdos_prompt_row = 16'h0000;
      1: ekdos_prompt_row = 16'h0810;
      2: ekdos_prompt_row = 16'h1408;
      3: ekdos_prompt_row = 16'h2204;
      4: ekdos_prompt_row = 16'h2202;
      5: ekdos_prompt_row = 16'h3e04;
      6: ekdos_prompt_row = 16'h2208;
      7: ekdos_prompt_row = 16'h2210;
      8: ekdos_prompt_row = 16'h0000;
      9: ekdos_prompt_row = 16'h0000;
      default: ekdos_prompt_row = 16'hffff;
    endcase
  end endfunction

  function ekdos_prompt_ok; integer y; reg [15:0] got; begin
    ekdos_prompt_ok = 1'b1;
    for (y = 0; y < 10; y = y + 1) begin
      got = {dram_byte(16'hD800 + (70 + y) * 40), dram_byte(16'hD800 + (70 + y) * 40 + 1)};
      if (got !== ekdos_prompt_row(y)) ekdos_prompt_ok = 1'b0;
    end
  end endfunction

  function jmon33_cursor_ok; integer y; begin
    jmon33_cursor_ok = 1'b1;
    for (y = 20; y < 30; y = y + 1)
      if (dram_byte(16'hD800 + y * 40 + 1) !== 8'hFF) jmon33_cursor_ok = 1'b0;
  end endfunction

  integer fd, dump_i, dump_addr; reg [7:0] dump_b;
  task dump_vram; begin
    fd = $fopen("hdl/sim/checkpoint_vram_top.bin", "wb");
    for (dump_i = 0; dump_i < 40 * 241; dump_i = dump_i + 1) begin
      dump_addr = 16'hD800 + dump_i;
      dump_b = dram_byte(dump_addr);
      $fwrite(fd, "%c", dump_b);
    end
    $fclose(fd);
    $display("[RESUME-VRAM] dumped checkpoint VRAM -> hdl/sim/checkpoint_vram_top.bin");
    $fflush;
  end endtask

  task load_checkpoint_state; begin
    dut.U_CPU.u.core.r16_pc = state_pc[15:0];
    dut.U_CPU.u.core.r16_sp = state_sp[15:0];
    dut.U_CPU.u.core.r16_bc = state_bc[15:0];
    // Empirically, this vm80a core's r16_de/r16_hl internal names are opposite
    // the architectural DE/HL values visible in the cosim checkpoint state.
    dut.U_CPU.u.core.r16_de = state_hl[15:0];
    dut.U_CPU.u.core.r16_hl = state_de[15:0];
    dut.U_CPU.u.core.r16_wz = state_wz[15:0];
    dut.U_CPU.u.core.acc = state_a[7:0];
    dut.U_CPU.u.core.psw_s = state_sf[0];
    dut.U_CPU.u.core.psw_z = state_zf[0];
    dut.U_CPU.u.core.psw_ac = state_hf[0];
    dut.U_CPU.u.core.psw_p = state_pf[0];
    dut.U_CPU.u.core.psw_c = state_cf[0];
    dut.U_CPU.u.core.tmp_c = 1'b0;
    dut.U_CPU.u.core.inte = state_iff[0];
    dut.U_CPU.u.core.inta = 1'b0;
    dut.U_CPU.u.core.intr = 1'b0;
    dut.U_CPU.u.core.minta = 1'b0;
    dut.U_CPU.u.core.mstart = 1'b0;
    dut.U_CPU.u.core.i = 8'h00;
    dut.U_CPU.u.core.di = 8'h00;
    dut.U_CPU.u.core.db = 8'h00;
    dut.U_CPU.u.core.a = state_pc[15:0];
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

    dut.U_PPI0.regs[0] = state_kbd_col[7:0];
    dut.U_PPI0.regs[2] = state_portc[7:0];
    dut.U_PPI0.portc = state_portc[7:0];
    dut.U_PPI0.kbd_col_sel = state_kbd_col[3:0];

    dut.U_INTR.icw1 = state_pic_icw1[7:0];
    dut.U_INTR.icw2 = state_pic_icw2[7:0];
    dut.U_INTR.mask = state_pic_mask[7:0];
    dut.U_INTR.expect_icw2 = state_pic_expect_icw2[0];
    dut.U_INTR.pending = 1'b0;
    dut.U_INTR.inta_idx = 0;

    dut.U_FDC.status = state_fdc_status[7:0];
    dut.U_FDC.track = state_fdc_track[7:0];
    dut.U_FDC.sector = state_fdc_sector[7:0];
    dut.U_FDC.data = state_fdc_data[7:0];
    dut.U_FDC.command = state_fdc_command[7:0];
    dut.U_FDC.buffer_pos = state_fdc_buffer_pos;
    dut.U_FDC.buffer_len = state_fdc_buffer_len;
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
        $fflush;
        trace_resume = trace_resume - 1;
      end
      mcyc <= mcyc + 1;
    end
    sq <= dut.sync;
    if (resume_started && mcyc >= max_mcyc) begin
      $display("JUKU-TOP-CHECKPOINT-RESUME: FAIL max_mcyc pc=0x%04h ios=%0d pic_seen=%0d kbd_seen=%0d fdc_ios=%0d",
               dut.U_CPU.u.core.r16_pc, raw_ios, pic_seen, kbd_seen, fdc_ios);
      $fflush;
      $finish;
    end

    if (resume_started) begin
      if (ekdoskeys != 0) begin
        if (kbd_en && key_t < 0 && ekdos_key < 3 && keyat != 0 && vram_writes >= keyat) begin
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
      if (tracekbd && kbd_pressed && !kbd_was_pressed) begin
        $display("[RESUME-KBD-STIM] press key=%0d col=%0d bit=%0d shift=%0d mcyc=%0d vram=%0d",
                 ekdos_key, kbd_kcol, kbd_kbit, kbd_shift, mcyc, vram_writes);
        $fflush;
      end
      if (tracekbd && !kbd_pressed && kbd_was_pressed) begin
        $display("[RESUME-KBD-STIM] release key=%0d mcyc=%0d vram=%0d", ekdos_key, mcyc, vram_writes);
        $fflush;
      end
      kbd_was_pressed <= kbd_pressed;

      osc_n <= osc_n + 1;
      frame_tick <= (frameirq != 0 && (osc_n % frameirq) == (frameirq - 1));
      if (frame_tick) begin
        frame_ticks = frame_ticks + 1;
        if (traceirq > 1) begin
          $display("[RESUME-IRQ] frame_tick count=%0d mcyc=%0d vram=%0d",
                   frame_ticks, mcyc, vram_writes);
          $fflush;
        end
      end
      if (dut.intr && !intr_q) begin
        intr_edges = intr_edges + 1;
        if (traceirq) begin
          $display("[RESUME-IRQ] intr rise count=%0d mcyc=%0d vram=%0d",
                   intr_edges, mcyc, vram_writes);
          $fflush;
        end
      end
      if (!dut.inta_n && inta_q) begin
        inta_edges = inta_edges + 1;
        if (traceirq) begin
          $display("[RESUME-IRQ] inta fall count=%0d mcyc=%0d vram=%0d",
                   inta_edges, mcyc, vram_writes);
          $fflush;
        end
      end
      intr_q <= dut.intr;
      inta_q <= dut.inta_n;
    end
  end

  always @(negedge dut.memw_n) if (~dut.ram_sel_n && dut.BA >= 16'hD800) begin
    vram_writes = vram_writes + 1;
    if ((vram_writes % 100) == 0) begin
      $display("[RESUME-VRAM] writes=%0d mcyc=%0d pc=0x%04h", vram_writes, mcyc, dut.U_CPU.u.core.r16_pc);
      $fflush;
    end
    if (stopprompt != 0 && !prompt_seen && ekdos_prompt_ok()) begin
      prompt_seen = 1;
      $display("[RESUME-PROMPT] EKDOS A> prompt reached x=0 y=70 mcyc=%0d vram=%0d pc=0x%04h",
               mcyc, vram_writes, dut.U_CPU.u.core.r16_pc);
      $fflush;
      dump_vram();
      $finish;
    end
    if (cursorstop != 0 && !cursor_seen && jmon33_cursor_ok()) begin
      cursor_seen = 1;
      $display("[RESUME-CURSOR] jmon33 cursor oracle reached x=8 y=20 mcyc=%0d vram=%0d pc=0x%04h",
               mcyc, vram_writes, dut.U_CPU.u.core.r16_pc);
      $fflush;
      dump_vram();
      $finish;
    end
  end

  always @(negedge dut.iowr_n) begin
    #1;
    raw_ios = raw_ios + 1;
    if (!dut.cs_pic_n) begin
      $display("[RESUME-PIC] OUT port=0x%02h data=0x%02h mcyc=%0d vram=%0d pc=0x%04h",
               dut.BA[7:0], dut.DB, mcyc, vram_writes, dut.U_CPU.u.core.r16_pc);
      $fflush;
      if (dut.BA[0] == 1'b0 && dut.DB == 8'hD6) pic_seen = 1;
    end
    if (!dut.cs_fdc_n) begin
      fdc_ios = fdc_ios + 1;
      fdc_writes = fdc_writes + 1;
      if (tracefdc) $display("[RESUME-FDC] OUT port=0x%02h reg=%0d data=0x%02h mcyc=%0d vram=%0d ios=%0d",
                             dut.BA[7:0], dut.BA[1:0], dut.DB, mcyc, vram_writes, fdc_ios);
      if (tracefdc) $fflush;
      if (stopfdc != 0 && fdc_ios >= stopfdc) begin
        $display("[RESUME-FDC] stop ios=%0d reads=%0d writes=%0d mcyc=%0d vram=%0d",
                 fdc_ios, fdc_reads, fdc_writes, mcyc, vram_writes);
        $fflush;
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
      $fflush;
      if (dut.DB == 8'hCF) kbd_seen = 1;
    end
    if (!dut.cs_fdc_n) begin
      fdc_ios = fdc_ios + 1;
      fdc_reads = fdc_reads + 1;
      if (dut.BA[7:0] == 8'h1f) fdc_data_reads = fdc_data_reads + 1;
      if (tracefdc) $display("[RESUME-FDC] IN  port=0x%02h reg=%0d data=0x%02h mcyc=%0d vram=%0d ios=%0d",
                             dut.BA[7:0], dut.BA[1:0], dut.DB, mcyc, vram_writes, fdc_ios);
      if (tracefdc) $fflush;
      if (stopfdc_data_reads != 0 && dut.BA[7:0] == 8'h1f && fdc_data_reads >= stopfdc_data_reads) begin
        $display("[RESUME-FDC] stop reason=data-read-count target=%0d ios=%0d reads=%0d data_reads=%0d writes=%0d data=0x%02h mcyc=%0d vram=%0d",
                 stopfdc_data_reads, fdc_ios, fdc_reads, fdc_data_reads, fdc_writes, dut.DB, mcyc, vram_writes);
        $fflush;
        $finish;
      end
      if (stopfdc_data_read != 0 && dut.BA[7:0] == 8'h1f) begin
        $display("[RESUME-FDC] stop reason=data-read ios=%0d reads=%0d data_reads=%0d writes=%0d data=0x%02h mcyc=%0d vram=%0d",
                 fdc_ios, fdc_reads, fdc_data_reads, fdc_writes, dut.DB, mcyc, vram_writes);
        $fflush;
        $finish;
      end
      if (stopfdc != 0 && fdc_ios >= stopfdc) begin
        $display("[RESUME-FDC] stop ios=%0d reads=%0d writes=%0d mcyc=%0d vram=%0d",
                 fdc_ios, fdc_reads, fdc_writes, mcyc, vram_writes);
        $fflush;
        $finish;
      end
    end
    if (pic_seen && kbd_seen && stopfdc == 0 && stopfdc_data_read == 0 && stopfdc_data_reads == 0) begin
      $display("JUKU-TOP-CHECKPOINT-RESUME: PASS pc=0x%04h mcyc=%0d vram=%0d ios=%0d",
               dut.U_CPU.u.core.r16_pc, mcyc, vram_writes, raw_ios);
      $fflush;
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
    if ($value$plusargs("stopfdc_data_read=%d", stopfdc_data_read)) ;
    if ($value$plusargs("stopfdc_data_reads=%d", stopfdc_data_reads)) ;
    if ($value$plusargs("stopprompt=%d", stopprompt)) ;
    if ($value$plusargs("cursorstop=%d", cursorstop)) ;
    if ($value$plusargs("state_vram_writes=%d", state_vram_writes)) ;
    if ($value$plusargs("state_pc=%h", state_pc)) ;
    if ($value$plusargs("state_sp=%h", state_sp)) ;
    if ($value$plusargs("state_bc=%h", state_bc)) ;
    if ($value$plusargs("state_de=%h", state_de)) ;
    if ($value$plusargs("state_hl=%h", state_hl)) ;
    if ($value$plusargs("state_wz=%h", state_wz)) ;
    if ($value$plusargs("state_a=%h", state_a)) ;
    if ($value$plusargs("state_sf=%d", state_sf)) ;
    if ($value$plusargs("state_zf=%d", state_zf)) ;
    if ($value$plusargs("state_hf=%d", state_hf)) ;
    if ($value$plusargs("state_pf=%d", state_pf)) ;
    if ($value$plusargs("state_cf=%d", state_cf)) ;
    if ($value$plusargs("state_iff=%d", state_iff)) ;
    if ($value$plusargs("state_portc=%h", state_portc)) ;
    if ($value$plusargs("state_kbd_col=%h", state_kbd_col)) ;
    if ($value$plusargs("state_kbd_pos=%d", state_kbd_pos)) ;
    if ($value$plusargs("state_kbd_phase=%d", state_kbd_phase)) ;
    if ($value$plusargs("state_pic_icw1=%h", state_pic_icw1)) ;
    if ($value$plusargs("state_pic_icw2=%h", state_pic_icw2)) ;
    if ($value$plusargs("state_pic_mask=%h", state_pic_mask)) ;
    if ($value$plusargs("state_pic_expect_icw2=%d", state_pic_expect_icw2)) ;
    if ($value$plusargs("state_fdc_status=%h", state_fdc_status)) ;
    if ($value$plusargs("state_fdc_track=%h", state_fdc_track)) ;
    if ($value$plusargs("state_fdc_sector=%h", state_fdc_sector)) ;
    if ($value$plusargs("state_fdc_data=%h", state_fdc_data)) ;
    if ($value$plusargs("state_fdc_command=%h", state_fdc_command)) ;
    if ($value$plusargs("state_fdc_buffer_pos=%d", state_fdc_buffer_pos)) ;
    if ($value$plusargs("state_fdc_buffer_len=%d", state_fdc_buffer_len)) ;

    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    #2000;
    force dut.reset_sys = 1'b0;
    #400;
    clk_run = 1'b0;
    #100;

    $readmemh(ram_file, ram);
    for (i = 0; i < 65536; i = i + 1) write_dram_byte(i, ram[i]);
    vram_writes = state_vram_writes;
    load_checkpoint_state();
    if (ekdoskeys != 0 && state_vram_writes >= keyat && state_kbd_pos < 3) begin
      ekdos_key = state_kbd_pos;
      key_t = state_kbd_phase;
      set_ekdos_key(state_kbd_pos);
    end else if (ekdoskeys != 0 && state_kbd_pos >= 3) begin
      ekdos_key = state_kbd_pos;
      key_t = -1;
    end
    $display("[RESUME] loaded checkpoint pc=0x%04h sp=0x%04h", dut.U_CPU.u.core.r16_pc, dut.U_CPU.u.core.r16_sp);
    $fflush;
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
    $fflush;
    $finish;
  end
endmodule

`default_nettype wire
