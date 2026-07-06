`timescale 1ns/100ps
`default_nettype none

module beeper_path_tb;
  reg [1:0] A = 0;
  tri [7:0] D;
  reg [7:0] drive_d = 0;
  reg drive = 0, cs_n = 1, rd_n = 1, wr_n = 1;
  reg clk1 = 0;
  wire pit_baud, sound, sync_b;

  assign D = drive ? drive_d : 8'bz;

  pit_8253 U_D57(.A(A), .D(D), .cs_n(cs_n), .rd_n(rd_n), .wr_n(wr_n), .clk(1'b0),
                 .clk0(1'b0), .gate0(1'b1), .clk1(clk1), .gate1(1'b1),
                 .clk2(1'b0), .gate2(1'b1),
                 .out0(pit_baud), .out1(sound), .out2(sync_b));

  always #5 clk1 = ~clk1;

  task pit_write(input [1:0] addr, input [7:0] value);
    begin
      @(negedge clk1);
      A = addr; drive_d = value; drive = 1; cs_n = 0; wr_n = 0;
      @(negedge clk1);
      wr_n = 1; cs_n = 1; drive = 0;
    end
  endtask

  integer edges = 0;
  reg last_sound = 0;
  always @(posedge clk1) begin
    if (sound !== last_sound) begin
      edges = edges + 1;
      last_sound = sound;
    end
  end

  initial begin
    // D57 channel 1 is the traced SOUND source. Program channel 1 for lsb/msb,
    // mode 3 style control, count=4; the minimal PIT model should toggle OUT1.
    pit_write(2'd3, 8'h76);
    pit_write(2'd1, 8'h04);
    pit_write(2'd1, 8'h00);
    repeat (40) @(posedge clk1);
    if (edges >= 2) begin
      $display("BEEPER-PATH: PASS sound toggled edges=%0d", edges);
    end else begin
      $display("BEEPER-PATH: FAIL sound did not toggle edges=%0d", edges);
    end
    $finish;
  end
endmodule

`default_nettype wire
