`timescale 1ns/1ps

// Focused diagnostic for the still-open physical-D6 runnable adoption path.
// It exercises the exact combinational chain which blocked checkpoint-resumed
// execution when the CPU called RAM at B37A in physical mode 000.
module d6_runtime_path_tb;
  reg [15:0] ba = 16'h0000;
  reg [2:0] pc = 3'b000; // {PC4,PC3,PC2}

  wand d6_join_n;
  wire d6_rev, d6_roe_n;
  wire ram_out_en;
  wire physical_d58_oe_n;

  wire functional_rom_n, functional_ram_n, functional_rev, functional_roe_n;
  wire functional_ram_out_en;
  wire functional_d58_oe_n;

  // juku_top's physical RT4 address order: A0..A7 =
  // BA15,BA14,BA13,BA12,BA11,PC2,PC3,PC4.
  wire [7:0] d6_a = {pc[2], pc[1], pc[0],
                     ba[11], ba[12], ba[13], ba[14], ba[15]};

  decode_prom U_D6_PHYSICAL (
      .a(d6_a), .v_en_n(1'b0),
      .rom_n(d6_join_n), .ram_n(d6_join_n),
      .rev(d6_rev), .roe_n(d6_roe_n));

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

  // The explicit runnable oracle is sampled only as a behavioral comparison.
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

  task check_low_rom;
    begin
      ba = 16'h0484;
      #1;
      if (d6_join_n !== 1'b0 || d6_roe_n !== 1'b1 ||
          physical_d58_oe_n !== 1'b1) begin
        $display("D6-RUNTIME-PATH: FAIL low-ROM physical tuple join=%b roe_n=%b d58_oe_n=%b",
                 d6_join_n, d6_roe_n, physical_d58_oe_n);
        errors = errors + 1;
      end
      if (functional_rom_n !== 1'b0 || functional_ram_n !== 1'b1) begin
        $display("D6-RUNTIME-PATH: FAIL low-ROM oracle tuple rom_n=%b ram_n=%b",
                 functional_rom_n, functional_ram_n);
        errors = errors + 1;
      end
      $display("D6-RUNTIME-LOW-ROM ba=%04h mode=%03b join_n=%b roe_n=%b d58_oe_n=%b",
               ba, pc, d6_join_n, d6_roe_n, physical_d58_oe_n);
    end
  endtask

  task check_ram_call;
    begin
      ba = 16'hB37A;
      #1;
      // Physical word 8 keeps the joined conductor low but leaves D6.9 high.
      // Through the currently traced D13/D37 polarity that releases D58, so
      // checkpoint RAM cannot drive DB at this address.
      if (d6_join_n !== 1'b0 || d6_rev !== 1'b0 || d6_roe_n !== 1'b1 ||
          ram_out_en !== 1'b0 || physical_d58_oe_n !== 1'b1) begin
        $display("D6-RUNTIME-PATH: FAIL B37A physical tuple join=%b rev=%b roe_n=%b ram_out_en=%b d58_oe_n=%b",
                 d6_join_n, d6_rev, d6_roe_n, ram_out_en, physical_d58_oe_n);
        errors = errors + 1;
      end
      if (functional_rom_n !== 1'b1 || functional_ram_n !== 1'b0 ||
          functional_roe_n !== 1'b0 || functional_d58_oe_n !== 1'b0) begin
        $display("D6-RUNTIME-PATH: FAIL B37A oracle tuple rom_n=%b ram_n=%b roe_n=%b d58_oe_n=%b",
                 functional_rom_n, functional_ram_n, functional_roe_n,
                 functional_d58_oe_n);
        errors = errors + 1;
      end
      $display("D6-RUNTIME-RAM ba=%04h mode=%03b join_n=%b rev=%b roe_n=%b ram_out_en=%b d58_oe_n=%b oracle_ram_n=%b oracle_d58_oe_n=%b",
               ba, pc, d6_join_n, d6_rev, d6_roe_n, ram_out_en,
               physical_d58_oe_n, functional_ram_n, functional_d58_oe_n);
    end
  endtask

  initial begin
    check_low_rom();
    check_ram_call();
    if (errors != 0) begin
      $display("D6-RUNTIME-PATH: FAIL (%0d errors)", errors);
      $fatal(1);
    end
    $display("D6-RUNTIME-PATH: BOUNDARY REPRODUCED (physical mode 000 blocks D58 at B37A)");
    $finish;
  end
endmodule
