// Juku E5104 — structural top level.
// Each instance is a chip on the board; wires are board nets.
// This is the LVS target (compare instance/net connectivity vs the KiCad netlist).
// Derived from ../docs/hardware-map.md.
`default_nettype none

module juku_top (
    input  wire        clk,        // CPU clock (from 8224-equiv, board glue)
    input  wire        reset_n
);
    // ---- board buses / nets ----
    wire [15:0] A;                 // address bus  (CPU -> all)
    wire [7:0]  D;                 // data bus     (bidirectional, tri-state)
    wire        memr_n, memw_n;    // memory read/write strobes (from bus control)
    wire        ior_n,  iow_n;     // I/O read/write strobes
    wire        inta_n;            // interrupt acknowledge
    wire        intr;              // interrupt request (PIC -> CPU)

    // ---- chip selects ----
    wire        cs_pic_n, cs_ppi0_n, cs_sio0_n, cs_ppi1_n;
    wire        cs_pit0_n, cs_pit1_n, cs_pit2_n, cs_fdc_n;
    wire        rom_oe_n, ram_we_n, ram_oe_n;     // memory enables from mem_decode
    wire [1:0]  mem_mode;                          // from PPI0 Port C[1:0]
    wire        reset = ~reset_n;                  // active-high reset (one board inverter)

    // ---- CPU + bus control (8080 + 8228/8224-equiv glue) ----
    cpu_8080 U_CPU (
        .clk(clk), .reset_n(reset_n),
        .A(A), .D(D),
        .memr_n(memr_n), .memw_n(memw_n), .ior_n(ior_n), .iow_n(iow_n),
        .intr(intr), .inta_n(inta_n)
    );

    // ---- I/O port decode: A4:A2 -> chip group, A1:A0 -> register ----
    io_decode U_IODEC (
        .A(A[7:0]), .ior_n(ior_n), .iow_n(iow_n),
        .cs_pic_n(cs_pic_n), .cs_ppi0_n(cs_ppi0_n), .cs_sio0_n(cs_sio0_n),
        .cs_ppi1_n(cs_ppi1_n), .cs_pit0_n(cs_pit0_n), .cs_pit1_n(cs_pit1_n),
        .cs_pit2_n(cs_pit2_n), .cs_fdc_n(cs_fdc_n)
    );

    // ---- memory bank decode: 4-mode ROM/RAM overlay (PPI0 PortC[1:0]) ----
    mem_decode U_MEMDEC (
        .A(A), .memr_n(memr_n), .memw_n(memw_n), .mode(mem_mode),
        .rom_oe_n(rom_oe_n), .ram_oe_n(ram_oe_n), .ram_we_n(ram_we_n)
    );

    // ---- memory ----
    rom_16k   U_ROM  (.A(A[13:0]), .D(D), .oe_n(rom_oe_n));
    ram_64k   U_RAM  (.A(A), .D(D), .we_n(ram_we_n), .oe_n(ram_oe_n)); // = 20x dram_64kx1

    // ---- peripherals on the I/O bus ----
    ppi_8255  U_PPI0 (.A(A[1:0]), .D(D), .cs_n(cs_ppi0_n), .rd_n(ior_n), .wr_n(iow_n),
                      .reset(reset), .portc_lo(mem_mode));   // PortC[1:0] -> mem mode
    ppi_8255  U_PPI1 (.A(A[1:0]), .D(D), .cs_n(cs_ppi1_n), .rd_n(ior_n), .wr_n(iow_n),
                      .reset(reset), .portc_lo());
    pit_8253  U_PIT0 (.A(A[1:0]), .D(D), .cs_n(cs_pit0_n), .rd_n(ior_n), .wr_n(iow_n), .clk(clk));
    pit_8253  U_PIT1 (.A(A[1:0]), .D(D), .cs_n(cs_pit1_n), .rd_n(ior_n), .wr_n(iow_n), .clk(clk));
    pit_8253  U_PIT2 (.A(A[1:0]), .D(D), .cs_n(cs_pit2_n), .rd_n(ior_n), .wr_n(iow_n), .clk(clk));
    usart_8251 U_SIO0(.A(A[0]),   .D(D), .cs_n(cs_sio0_n), .rd_n(ior_n), .wr_n(iow_n), .clk(clk));
    fdc_1793  U_FDC  (.A(A[1:0]), .D(D), .cs_n(cs_fdc_n),  .rd_n(ior_n), .wr_n(iow_n), .clk(clk));
    pic_8259  U_PIC  (.A(A[0]),   .D(D), .cs_n(cs_pic_n),  .rd_n(ior_n), .wr_n(iow_n),
                      .intr(intr), .inta_n(inta_n));

endmodule
`default_nettype wire
