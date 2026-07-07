// Load a cosim checkpoint RAM image into the LVS-checked juku_top DRAM planes.
//
// This is a pre-resume diagnostic: it proves the 64 KiB checkpoint RAM can be
// represented byte-for-byte in the bit-sliced D84..D91 DRAM instances without
// replaying the slow ROMBIOS framebuffer draw.
`timescale 1ns/100ps
`default_nettype none

module juku_top_checkpoint_load_tb();
  reg osc = 0;
  integer i, fd, a;
  reg [1023:0] ram_file;
  reg [7:0] ram [0:65535];
  reg [7:0] b;

  juku_top dut(.clk(1'b0), .reset_n(1'b1), .osc(osc),
               .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
               .kbd_kcol(4'd0), .kbd_kbit(3'd0), .frame_tick(1'b0));

  initial forever begin osc = 0; #10; osc = 1; #10; end

  function [7:0] dram_byte(input integer addr); begin
    dram_byte = {dut.U_D91.mem[addr], dut.U_D90.mem[addr], dut.U_D89.mem[addr], dut.U_D88.mem[addr],
                 dut.U_D87.mem[addr], dut.U_D86.mem[addr], dut.U_D85.mem[addr], dut.U_D84.mem[addr]};
  end endfunction

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

  initial begin
    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    force dut.phi1 = 1'b0;
    force dut.phi2 = 1'b0;
    if (!$value$plusargs("checkpoint_ram=%s", ram_file)) begin
      $display("JUKU-TOP-CHECKPOINT-LOAD: FAIL missing +checkpoint_ram=<hex>");
      $finish;
    end

    $readmemh(ram_file, ram);
    for (i = 0; i < 65536; i = i + 1) write_dram_byte(i, ram[i]);

    fd = $fopen("hdl/sim/checkpoint_ram_top.bin", "wb");
    for (a = 0; a < 65536; a = a + 1) begin
      b = dram_byte(a);
      $fwrite(fd, "%c", b);
      if (b !== ram[a]) begin
        $display("JUKU-TOP-CHECKPOINT-LOAD: FAIL addr=0x%04h got=0x%02h want=0x%02h", a[15:0], b, ram[a]);
        $finish;
      end
    end
    $fclose(fd);

    fd = $fopen("hdl/sim/checkpoint_vram_top.bin", "wb");
    for (a = 0; a < 40*241; a = a + 1) begin
      b = dram_byte(16'hD800 + a);
      $fwrite(fd, "%c", b);
    end
    $fclose(fd);

    $display("JUKU-TOP-CHECKPOINT-LOAD: PASS");
    $finish;
  end
endmodule

`default_nettype wire
