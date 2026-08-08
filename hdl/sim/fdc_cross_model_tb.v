`timescale 1ns/100ps
`default_nettype none

module fdc_cross_model_tb;
  reg clk = 1'b1;
  reg cs_n = 1'b1, rd_n = 1'b1, wr_n = 1'b1;
  reg motor_on = 1'b0, side = 1'b0, ready = 1'b1, index = 1'b0;
  reg hlt = 1'b1, tr00 = 1'b0, clock_2mhz = 1'b1;
  reg [1:0] A = 2'b00;
  reg [7:0] drive = 8'h00;
  reg drive_en = 1'b0;
  wire [7:0] D = drive_en ? drive : 8'hzz;
  wire drq, intrq, step, dirc;

  fdc_1793 dut(.A(A), .D(D), .cs_n(cs_n), .rd_n(rd_n), .wr_n(wr_n),
               .mr_n(1'b1), .clk(clk), .clock_2mhz(clock_2mhz),
               .dden(1'b0), .nc_back_bias(1'b0), .vss_gnd(1'b0),
               .vcc_5v(1'b1), .vdd_12v(1'b1), .step(step), .dirc(dirc),
               .early(), .late(), .rg(), .hld(), .tg43(), .wg(), .wdata(),
               .test(1'b0), .hlt(hlt), .rclk(1'b0), .raw_read(1'b0),
               .ready(ready), .tr00(tr00), .index(index), .wprt(1'b0),
               .wf_vfoe(), .motor_on(motor_on), .side(side),
               .drq(drq), .intrq(intrq));

  integer fd, code, a, b, index_no = 0, tick_no;
  reg [7:0] op;
  reg [7:0] read_value;
  reg [1023:0] vector_path;

  task write_reg(input [1:0] regno, input [7:0] value); begin
    A = regno; drive = value; drive_en = 1'b1; cs_n = 1'b0; wr_n = 1'b0;
    #1; wr_n = 1'b1; cs_n = 1'b1; drive_en = 1'b0; #1;
  end endtask

  task read_reg(input [1:0] regno, output [7:0] value); begin
    A = regno; drive_en = 1'b0; cs_n = 1'b0; rd_n = 1'b0;
    #1; value = D; rd_n = 1'b1; cs_n = 1'b1; #1;
  end endtask

  task print_state; begin
    $display("STATE %0d %02x %02x %02x %02x %02x %0d %0d %0d %0d",
             index_no, dut.effective_status, dut.track, dut.physical_track, dut.sector,
             dut.data, drq, intrq, dut.head_loaded, dut.step_dir_in);
  end endtask

  initial begin
    if (!$value$plusargs("vectors=%s", vector_path)) begin
      $display("FDC-CROSS: missing +vectors=FILE");
      $finish;
    end
    fd = $fopen(vector_path, "r");
    if (!fd) begin
      $display("FDC-CROSS: cannot open vector file");
      $finish;
    end
    while (!$feof(fd)) begin
      code = $fscanf(fd, " %s %h %h\n", op, a, b);
      if (code == 3) begin
        case (op)
          "P": begin
            motor_on = a[2]; clock_2mhz = a[3]; side = a[6];
          end
          "H": hlt = a[0];
          "T": tr00 = a[0];
          "Y": ready = a[0];
          "I": index = a[0];
          "W": write_reg(a[1:0], b[7:0]);
          "K": begin
            for (tick_no = 0; tick_no < a; tick_no = tick_no + 1) begin
              clk = 1'b0; #1; clk = 1'b1; #1;
            end
          end
          "R": begin
            read_reg(a[1:0], read_value);
            $display("READ %0d %02x", index_no, read_value);
          end
          default: begin
            $display("FDC-CROSS: unknown operation %0s", op);
            $finish;
          end
        endcase
        #1; print_state(); index_no = index_no + 1;
      end
    end
    $fclose(fd);
    $display("FDC-CROSS: COMPLETE %0d", index_no);
    $finish;
  end
endmodule
`default_nettype wire
