`timescale 1ns/1ps

module prom_fallback_tb;
  reg [7:0] d6_expected [0:255];
  reg [7:0] d2_expected [0:255];
  reg [7:0] d8_expected [0:31];
  reg [7:0] a8;
  reg [4:0] a5;
  wire rom_n, ram_n, rev, roe_n;
  wire [7:0] d8_data;
  wire [3:0] d2_data;
  integer i;
  integer errors = 0;

  decode_prom U_D6(.a(a8), .v_en_n(1'b0), .rom_n(rom_n), .ram_n(ram_n), .rev(rev), .roe_n(roe_n));
  wait_prom_037 U_D2(.a(a8), .v1_n(1'b0), .v2_n(1'b0), .d(d2_data));
  re3_prom U_D8(.a(a5), .e_n(1'b0), .d(d8_data));

  initial begin
    $readmemh("ref/physical-proms/validated/d2_037.raw.hex", d2_expected);
    $readmemh("ref/physical-proms/validated/d6_038.raw.hex", d6_expected);
    $readmemh("ref/reconstructed-proms/d8_re3_rom_pager_reconstructed.hex", d8_expected);

    for (i = 0; i < 256; i = i + 1) begin
      a8 = i[7:0];
      #1;
      if ({4'b0000, roe_n, rev, ram_n, rom_n} !== d6_expected[i]) begin
        $display("PROM-FALLBACK: D6 mismatch row=%02x got=%02x expected=%02x",
                 i[7:0], {4'b0000, roe_n, rev, ram_n, rom_n}, d6_expected[i]);
        errors = errors + 1;
      end
      if ({4'b0000, d2_data} !== d2_expected[i]) begin
        $display("PROM-FALLBACK: D2 mismatch row=%02x got=%02x expected=%02x",
                 i[7:0], {4'b0000, d2_data}, d2_expected[i]);
        errors = errors + 1;
      end
    end

    for (i = 0; i < 32; i = i + 1) begin
      a5 = i[4:0];
      #1;
      if (d8_data !== d8_expected[i]) begin
        $display("PROM-FALLBACK: D8 mismatch row=%02x got=%02x expected=%02x",
                 i[7:0], d8_data, d8_expected[i]);
        errors = errors + 1;
      end
    end

    if (errors == 0) begin
      $display("PROM-FALLBACK: PASS");
      $finish;
    end
    $display("PROM-FALLBACK: FAIL errors=%0d", errors);
    $finish(1);
  end
endmodule
