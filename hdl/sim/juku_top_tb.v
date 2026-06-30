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
  integer vram_writes=0, max_vram=6000, mcyc=0;
  reg vram_seen=0, sq=0;

  // keyboard stimulus (opt-in: keyat=0 => kbd off => boot byte-identical). Press the
  // configured key once the banner is drawn (vram_writes >= keyat), hold for khold osc
  // cycles, then release so the BIOS sees a clean edge. kcol/kbit/kshift = the decoded key.
  reg kbd_en=0, kbd_pressed=0, kbd_shift=0; reg [3:0] kbd_kcol=0; reg [2:0] kbd_kbit=0;
  integer keyat=0, khold=900000, key_t=-1, kcolp=0, kbitp=0, kshiftp=0;
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

  // count machine cycles off the structural SYNC net; drive the keyboard press window
  always @(posedge osc) begin
    if (dut.sync && !sq) mcyc <= mcyc+1;
    sq <= dut.sync;
    if (kbd_en && key_t < 0 && keyat != 0 && vram_writes >= keyat) key_t <= 0;  // arm on banner
    else if (key_t >= 0) key_t <= key_t + 1;
    kbd_pressed <= (key_t >= 0 && key_t < khold);                               // hold then release
    osc_n <= osc_n + 1;
    frame_tick <= (frameirq != 0 && (osc_n % frameirq) == (frameirq-1));        // periodic IR5 tick
  end

  // count video writes (RAM write to >=0xD800); dump the framebuffer at the bound
  always @(negedge dut.memw_n) if (~dut.ram_sel_n && dut.BA >= 16'hD800) begin
    vram_writes = vram_writes + 1;
    if (!vram_seen) begin vram_seen=1;
      $display("[VRAM] first video write @0x%04h mcyc=%0d", dut.BA, mcyc); end
    if (vram_writes == max_vram) begin
      $display("[VRAM] %0d writes (mcyc=%0d) -- dump", vram_writes, mcyc); #60 dump_vram; $finish;
    end
  end

  // The framebuffer lives in the 8 bit-sliced К565РУ5 DRAMs (D60=bit0 .. D67=bit7);
  // reconstruct each byte from the eight 1-bit planes.
  integer fd, k, a; reg [7:0] b;
  task dump_vram; begin
    fd=$fopen("hdl/sim/vram_top.bin","wb");
    for (k=0;k<40*241;k=k+1) begin
      a = 16'hD800 + k;
      b = {dut.U_D67.mem[a], dut.U_D66.mem[a], dut.U_D65.mem[a], dut.U_D64.mem[a],
           dut.U_D63.mem[a], dut.U_D62.mem[a], dut.U_D61.mem[a], dut.U_D60.mem[a]};
      $fwrite(fd,"%c", b);
    end
    $fclose(fd); $display("[SIM] dumped VRAM -> hdl/sim/vram_top.bin");
  end endtask

  integer timecap = 400000000;       // ns; enough for the 6000-write boot guard. Interactive
                                      // runs (full banner + key) need more -> raise via +timecap.
  initial begin
    if ($value$plusargs("maxvram=%d", max_vram)) ;
    if ($value$plusargs("timecap=%d", timecap)) ;
    if ($value$plusargs("keyat=%d",  keyat))  ;          // press key after N video writes
    if ($value$plusargs("kcol=%d",   kcolp))  ;          // decoded key column 0-15
    if ($value$plusargs("kbit=%d",   kbitp))  ;          // decoded key row bit 0-7
    if ($value$plusargs("kshift=%d", kshiftp)) ;         // 1 = SHIFT held (uppercase)
    if ($value$plusargs("khold=%d",  khold))  ;
    if ($value$plusargs("frameirq=%d", frameirq)) ;     // 0=off (boot-identical)
    if (keyat != 0) begin kbd_en=1; kbd_kcol=kcolp[3:0]; kbd_kbit=kbitp[2:0]; kbd_shift=kshiftp[0]; end
  end
  initial begin #(timecap);       // time cap (the bit-sliced DRAM makes this sim heavy)
    $display("[SIM] time cap mcyc=%0d vram_writes=%0d", mcyc, vram_writes); dump_vram; $finish;
  end
endmodule
`default_nettype wire
