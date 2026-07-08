// Guard the runnable video_raster geometry against the Juku/MAME 40x241 screen.
`timescale 1ns/100ps
`default_nettype none

module video_raster_geometry_tb;
  localparam integer COLS = 40;
  localparam integer ROWS = 241;
  localparam integer BYTES = COLS * ROWS;
  localparam integer DOTS = BYTES * 8;

  reg dotclk = 0;
  wire [15:0] vid_addr;
  wire shl_n;

  integer cycle = 0;
  integer errors = 0;
  integer expected_addr = 0;
  integer expected_shl = 0;

  video_raster dut(.dotclk(dotclk), .vid_addr(vid_addr), .shl_n(shl_n));

  always #10 dotclk = ~dotclk;

  task fail(input [255*8:1] label); begin
    $display("VIDEO-RASTER-GEOMETRY: FAIL %0s cycle=%0d addr=0x%04h shl_n=%0d expected_addr=0x%04h expected_shl_n=%0d",
             label, cycle, vid_addr, shl_n, expected_addr[15:0], expected_shl);
    errors = errors + 1;
  end endtask

  initial begin
    #1;
    if (vid_addr !== 16'hD800 || shl_n !== 1'b0) begin
      expected_addr = 16'hD800;
      expected_shl = 0;
      fail("initial load state");
    end
  end

  always @(negedge dotclk) begin
    cycle = cycle + 1;
    expected_addr = (cycle == DOTS) ? 16'hD800 : 16'hD800 + (cycle / 8);
    expected_shl = ((cycle % 8) != 0);

    if (vid_addr !== expected_addr[15:0]) fail("address sequence");
    if (shl_n !== expected_shl[0]) fail("load/shift cadence");

    if (cycle == DOTS) begin
      if (errors == 0) begin
        $display("VIDEO-RASTER-GEOMETRY: PASS cols=%0d rows=%0d bytes=%0d dots=%0d wrap_addr=0x%04h",
                 COLS, ROWS, BYTES, DOTS, vid_addr);
      end else begin
        $display("VIDEO-RASTER-GEOMETRY: FAIL errors=%0d", errors);
      end
      $finish;
    end
  end

  initial begin
    #3000000;
    $display("VIDEO-RASTER-GEOMETRY: FAIL timeout cycle=%0d addr=0x%04h shl_n=%0d",
             cycle, vid_addr, shl_n);
    $finish;
  end
endmodule
`default_nettype wire
