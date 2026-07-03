// SELF-CLOCKING boot harness -- the payoff of the faithful clock mesh. Unlike juku_top_tb (which
// force-feeds Φ1/Φ2 and toggles osc in lockstep, freezing the divider), this drives ONLY the crystal
// input `clk`. Everything else is generated inside juku_top by the running mesh:
//   D59 -> osc_clk -> D40 divider ; sclk = d40_q[0] ; Φ1/Φ2 = D35 from d40_q[1]
// If the die-accurate CPU boots the ekta37 BIOS byte-identical to the golden framebuffer while
// clocked entirely by its own divider, the mesh is proven to clock the machine -- not just wired.
// Compile with -DSELF_CLOCK (routes cpu_8080.sclk <- d40_q[0]); compare vram_selfclk.bin to the
// golden hdl/sim/vram_top.bin (the forced-clock boot).
`timescale 1ns/100ps
`default_nettype none

module juku_selfclk_tb();
  reg clk = 0;                              // the crystal (D59 xin) -- the ONLY driven clock
  integer vram_writes=0, max_vram=6000, mcyc=0;
  reg vram_seen=0, sq=0;

  juku_top dut(.clk(clk), .reset_n(1'b1), .osc(1'b0),           // osc input unused under SELF_CLOCK
               .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
               .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(1'b0));

  // reset + ready (discrete D13/D30 subsystems = boundary). The divider free-runs from t=0, so the
  // CPU sees a live Φ1/Φ2 + sclk throughout reset.
  initial begin force dut.ready=1'b1; force dut.reset_sys=1; #2000 force dut.reset_sys=0; end

  always #5 clk = ~clk;                     // 10 ns crystal -> d40_q[0] (sclk) 20 ns, Φ1/Φ2 40 ns
                                            // == the exact waveform juku_top_tb hand-crafts.

  // machine-cycle counter off the structural SYNC net (sampled on the self-generated sclk)
  always @(posedge dut.sclk_i) begin
    if (dut.sync && !sq) mcyc <= mcyc+1;
    sq <= dut.sync;
  end

  // count video writes (RAM write to >=0xD800); dump the framebuffer at the bound
  always @(negedge dut.memw_n) if (~dut.ram_sel_n && dut.BA >= 16'hD800) begin
    vram_writes = vram_writes + 1;
    if (!vram_seen) begin vram_seen=1;
      $display("[SELFCLK] first video write @0x%04h mcyc=%0d", dut.BA, mcyc); end
    if (vram_writes == max_vram) begin
      $display("[SELFCLK] %0d writes (mcyc=%0d) -- dump", vram_writes, mcyc); #60 dump_vram; $finish;
    end
  end

  integer fd, k, a; reg [7:0] b;
  task dump_vram; begin
    fd=$fopen("hdl/sim/vram_selfclk.bin","wb");
    for (k=0;k<40*241;k=k+1) begin
      a = 16'hD800 + k;
      b = {dut.U_D91.mem[a], dut.U_D90.mem[a], dut.U_D89.mem[a], dut.U_D88.mem[a],
           dut.U_D87.mem[a], dut.U_D86.mem[a], dut.U_D85.mem[a], dut.U_D84.mem[a]};
      $fwrite(fd,"%c", b);
    end
    $fclose(fd); $display("[SELFCLK] dumped VRAM -> hdl/sim/vram_selfclk.bin");
  end endtask

  integer timecap = 400000000;
  initial begin
    if ($value$plusargs("maxvram=%d", max_vram)) ;
    if ($value$plusargs("timecap=%d", timecap)) ;
  end
  initial begin #(timecap);
    $display("[SELFCLK] time cap mcyc=%0d vram_writes=%0d", mcyc, vram_writes); dump_vram; $finish;
  end
endmodule
`default_nettype wire
