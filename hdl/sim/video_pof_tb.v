// Regress the C9 physical blank-video fault at the digital POF boundary.
// Sync is deliberately outside vid_out; this oracle proves only that PC7 high
// suppresses pixels and PC7 low permits the existing framebuffer serializer.
`timescale 1ns/100ps
`default_nettype none

module video_pof_tb;
  reg dotclk = 0;
  wire vid_out;
  integer failures = 0;
  integer samples = 0;
  integer visible_ones = 0;
  integer k;

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(1'b0),
    .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
    .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(1'b0),
    .dotclk(dotclk), .vid_out(vid_out));

  always #10 dotclk = ~dotclk;

  task fail(input [1023:0] message); begin
    $display("VIDEO-POF-HDL: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  initial begin
    // Make the first 64 bytes unambiguously nonblank in every bit slice.
    for (k=0;k<64;k=k+1) begin
      dut.U_D84.mem[16'hD800+k]=1'b1; dut.U_D85.mem[16'hD800+k]=1'b1;
      dut.U_D86.mem[16'hD800+k]=1'b1; dut.U_D87.mem[16'hD800+k]=1'b1;
      dut.U_D88.mem[16'hD800+k]=1'b1; dut.U_D89.mem[16'hD800+k]=1'b1;
      dut.U_D90.mem[16'hD800+k]=1'b1; dut.U_D91.mem[16'hD800+k]=1'b1;
    end

    // C9 final state: memory mode 1 plus PC7/POF high. Every pixel must be low.
    dut.U_PPI0.portc = 8'h81;
    repeat (32) begin
      @(negedge dotclk); #1;
      if (vid_out !== 1'b0) fail("PC7 high leaked a framebuffer pixel");
    end

    // C10 final state: same mode, only PC7 released. Pixels must emerge.
    dut.U_PPI0.portc = 8'h01;
    repeat (64) begin
      @(negedge dotclk); #1;
      samples = samples + 1;
      if (vid_out === 1'b1) visible_ones = visible_ones + 1;
    end
    if (visible_ones == 0) fail("PC7 low did not release framebuffer pixels");

    // Reassertion is the negative edge of the discriminator.
    dut.U_PPI0.portc = 8'h81;
    repeat (16) begin
      @(negedge dotclk); #1;
      if (vid_out !== 1'b0) fail("reasserted POF did not blank pixels");
    end

    if (failures == 0)
      $display("VIDEO-POF-HDL: PASS C9=blank C10=visible ones=%0d/%0d",
               visible_ones, samples);
    $finish;
  end
endmodule

`default_nettype wire
