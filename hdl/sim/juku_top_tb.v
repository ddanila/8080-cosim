// Boot harness for the LVS-checked structural netlist `juku_top.v` (the merge target).
// Unlike juku_struct_tb (a parallel functional copy), this drives the SAME module the LVS
// checker compares against the KiCad board -- so a green boot here means the one model is
// simultaneously the PCB netlist, the LVS-checked structure, AND a runnable digital twin.
//
// It boots the real ekta37 BIOS byte-for-byte identical to the cosim oracle (guarded by
// sync/boot_check.sh, bounded to N video writes). The EPROM loads `+rom=` (default
// hdl/sim/ekta37.hex) via devices.v.
//
// CLOCKING: the real board's clock mesh (crystal + D59/D33/D36/D35/D38) is a documented
// un-traced boundary. The die-accurate vm80a needs a precise non-overlapping Φ1/Φ2 plus a
// fast sampling clock (osc) that rises mid-phase. We drive that lockstep here -- forcing
// Φ1/Φ2 (overriding juku_top's schematic-intent clk_phase generator, which can't carry the
// exact sub-cycle timing) and toggling osc -- exactly as juku_struct_tb does for its ports.
// RESET/READY are likewise driven (their discrete subsystems, D13/D30, are boundaries).
`timescale 1ns/100ps
`default_nettype none

