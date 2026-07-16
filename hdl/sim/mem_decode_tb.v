`timescale 1ns/1ps

module mem_decode_tb;
  reg [15:0] address = 0;
  reg memr_n = 1;
  reg memw_n = 1;
  reg [1:0] mode = 0;
  wire rom_oe_n;
  wire ram_oe_n;
  wire ram_we_n;

  mem_decode dut(
      .A(address), .memr_n(memr_n), .memw_n(memw_n), .mode(mode),
      .rom_oe_n(rom_oe_n), .ram_oe_n(ram_oe_n), .ram_we_n(ram_we_n));

  task check_outputs;
    input expected_rom_oe_n;
    input expected_ram_oe_n;
    input expected_ram_we_n;
    begin
      #1;
      if (rom_oe_n !== expected_rom_oe_n ||
          ram_oe_n !== expected_ram_oe_n ||
          ram_we_n !== expected_ram_we_n) begin
        $display("[MEM-DECODE] FAIL mode=%0d A=%04h R/W=%b/%b got=%b/%b/%b expected=%b/%b/%b",
                 mode, address, memr_n, memw_n,
                 rom_oe_n, ram_oe_n, ram_we_n,
                 expected_rom_oe_n, expected_ram_oe_n, expected_ram_we_n);
        $fatal(1);
      end
    end
  endtask

  initial begin
    // Low ROM is the read source, but /MEMW still writes underlying page-zero RAM.
    mode = 0; address = 16'h00E4; memr_n = 0; memw_n = 1;
    check_outputs(0, 1, 1);
    memr_n = 1; memw_n = 0;
    check_outputs(1, 1, 0);

    // The high ROM window remains write-protected.
    mode = 1; address = 16'hD800; memr_n = 0; memw_n = 1;
    check_outputs(0, 1, 1);
    memr_n = 1; memw_n = 0;
    check_outputs(1, 1, 1);

    // Ordinary RAM remains the read source and receives writes normally.
    address = 16'h4000; memr_n = 0; memw_n = 1;
    check_outputs(1, 0, 1);
    memr_n = 1; memw_n = 0;
    check_outputs(1, 1, 0);
    memw_n = 1;
    check_outputs(1, 1, 1);

    $display("[MEM-DECODE] PASS low-ROM write-behind + protected high ROM");
    $finish;
  end
endmodule
