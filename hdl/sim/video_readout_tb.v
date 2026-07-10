// Video-readout demo (arc V1): serialize a real framebuffer through the ИР16 (ir16_sr) pixel
// shift-register at the dot clock -- exactly what the video output stage does -- capture the serial
// pixel stream, and reconstruct the image from it. If the reconstruction == the input framebuffer,
// the serializer + readout timing faithfully turn stored bytes into the pixel stream a display sees.
// (The µP/video КП14 arbitration on the shared РУ5 remains open; here we read the framebuffer
// array directly, since a sim read doesn't contend.) Loads hdl/sim/vram_top.hex (a booted screen).
`timescale 1ns/100ps
`default_nettype none

module video_readout_tb;
  localparam integer N = 40*241;        // 9640 framebuffer bytes (40 cols x 241 rows)
  reg [7:0] fb [0:16383];               // source framebuffer
  reg [7:0] recon [0:16383];            // image reconstructed from the serial stream
  integer i, fd;

  reg clk = 0;                          // 16 MHz dot clock
  reg [2:0] pix = 0;                    // pixel within the current char byte (0..7)
  reg [13:0] addr = 0;                  // byte address (video raster counter stand-in)
  reg [7:0] sh; reg done = 0;
  wire shl_n = (pix != 3'd0);           // LOAD at pixel 0, SHIFT for pixels 1..7
  wire pixel;                           // serial pixel out of the ИР16

  ir16_sr ir (.clk(clk), .clk_inh(1'b0), .shl_n(shl_n), .clr_n(1'b1), .si(1'b0),
              .d(fb[addr]), .so(pixel));

  initial begin
    for (i=0;i<16384;i=i+1) begin fb[i]=0; recon[i]=0; end
    $readmemh("hdl/sim/vram_top.hex", fb);
  end
  always #10 clk = ~clk;                // 20 ns period

  // sample the serial bit after each rising edge (ИР16 has loaded/shifted); MSB first
  always @(negedge clk) if (!done) begin
    sh[3'd7 - pix] = pixel;
    if (pix == 3'd7) begin
      recon[addr] = sh;
      if (addr == N-1) begin done = 1; dump_img; end
      else begin addr = addr + 1'b1; pix = 0; end
    end else pix = pix + 1'b1;
  end

  task dump_img; begin
    fd = $fopen("hdl/sim/vram_readout.bin","wb");
    for (i=0;i<N;i=i+1) $fwrite(fd,"%c", recon[i]);
    $fclose(fd);
    $display("[readout] serialized %0d bytes through the ИР16 -> hdl/sim/vram_readout.bin", N);
    $finish;
  end endtask

  initial begin #6000000; $display("[readout] TIMEOUT at addr=%0d", addr); $finish; end
endmodule
`default_nettype wire
