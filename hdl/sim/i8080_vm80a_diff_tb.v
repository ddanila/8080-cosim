`timescale 1ns/100ps
`default_nettype none

// Execute one generated instruction at a time from a directly seeded clean M1
// boundary. Architectural state and all write-side effects are compared with
// the C i8080 core by tests/i8080_vm80a_diff_test.py.
module i8080_vm80a_diff_tb;
  localparam [15:0] PROGRAM = 16'h2000;

  tri1 [7:0] d;
  wire [15:0] a_bus;
  reg clk = 1'b0, f1 = 1'b0, f2 = 1'b0, reset = 1'b1;
  reg ready = 1'b1;
  wire inte, sync, dbin, wr_n;
  reg [7:0] mem [0:65535];
  reg [7:0] status = 8'h00, read_data = 8'h00;
  reg sync_q = 1'b0;
  reg active = 1'b0, done = 1'b0, stop_after_fetch = 1'b0;
  integer fetch_count = 0;
  reg [15:0] next_pc = PROGRAM;

  integer fd, code, i, cycles;
  integer vector_index, opcode, flags, op1, op2, reg_a;
  integer reg_bc, reg_de, reg_hl, reg_sp, reg_iff;
  integer mem_hl, stack_lo, stack_hi;
  integer write_count = 0;
  reg [15:0] written [0:3];
  reg [1023:0] vector_path;

  vm80a cpu (
    .pin_clk(clk), .pin_f1(f1), .pin_f2(f2), .pin_reset(reset),
    .pin_a(a_bus), .pin_d(d), .pin_hold(1'b0), .pin_hlda(),
    .pin_ready(ready), .pin_wait(), .pin_int(1'b0), .pin_inte(inte),
    .pin_sync(sync), .pin_dbin(dbin), .pin_wr_n(wr_n)
  );

  wire [15:0] architectural_de = cpu.core.xchg_dh
      ? cpu.core.r16_de : cpu.core.r16_hl;
  wire [15:0] architectural_hl = cpu.core.xchg_dh
      ? cpu.core.r16_hl : cpu.core.r16_de;
  wire [7:0] architectural_flags = {
      cpu.core.psw_s, cpu.core.psw_z, 1'b0, cpu.core.psw_ac,
      1'b0, cpu.core.psw_p, 1'b1, cpu.core.psw_c
  };

  function [7:0] baseline(input [15:0] address); begin
    baseline = ((address * 16'd37) + 16'h005a) & 8'hff;
  end endfunction

  task pulse(input phase1, input phase2); begin
    f1 = phase1; f2 = phase2; clk = 1'b0; #1;
    clk = 1'b1; #1;
  end endtask

  task phase_cycle; begin
    pulse(1'b1, 1'b0);
    if (!active || !done) pulse(1'b0, 1'b1);
    f1 = 1'b0; f2 = 1'b0;
  end endtask

  task seed_clean_m1; begin
    // The package wrapper pipelines the external phase enables by one pin_clk
    // edge. Arrange for the first post-seed core edge to be F2, which consumes
    // the seeded EOM and starts T1 before a later F1 can clear it.
    cpu.f1_core = 1'b0;
    cpu.f2_core = 1'b1;
    cpu.core.r16_pc = PROGRAM;
    cpu.core.r16_sp = reg_sp[15:0];
    cpu.core.r16_bc = reg_bc[15:0];
    // vm80a's physical r16_de/r16_hl names are opposite the architectural
    // values while xchg_dh is clear.
    cpu.core.r16_de = reg_hl[15:0];
    cpu.core.r16_hl = reg_de[15:0];
    cpu.core.r16_wz = 16'h0000;
    cpu.core.acc = reg_a[7:0];
    cpu.core.psw_s = flags[4];
    cpu.core.psw_z = flags[3];
    cpu.core.psw_ac = flags[2];
    cpu.core.psw_p = flags[1];
    cpu.core.psw_c = flags[0];
    cpu.core.tmp_c = 1'b0;
    cpu.core.inte = reg_iff[0];
    cpu.core.inta = 1'b0;
    cpu.core.intr = 1'b0;
    cpu.core.minta = 1'b0;
    cpu.core.mstart = 1'b0;
    cpu.core.i = 8'h00;
    cpu.core.di = 8'h00;
    cpu.core.db = 8'h00;
    cpu.core.a = PROGRAM;
    cpu.core.abufena = 1'b1;
    cpu.core.db_ena = 1'b0;
    cpu.core.db_stb = 1'b0;
    cpu.core.dbin_pin = 1'b0;
    cpu.core.dbin_ext = 1'b0;
    cpu.core.wr_n = 1'b1;
    cpu.core.sync = 1'b0;
    cpu.core.reset = 1'b0;
    cpu.core.t404 = 1'b0;
    cpu.core.xchg_dh = 1'b0;
    cpu.core.xchg_tt = 1'b0;
    cpu.core.t953 = 1'b0;
    cpu.core.t976 = 1'b0;
    cpu.core.t980 = 1'b0;
    cpu.core.sy_stack = 1'b0;

    cpu.core.t1 = 1'b0; cpu.core.t2 = 1'b0; cpu.core.tw = 1'b0;
    cpu.core.t3 = 1'b0; cpu.core.t4 = 1'b0; cpu.core.t5 = 1'b0;
    cpu.core.t1f1 = 1'b0; cpu.core.t2f1 = 1'b0; cpu.core.twf1 = 1'b0;
    cpu.core.t3f1 = 1'b0; cpu.core.t4f1 = 1'b0; cpu.core.t5f1 = 1'b0;
    cpu.core.m1 = 1'b1; cpu.core.m2 = 1'b0; cpu.core.m3 = 1'b0;
    cpu.core.m4 = 1'b0; cpu.core.m5 = 1'b0;
    cpu.core.m1f1 = 1'b1; cpu.core.m2f1 = 1'b0; cpu.core.m3f1 = 1'b0;
    cpu.core.m4f1 = 1'b0; cpu.core.m5f1 = 1'b0;
    cpu.core.eom = 1'b1;
    cpu.core.t789 = 1'b0;
    cpu.core.t887 = 1'b0;
  end endtask

  always @(posedge clk) begin
    if (sync && !sync_q) status <= d;
    sync_q <= sync;
    if (active && sync && !sync_q && d[5]) begin
      if (fetch_count == 1) begin
        next_pc <= a_bus;
        stop_after_fetch <= 1'b1;
      end
      fetch_count <= fetch_count + 1;
    end
    if (active && !done && cpu.core.thalt) begin
      next_pc <= cpu.core.r16_pc;
      done <= 1'b1;
    end
  end

  // The second M1 identifies the post-instruction PC. Wait until that fetch's
  // DBIN has completed so late flag/register latches from the tested
  // instruction are settled; the fetched next opcode has not executed yet.
  always @(negedge dbin) if (active && stop_after_fetch) done <= 1'b1;

  always @(posedge dbin) begin
    if (status[6]) read_data <= a_bus[7:0] ^ 8'ha5;
    else read_data <= mem[a_bus];
  end
  assign d = dbin ? read_data : 8'hzz;

  always @(negedge wr_n) if (active) begin
    if (status[4]) begin
      $display("IOOUT %0d %02x %02x", vector_index, a_bus[7:0], d);
    end else begin
      mem[a_bus] = d;
      if (write_count < 4) written[write_count] = a_bus;
      write_count = write_count + 1;
      $display("WRITE %0d %04x %02x", vector_index, a_bus, d);
    end
  end

  initial begin
    for (i = 0; i < 65536; i = i + 1) mem[i] = baseline(i[15:0]);
    if (!$value$plusargs("vectors=%s", vector_path)) begin
      $display("I8080-VM80A-DIFF: missing +vectors=FILE");
      $finish;
    end
    fd = $fopen(vector_path, "r");
    if (!fd) begin
      $display("I8080-VM80A-DIFF: cannot open vector file");
      $finish;
    end
    while (!$feof(fd)) begin
      code = $fscanf(fd, " %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                    vector_index, opcode, flags, op1, op2, reg_a, reg_bc,
                    reg_de, reg_hl, reg_sp, reg_iff, mem_hl, stack_lo, stack_hi);
      if (code == 14) begin
        active = 1'b0;
        reset = 1'b1;
        repeat (4) phase_cycle();
        pulse(1'b0, 1'b0);
        pulse(1'b0, 1'b0);

        mem[PROGRAM] = opcode[7:0];
        mem[PROGRAM + 1] = op1[7:0];
        mem[PROGRAM + 2] = op2[7:0];
        mem[reg_hl[15:0]] = mem_hl[7:0];
        mem[reg_sp[15:0]] = stack_lo[7:0];
        mem[(reg_sp + 1) & 16'hffff] = stack_hi[7:0];
        write_count = 0;
        fetch_count = 0;
        done = 1'b0;
        stop_after_fetch = 1'b0;
        sync_q = 1'b0;
        status = 8'h00;
        seed_clean_m1();
        reset = 1'b0;
        active = 1'b1;

        cycles = 0;
        while (!done && cycles < 100) begin
          phase_cycle();
          cycles = cycles + 1;
        end
        active = 1'b0;
        if (!done) begin
          $display("I8080-VM80A-DIFF: timeout vector=%0d opcode=%02x flags=%02x sync=%b m=%b%b%b%b%b t=%b%b%b%b%b pc=%04x a=%04x reset=%b f=%b%b start=%b eom=%b t953=%b",
                   vector_index, opcode, flags, sync,
                   cpu.core.m1, cpu.core.m2, cpu.core.m3, cpu.core.m4, cpu.core.m5,
                   cpu.core.t1, cpu.core.t2, cpu.core.t3, cpu.core.t4, cpu.core.t5,
                   cpu.core.r16_pc, cpu.core.a, cpu.core.reset,
                   cpu.f1_core, cpu.f2_core, cpu.core.start, cpu.core.eom,
                   cpu.core.t953);
          $finish;
        end
        #0.1;
        $display("RESULT %0d %02x %02x %04x %04x %04x %04x %04x %02x %0d %0d",
                 vector_index, opcode[7:0], cpu.core.acc, cpu.core.r16_bc,
                 architectural_de, architectural_hl, cpu.core.r16_sp, next_pc,
                 architectural_flags, inte, cpu.core.thalt);

        mem[PROGRAM] = baseline(PROGRAM);
        mem[PROGRAM + 1] = baseline(PROGRAM + 1);
        mem[PROGRAM + 2] = baseline(PROGRAM + 2);
        mem[reg_hl[15:0]] = baseline(reg_hl[15:0]);
        mem[reg_sp[15:0]] = baseline(reg_sp[15:0]);
        mem[(reg_sp + 1) & 16'hffff] = baseline((reg_sp + 1) & 16'hffff);
        for (i = 0; i < write_count && i < 4; i = i + 1)
          mem[written[i]] = baseline(written[i]);
      end
    end
    $fclose(fd);
    $finish;
  end
endmodule

`default_nettype wire
