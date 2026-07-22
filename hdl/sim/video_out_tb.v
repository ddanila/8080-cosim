// Runnable abstract-serializer check. Preload a banner framebuffer into juku_top's bit-sliced РУ5,
// run the dot clock, and capture its sim-only vid_out pixel bitstream, then reconstruct the image.
// If it matches the loaded framebuffer, the video_raster -> ИР16 -> ЛП5 oracle faithfully turns
// stored bytes into serial bits. This is not D34/X7 composite: sync summing, VT2, loading, voltage,
// and physical µP/video arbitration are absent (the test uses the РУ5 second read port).
`timescale 1ns/100ps
`default_nettype none

module video_out_tb;
  reg dotclk = 0;
  wire vid_out;

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(1'b0),
    .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0), .kbd_kcol(4'b0), .kbd_kbit(3'b0),
    .frame_tick(1'b0), .dotclk(dotclk), .vid_out(vid_out));

  // preload the banner framebuffer into the bit-sliced РУ5 (bit j of byte k -> chip D6j)
  reg [7:0] fb [0:16383]; integer k;
  initial begin
    $readmemh("hdl/sim/vram_top.hex", fb);
    for (k=0;k<40*241;k=k+1) begin
      dut.U_D84.mem[16'hD800+k]=fb[k][0]; dut.U_D85.mem[16'hD800+k]=fb[k][1];
      dut.U_D86.mem[16'hD800+k]=fb[k][2]; dut.U_D87.mem[16'hD800+k]=fb[k][3];
      dut.U_D88.mem[16'hD800+k]=fb[k][4]; dut.U_D89.mem[16'hD800+k]=fb[k][5];
      dut.U_D90.mem[16'hD800+k]=fb[k][6]; dut.U_D91.mem[16'hD800+k]=fb[k][7];
    end
  end
  always #10 dotclk = ~dotclk;

  // capture the abstract bitstream: internal video_raster scans 0xD800.. in lockstep, MSB-first
  reg [7:0] recon [0:16383]; reg [2:0] cpix = 0; integer caddr = 0; reg [7:0] csh; reg done = 0;
  integer fd, i;
  always @(negedge dotclk) if (!done) begin
    csh[3'd7 - cpix] = vid_out;
    if (cpix == 3'd7) begin
      recon[caddr] = csh;
      if (caddr == 40*241 - 1) begin done = 1; dump_vid; end
      else begin caddr = caddr + 1; cpix = 0; end
    end else cpix = cpix + 1;
  end

  task dump_vid; begin
    fd = $fopen("hdl/sim/vram_vidout.bin","wb");
    for (i=0;i<40*241;i=i+1) $fwrite(fd,"%c", recon[i]);
    $fclose(fd);
    $display("[vidout] captured %0d bytes from juku_top's abstract pixel oracle -> hdl/sim/vram_vidout.bin", 40*241);
    $finish;
  end endtask
  initial begin #6000000; $display("[vidout] TIMEOUT caddr=%0d", caddr); $finish; end
endmodule
`default_nettype wire