module juku_top_tb();
  reg osc=0;
  integer vram_writes=0, max_vram=6000, mcyc=0, cursorstop=0, cursor_seen=0, traceprogress=0;
  reg vram_seen=0, sq=0;
  integer stoppc_en=0; reg [15:0] stoppc=16'h0000;

  // keyboard stimulus (opt-in: keyat=0 => kbd off => boot byte-identical). Press the
  // configured key once the banner is drawn (vram_writes >= keyat), hold for khold osc
  // cycles, then release so the BIOS sees a clean edge. kcol/kbit/kshift = the decoded key.
  reg kbd_en=0, kbd_pressed=0, kbd_shift=0; reg [3:0] kbd_kcol=0; reg [2:0] kbd_kbit=0;
  integer keyat=0, khold=900000, kgap=900000, key_t=-1, kcolp=0, kbitp=0, kshiftp=0;
  integer ekdoskeys=0, ekdos_key=0;
  // frame interrupt: a 1-osc-cycle pulse every `frameirq` osc cycles (8253 VER-RTR -> 8259
  // IR5). Opt-in: frameirq=0 => no pulse => intr stays 0 => boot byte-identical.
  reg frame_tick=0; integer frameirq=0, osc_n=0;

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(kbd_en), .kbd_pressed(kbd_pressed), .kbd_shift(kbd_shift),
               .kbd_kcol(kbd_kcol), .kbd_kbit(kbd_kbit), .frame_tick(frame_tick));

  // reset + ready (discrete subsystems = boundary, driven here)
  initial begin force dut.ready=1'b1; force dut.reset_sys=1; #2000 force dut.reset_sys=0; end

  // clock: Φ1 high, then Φ2 high (non-overlapping); osc rises in the middle of each phase
  // so vm80a samples the active phase. Matches juku_struct_tb / vm80a_smoke_tb timing.
  initial forever begin
    force dut.phi1=1; force dut.phi2=0; osc=0; #10; osc=1; #10;
    force dut.phi1=0; force dut.phi2=1; osc=0; #10; osc=1; #10;
    force dut.phi2=0;
  end

  task set_ekdos_key(input integer idx); begin
    kbd_shift <= 1'b1;
    if (idx == 0) begin kbd_kcol <= 4; kbd_kbit <= 3; end   // T
    else begin kbd_kcol <= 6; kbd_kbit <= 5; end             // D
  end endtask

  // count machine cycles off the structural SYNC net; drive the keyboard press window
  always @(posedge osc) begin
    if (dut.sync && !sq) mcyc <= mcyc+1;
    sq <= dut.sync;
    if (stoppc_en && dut.U_CPU.u.core.r16_pc == stoppc) begin
      $display("[PC] stop pc=0x%04h mcyc=%0d vram=%0d", dut.U_CPU.u.core.r16_pc, mcyc, vram_writes);
      #60 dump_vram; $finish;
    end
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
    end else begin
      if (kbd_en && key_t < 0 && keyat != 0 && vram_writes >= keyat) key_t <= 0;  // arm on banner
      else if (key_t >= 0) key_t <= key_t + 1;
      kbd_pressed <= (key_t >= 0 && key_t < khold);                               // hold then release
    end
    osc_n <= osc_n + 1;
    frame_tick <= (frameirq != 0 && (osc_n % frameirq) == (frameirq-1));        // periodic IR5 tick
  end

  integer traceio=0, stopio=0, raw_ios=0, raw_reads=0, raw_writes=0;
  integer tracekbd=0, traceppi=0, stopppi=0, ppi_ios=0, ppi_reads=0, ppi_writes=0, ppi_key_reads=0;
  integer tracepic=0, stoppic=0, pic_ios=0, pic_reads=0, pic_writes=0;
  reg kbd_was_pressed=0;
  integer traceirq=0, frame_ticks=0, intr_edges=0, inta_edges=0;
  reg intr_q=0, inta_q=1;
  always @(posedge osc) begin
    if (frame_tick) begin
      frame_ticks = frame_ticks + 1;
      if (traceirq > 1) $display("[IRQ] frame_tick count=%0d mcyc=%0d vram=%0d", frame_ticks, mcyc, vram_writes);
    end
    if (dut.intr && !intr_q) begin
      intr_edges = intr_edges + 1;
      if (traceirq) $display("[IRQ] intr rise count=%0d mcyc=%0d vram=%0d", intr_edges, mcyc, vram_writes);
    end
    if (!dut.inta_n && inta_q) begin
      inta_edges = inta_edges + 1;
      if (traceirq) $display("[IRQ] inta fall count=%0d mcyc=%0d vram=%0d", inta_edges, mcyc, vram_writes);
    end
    intr_q <= dut.intr;
    inta_q <= dut.inta_n;
  end

  always @(negedge dut.iowr_n) begin
    #1;
    raw_ios = raw_ios + 1;
    raw_writes = raw_writes + 1;
    if (traceio) $display("[RAWIO] OUT ba=0x%04h port=0x%02h data=0x%02h mcyc=%0d vram=%0d ios=%0d pic=%0d ppi0=%0d sio0=%0d ppi1=%0d pit0=%0d pit1=%0d pit2=%0d fdc=%0d",
                          dut.BA, dut.BA[7:0], dut.DB, mcyc, vram_writes, raw_ios,
                          !dut.cs_pic_n, !dut.cs_ppi0_n, !dut.cs_sio0_n, !dut.cs_ppi1_n,
                          !dut.cs_pit0_n, !dut.cs_pit1_n, !dut.cs_pit2_n, !dut.cs_fdc_n);
    if (stopio != 0 && raw_ios >= stopio) begin
      $display("[RAWIO] stop ios=%0d reads=%0d writes=%0d mcyc=%0d vram=%0d",
               raw_ios, raw_reads, raw_writes, mcyc, vram_writes);
      #60 dump_vram; $finish;
    end
  end
  always @(negedge dut.iord_n) begin
    #1;
    raw_ios = raw_ios + 1;
    raw_reads = raw_reads + 1;
    if (traceio) $display("[RAWIO] IN  ba=0x%04h port=0x%02h data=0x%02h mcyc=%0d vram=%0d ios=%0d pic=%0d ppi0=%0d sio0=%0d ppi1=%0d pit0=%0d pit1=%0d pit2=%0d fdc=%0d",
                          dut.BA, dut.BA[7:0], dut.DB, mcyc, vram_writes, raw_ios,
                          !dut.cs_pic_n, !dut.cs_ppi0_n, !dut.cs_sio0_n, !dut.cs_ppi1_n,
                          !dut.cs_pit0_n, !dut.cs_pit1_n, !dut.cs_pit2_n, !dut.cs_fdc_n);
    if (stopio != 0 && raw_ios >= stopio) begin
      $display("[RAWIO] stop ios=%0d reads=%0d writes=%0d mcyc=%0d vram=%0d",
               raw_ios, raw_reads, raw_writes, mcyc, vram_writes);
      #60 dump_vram; $finish;
    end
  end

  always @(posedge osc) begin
    if (tracekbd && kbd_pressed && !kbd_was_pressed)
      $display("[KBD] press key=%0d col=%0d bit=%0d shift=%0d mcyc=%0d vram=%0d",
               ekdos_key, kbd_kcol, kbd_kbit, kbd_shift, mcyc, vram_writes);
    if (tracekbd && !kbd_pressed && kbd_was_pressed)
      $display("[KBD] release key=%0d mcyc=%0d vram=%0d", ekdos_key, mcyc, vram_writes);
    kbd_was_pressed <= kbd_pressed;
  end

  always @(negedge dut.iowr_n) begin #1; if (!dut.cs_pic_n) begin
      pic_ios = pic_ios + 1;
      pic_writes = pic_writes + 1;
      if (tracepic) $display("[PIC] OUT port=0x%02h reg=%0d data=0x%02h mcyc=%0d vram=%0d ios=%0d",
                             {7'b0000000, dut.BA[0]}, dut.BA[0], dut.DB, mcyc, vram_writes, pic_ios);
      if (stoppic != 0 && pic_ios >= stoppic) begin
        $display("[PIC] stop ios=%0d reads=%0d writes=%0d mcyc=%0d vram=%0d",
                 pic_ios, pic_reads, pic_writes, mcyc, vram_writes);
        #60 dump_vram; $finish;
      end
    end
  end
  always @(negedge dut.iord_n) begin #1; if (!dut.cs_pic_n) begin
      pic_ios = pic_ios + 1;
      pic_reads = pic_reads + 1;
      if (tracepic) $display("[PIC] IN  port=0x%02h reg=%0d data=0x%02h mcyc=%0d vram=%0d ios=%0d",
                             {7'b0000000, dut.BA[0]}, dut.BA[0], dut.DB, mcyc, vram_writes, pic_ios);
      if (stoppic != 0 && pic_ios >= stoppic) begin
        $display("[PIC] stop ios=%0d reads=%0d writes=%0d mcyc=%0d vram=%0d",
                 pic_ios, pic_reads, pic_writes, mcyc, vram_writes);
        #60 dump_vram; $finish;
      end
    end
  end

  always @(negedge dut.iowr_n) begin #1; if (!dut.cs_ppi0_n) begin
      ppi_ios = ppi_ios + 1;
      ppi_writes = ppi_writes + 1;
      if (traceppi > 1) $display("[PPI0] OUT port=0x%02h reg=%0d data=0x%02h mcyc=%0d ios=%0d",
                                 {6'b000001, dut.BA[1:0]}, dut.BA[1:0], dut.DB, mcyc, ppi_ios);
      if (stopppi != 0 && ppi_ios >= stopppi) begin
        $display("[PPI0] stop ios=%0d reads=%0d writes=%0d key_reads=%0d mcyc=%0d",
                 ppi_ios, ppi_reads, ppi_writes, ppi_key_reads, mcyc);
        #60 dump_vram; $finish;
      end
    end
  end
  always @(negedge dut.iord_n) begin #1; if (!dut.cs_ppi0_n) begin
      ppi_ios = ppi_ios + 1;
      ppi_reads = ppi_reads + 1;
      if (dut.BA[1:0] == 2'd1 && kbd_pressed) begin
        ppi_key_reads = ppi_key_reads + 1;
        if (traceppi) $display("[PPI0] IN  port=0x%02h reg=%0d data=0x%02h col=%0d key_col=%0d key_bit=%0d mcyc=%0d key_reads=%0d",
                               {6'b000001, dut.BA[1:0]}, dut.BA[1:0], dut.DB,
                               dut.U_PPI0.kbd_col_sel, kbd_kcol, kbd_kbit, mcyc, ppi_key_reads);
      end
      if (stopppi != 0 && ppi_ios >= stopppi) begin
        $display("[PPI0] stop ios=%0d reads=%0d writes=%0d key_reads=%0d mcyc=%0d",
                 ppi_ios, ppi_reads, ppi_writes, ppi_key_reads, mcyc);
        #60 dump_vram; $finish;
      end
    end
  end

  integer tracefdc=0, stopfdc=0, fdc_ios=0, fdc_reads=0, fdc_writes=0;
  always @(negedge dut.iowr_n) begin #1; if (!dut.cs_fdc_n) begin
      fdc_ios = fdc_ios + 1;
      fdc_writes = fdc_writes + 1;
      if (tracefdc) $display("[FDC] OUT port=0x%02h reg=%0d data=0x%02h mcyc=%0d ios=%0d",
                             {6'b000111, dut.BA[1:0]}, dut.BA[1:0], dut.DB, mcyc, fdc_ios);
      if (stopfdc != 0 && fdc_ios >= stopfdc) begin
        $display("[FDC] stop ios=%0d reads=%0d writes=%0d mcyc=%0d", fdc_ios, fdc_reads, fdc_writes, mcyc);
        #60 dump_vram; $finish;
      end
    end
  end
  always @(negedge dut.iord_n) begin #1; if (!dut.cs_fdc_n) begin
      fdc_ios = fdc_ios + 1;
      fdc_reads = fdc_reads + 1;
      if (tracefdc) $display("[FDC] IN  port=0x%02h reg=%0d data=0x%02h mcyc=%0d ios=%0d",
                             {6'b000111, dut.BA[1:0]}, dut.BA[1:0], dut.DB, mcyc, fdc_ios);
      if (stopfdc != 0 && fdc_ios >= stopfdc) begin
        $display("[FDC] stop ios=%0d reads=%0d writes=%0d mcyc=%0d", fdc_ios, fdc_reads, fdc_writes, mcyc);
        #60 dump_vram; $finish;
      end
    end
  end

  // count video writes (RAM write to >=0xD800); dump the framebuffer at the bound
  always @(negedge dut.memw_n) if (~dut.ram_sel_n && dut.BA >= 16'hD800) begin
    vram_writes = vram_writes + 1;
    if (!vram_seen) begin vram_seen=1;
      $display("[VRAM] first video write @0x%04h mcyc=%0d", dut.BA, mcyc); end
    if (traceprogress != 0 && (vram_writes % traceprogress) == 0)
      $display("[VRAM] progress writes=%0d mcyc=%0d", vram_writes, mcyc);
    if (cursorstop && !cursor_seen && cursor_oracle_ok()) begin
      cursor_seen = 1;
      $display("[VRAM] jmon33 cursor oracle reached (mcyc=%0d writes=%0d)", mcyc, vram_writes);
      #60 dump_vram; $finish;
    end
    if (vram_writes == max_vram) begin
      $display("[VRAM] %0d writes (mcyc=%0d) -- dump", vram_writes, mcyc); #60 dump_vram; $finish;
    end
  end

  // The framebuffer lives in the 8 bit-sliced К565РУ5 DRAMs (D60=bit0 .. D67=bit7);
  // reconstruct each byte from the eight 1-bit planes.
  integer fd, k, a; reg [7:0] b;
  function [7:0] dram_byte(input integer addr); begin
    dram_byte = {dut.U_D91.mem[addr], dut.U_D90.mem[addr], dut.U_D89.mem[addr], dut.U_D88.mem[addr],
                 dut.U_D87.mem[addr], dut.U_D86.mem[addr], dut.U_D85.mem[addr], dut.U_D84.mem[addr]};
  end endfunction
  function cursor_oracle_ok; integer y; begin
    cursor_oracle_ok = 1'b1;
    for (y=20; y<30; y=y+1)
      if (dram_byte(16'hD800 + y*40 + 1) !== 8'hFF) cursor_oracle_ok = 1'b0;
  end endfunction
  task dump_vram; begin
    fd=$fopen("hdl/sim/vram_top.bin","wb");
    for (k=0;k<40*241;k=k+1) begin
      a = 16'hD800 + k;
      b = dram_byte(a);
      $fwrite(fd,"%c", b);
    end
    $fclose(fd); $display("[SIM] dumped VRAM -> hdl/sim/vram_top.bin");
    $display("[CPU] pc=0x%04h sp=0x%04h instr=0x%02h ba=0x%04h db=0x%02h mcyc=%0d vram=%0d memr_n=%0d memw_n=%0d iord_n=%0d iowr_n=%0d inta_n=%0d sync=%0d intr=%0d",
             dut.U_CPU.u.core.r16_pc, dut.U_CPU.u.core.r16_sp, dut.U_CPU.u.core.i,
             dut.BA, dut.DB, mcyc, vram_writes, dut.memr_n, dut.memw_n, dut.iord_n,
             dut.iowr_n, dut.inta_n, dut.sync, dut.intr);
    $display("[STATE] pc=%04h sp=%04h a=%02h b=%02h c=%02h d=%02h e=%02h h=%02h l=%02h sf=%0d zf=%0d hf=%0d pf=%0d cf=%0d iff=%0d mode=%0d portc=%02h kbd_col=%02h pic_icw1=%02h pic_icw2=%02h pic_mask=%02h pic_expect_icw2=%0d fdc_motor_on=%0d fdc_status=%02h fdc_track=%02h fdc_sector=%02h fdc_data=%02h fdc_command=%02h fdc_buffer_pos=%0d fdc_buffer_len=%0d",
             dut.U_CPU.u.core.r16_pc, dut.U_CPU.u.core.r16_sp, dut.U_CPU.u.core.acc,
             dut.U_CPU.u.core.r16_bc[15:8], dut.U_CPU.u.core.r16_bc[7:0],
             dut.U_CPU.u.core.r16_hl[15:8], dut.U_CPU.u.core.r16_hl[7:0],
             dut.U_CPU.u.core.r16_de[15:8], dut.U_CPU.u.core.r16_de[7:0],
             dut.U_CPU.u.core.psw_s, dut.U_CPU.u.core.psw_z, dut.U_CPU.u.core.psw_ac,
             dut.U_CPU.u.core.psw_p, dut.U_CPU.u.core.psw_c, dut.U_CPU.u.core.inte,
             dut.mem_mode, dut.U_PPI0.portc, {4'b0000, dut.U_PPI0.kbd_col_sel},
             dut.U_INTR.icw1, dut.U_INTR.icw2, dut.U_INTR.mask, dut.U_INTR.expect_icw2,
             dut.ppi0_pc[2], dut.U_FDC.status, dut.U_FDC.track, dut.U_FDC.sector,
             dut.U_FDC.data, dut.U_FDC.command, dut.U_FDC.buffer_pos, dut.U_FDC.buffer_len);
    if (traceio || tracekbd || tracepic || traceppi || tracefdc || traceirq)
      $display("[IO] raw_ios=%0d raw_reads=%0d raw_writes=%0d pic_ios=%0d pic_reads=%0d pic_writes=%0d ppi_ios=%0d ppi_reads=%0d ppi_writes=%0d ppi_key_reads=%0d fdc_ios=%0d fdc_reads=%0d fdc_writes=%0d frame_ticks=%0d intr_edges=%0d inta_edges=%0d",
               raw_ios, raw_reads, raw_writes, pic_ios, pic_reads, pic_writes, ppi_ios, ppi_reads, ppi_writes, ppi_key_reads, fdc_ios, fdc_reads, fdc_writes,
               frame_ticks, intr_edges, inta_edges);
  end endtask

  integer timecap = 400000000;       // ns; enough for the 6000-write boot guard. Interactive
                                      // runs (full banner + key) need more -> raise via +timecap.
  initial begin
    if ($value$plusargs("maxvram=%d", max_vram)) ;
    if ($value$plusargs("traceprogress=%d", traceprogress)) ;
    if ($value$plusargs("stoppc=%h", stoppc)) stoppc_en = 1;
    if ($value$plusargs("timecap=%d", timecap)) ;
    if ($value$plusargs("keyat=%d",  keyat))  ;          // press key after N video writes
    if ($value$plusargs("kcol=%d",   kcolp))  ;          // decoded key column 0-15
    if ($value$plusargs("kbit=%d",   kbitp))  ;          // decoded key row bit 0-7
    if ($value$plusargs("kshift=%d", kshiftp)) ;         // 1 = SHIFT held (uppercase)
    if ($value$plusargs("khold=%d",  khold))  ;
    if ($value$plusargs("kgap=%d",   kgap))   ;
    if ($value$plusargs("ekdoskeys=%d", ekdoskeys)) ;    // fixed T,D,D sequence
    if ($value$plusargs("traceio=%d", traceio)) ;
    if ($value$plusargs("stopio=%d", stopio)) ;
    if ($value$plusargs("tracekbd=%d", tracekbd)) ;
    if ($value$plusargs("tracepic=%d", tracepic)) ;
    if ($value$plusargs("stoppic=%d", stoppic)) ;
    if ($value$plusargs("traceppi=%d", traceppi)) ;
    if ($value$plusargs("stopppi=%d", stopppi)) ;
    if ($value$plusargs("traceirq=%d", traceirq)) ;
    if ($value$plusargs("tracefdc=%d", tracefdc)) ;
    if ($value$plusargs("stopfdc=%d", stopfdc)) ;
    if ($value$plusargs("frameirq=%d", frameirq)) ;     // 0=off (boot-identical)
    if ($value$plusargs("cursorstop=%d", cursorstop)) ; // stop when jmon33 idle cursor is in VRAM
    if (keyat != 0) begin
      kbd_en=1;
      if (ekdoskeys == 0) begin kbd_kcol=kcolp[3:0]; kbd_kbit=kbitp[2:0]; kbd_shift=kshiftp[0]; end
    end
  end
  initial begin #(timecap);       // time cap (the bit-sliced DRAM makes this sim heavy)
    $display("[SIM] time cap mcyc=%0d vram_writes=%0d", mcyc, vram_writes); dump_vram; $finish;
  end
endmodule
`default_nettype wire
