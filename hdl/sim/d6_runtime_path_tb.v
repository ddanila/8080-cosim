`timescale 1ns/1ps

// Focused diagnostic for the still-open physical-D6 runnable adoption path.
// It exercises the exact combinational chain which blocked checkpoint-resumed
// execution when the CPU called RAM at B37A. `pc` below is now only a raw
// A7..A5 table coordinate; measured board inputs are A6=/PC1, A5=/PC0, while
// owner continuity closes A7 as D7.8 IO_CYCLE_H. The runnable memory checks use
// A7=0 because neither raw /IORD nor /IOWR is asserted during memory cycles.
module d6_runtime_path_tb;
  reg [15:0] ba = 16'h0000;
  reg [2:0] pc = 3'b000; // raw {D6 A7,A6,A5}
  reg d6_v_en_n = 1'b0;

  tri1 d6_rom_n, d6_ram_n, d6_rev, d6_roe_n;
  wire d6_select_and_n = d6_rom_n & d6_ram_n; // diagnostic expression, not a copper join
  tri1 [7:0] d8_d;
  wire ram_out_en;
  wire physical_d58_oe_n;

  wire functional_rom_n, functional_ram_n, functional_rev, functional_roe_n;
  wire functional_ram_out_en;
  wire functional_d58_oe_n;

  // Physical RT4 address order: A0..A7 =
  // BA15,BA14,BA13,BA12,BA11,A5,A6,A7.
  wire [7:0] d6_a = {pc[2], pc[1], pc[0],
                     ba[11], ba[12], ba[13], ba[14], ba[15]};

  decode_prom U_D6_PHYSICAL (
      .a(d6_a), .v_en_n(d6_v_en_n),
      .rom_n(d6_rom_n), .ram_n(d6_ram_n),
      .rev(d6_rev), .roe_n(d6_roe_n));
  re3_prom U_D8_PHYSICAL (
      .a(ba[15:11]), .e_n(d6_rom_n), .d(d8_d));

  tl2_hex U_D13_PHYSICAL (
      .i1(d6_roe_n), .o2(ram_out_en),
      .i3(1'b1), .o4(), .i5(1'b1), .o6(),
      .i9(1'b1), .o8(), .i11(1'b1), .o10(),
      .i13(1'b1), .o12());
  la3_gate U_D37_PHYSICAL (
      .a(1'b1), .b(1'b1), .y(),
      .a2(1'b1), .b2(1'b1), .y2(),
      .a3(1'b1), .b3(ram_out_en), .y3(physical_d58_oe_n),
      .a4(1'b1), .b4(1'b1), .y4());

  // The retired runnable oracle is sampled only as a historical comparison.
  decode_prom_functional U_D6_ORACLE (
      .ba(ba[15:11]), .pc2(pc[0]),
      .rom_n(functional_rom_n), .ram_n(functional_ram_n),
      .rev(functional_rev), .roe_n(functional_roe_n));
  tl2_hex U_D13_ORACLE (
      .i1(functional_roe_n), .o2(functional_ram_out_en),
      .i3(1'b1), .o4(), .i5(1'b1), .o6(),
      .i9(1'b1), .o8(), .i11(1'b1), .o10(),
      .i13(1'b1), .o12());
  la3_gate U_D37_ORACLE (
      .a(1'b1), .b(1'b1), .y(),
      .a2(1'b1), .b2(1'b1), .y2(),
      .a3(1'b1), .b3(functional_ram_out_en), .y3(functional_d58_oe_n),
      .a4(1'b1), .b4(1'b1), .y4());

  integer errors = 0;
  integer mode;

  task check_low_rom;
    begin
      ba = 16'h0484;
      #1;
      if (d6_select_and_n !== 1'b0 || d6_roe_n !== 1'b1 ||
          physical_d58_oe_n !== 1'b1) begin
        $display("D6-RUNTIME-PATH: FAIL low-ROM physical tuple select_and=%b roe_n=%b d58_oe_n=%b",
                 d6_select_and_n, d6_roe_n, physical_d58_oe_n);
        errors = errors + 1;
      end
      $display("D6-RUNTIME-LOW-ROM ba=%04h mode=%03b select_and_n=%b roe_n=%b d58_oe_n=%b",
               ba, pc, d6_select_and_n, d6_roe_n, physical_d58_oe_n);
    end
  endtask

  task check_disabled_at_ram_call;
    begin
      ba = 16'hB37A;
      pc = 3'b000;
      d6_v_en_n = 1'b1;
      #1;
      if ({d6_roe_n, d6_rev, d6_ram_n, d6_rom_n} !== 4'hF ||
          d6_roe_n !== 1'b1 || ram_out_en !== 1'b0 ||
          physical_d58_oe_n !== 1'b1) begin
        $display("D6-RUNTIME-PATH: FAIL disabled B37A word=%h d6_9=%b d13_2=%b d58_9=%b",
                 {d6_roe_n, d6_rev, d6_ram_n, d6_rom_n},
                 d6_roe_n, ram_out_en, physical_d58_oe_n);
        errors = errors + 1;
      end
      $display("D6-RUNTIME-DISABLED ba=%04h word=%h d6_9=%b d13_2=%b d58_9=%b",
               ba, {d6_roe_n, d6_rev, d6_ram_n, d6_rom_n},
               d6_roe_n, ram_out_en, physical_d58_oe_n);
      d6_v_en_n = 1'b0;
    end
  endtask

  task check_address_qualifier;
    begin
      pc = 3'b011;
      d6_v_en_n = 1'b0;
      ba = 16'h0484;
      #1;
      if ({d6_roe_n, d6_rev, d6_ram_n, d6_rom_n} !== 4'h8 || d8_d !== 8'hEF) begin
        $display("D6-RUNTIME-PATH: FAIL qualifier low word=%h d8=%h",
                 {d6_roe_n, d6_rev, d6_ram_n, d6_rom_n}, d8_d);
        errors = errors + 1;
      end
      ba = 16'hB37A;
      #1;
      if ({d6_roe_n, d6_rev, d6_ram_n, d6_rom_n} !== 4'h1 || d8_d !== 8'hFF) begin
        $display("D6-RUNTIME-PATH: FAIL qualifier RAM word=%h d8=%h",
                 {d6_roe_n, d6_rev, d6_ram_n, d6_rom_n}, d8_d);
        errors = errors + 1;
      end
      $display("D6-RUNTIME-QUALIFIER mode=011 low_ba=0484 low_word=8 low_d8=ef ram_ba=b37a ram_word=1 ram_d8=ff");
    end
  endtask

  task check_all_modes_at_ram_call;
    reg [3:0] expected_word;
    begin
      ba = 16'hB37A;
      for (mode = 0; mode < 8; mode = mode + 1) begin
        pc = mode[2:0];
        #1;
        expected_word = (mode == 0 || mode == 2 || mode == 3) ? 4'h1 : 4'hF;
        if ({d6_roe_n, d6_rev, d6_ram_n, d6_rom_n} !== expected_word) begin
          $display("D6-RUNTIME-PATH: FAIL all-mode B37A mode=%03b word=%h ram_out_en=%b d58_oe_n=%b",
                   pc, {d6_roe_n, d6_rev, d6_ram_n, d6_rom_n},
                   ram_out_en, physical_d58_oe_n);
          errors = errors + 1;
        end
        $display("D6-RUNTIME-ALL-MODES ba=%04h mode=%03b word=%h d6_9=%b d13_2=%b d58_9=%b",
                 ba, pc, {d6_roe_n, d6_rev, d6_ram_n, d6_rom_n},
                 d6_roe_n, ram_out_en, physical_d58_oe_n);
      end
    end
  endtask

  task check_ram_call;
    begin
      ba = 16'hB37A;
      #1;
      // Corrected physical word 1 releases ROM, sinks RAM and ROE, and enables
      // D58 through the traced D13/D37 path at the measured mode suffix 011.
      if (d6_select_and_n !== 1'b0 || d6_rev !== 1'b0 || d6_roe_n !== 1'b0 ||
          ram_out_en !== 1'b1 || physical_d58_oe_n !== 1'b0) begin
        $display("D6-RUNTIME-PATH: FAIL B37A physical tuple select_and=%b rev=%b roe_n=%b ram_out_en=%b d58_oe_n=%b",
                 d6_select_and_n, d6_rev, d6_roe_n, ram_out_en, physical_d58_oe_n);
        errors = errors + 1;
      end
      if (functional_rom_n !== 1'b1 || functional_ram_n !== 1'b0 ||
          functional_roe_n !== 1'b0 || functional_d58_oe_n !== 1'b0) begin
        $display("D6-RUNTIME-PATH: FAIL B37A oracle tuple rom_n=%b ram_n=%b roe_n=%b d58_oe_n=%b",
                 functional_rom_n, functional_ram_n, functional_roe_n,
                 functional_d58_oe_n);
        errors = errors + 1;
      end
      $display("D6-RUNTIME-RAM ba=%04h mode=%03b select_and_n=%b rev=%b roe_n=%b ram_out_en=%b d58_oe_n=%b oracle_ram_n=%b oracle_d58_oe_n=%b",
               ba, pc, d6_select_and_n, d6_rev, d6_roe_n, ram_out_en,
               physical_d58_oe_n, functional_ram_n, functional_d58_oe_n);
    end
  endtask

  initial begin
    pc = 3'b011;
    check_low_rom();
    check_ram_call();
    check_all_modes_at_ram_call();
    check_disabled_at_ram_call();
    check_address_qualifier();
    if (errors != 0) begin
      $display("D6-RUNTIME-PATH: FAIL (%0d errors)", errors);
      $fatal(1);
    end
    $display("D6-RUNTIME-PATH: CORRECTED TABLE MATCHES MEASURED MODE PATH");
    $finish;
  end
endmodule
