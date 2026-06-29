// Juku processor module — structural top level (discrete-chip granularity).
// Mirrors the schematic (ref/schematics/, drawing DGSh5.109.006 E3): the CPU core
// is 8080 + 8224 clock + 8238 system controller + 8286 address buffers, producing
// the BUFFERED address bus (BA) / system data bus (DB) + strobes that the rest of
// the board hangs off. Each instance = a chip; wires = board nets. This is the LVS
// target. See docs/transcription/cpu-core.md.
`default_nettype none

module juku_top (
    input  wire clk,        // board oscillator feeding the 8224
    input  wire reset_n
);
    // ---- CPU-local buses (between 8080 and its buffers/controller) ----
    wire [15:0] A;          // CPU address out -> 8286 buffers
    wire [7:0]  D;          // CPU data/status (mux) <-> 8238
    wire        dbin, wr_n, sync, hlda, inte, wait_o;

    // ---- clock / reset domain (boundary to a DISCRETE subsystem) ----
    // The real board has NO 8224: clock = crystal Z1 + D59 (ЛН1) oscillator +
    // phase gates D33/D38/D36/D35 (Φ1/Φ2 via D35, STB via D38); RESET from D13,
    // READY from D30, STSTB(8238) from D13. Driven by that subsystem, not modeled here.
    wire        phi1, phi2, phi2ttl, ready, reset_sys, ststb_n;

    // ---- buffered board buses + control strobes (out of the CPU core) ----
    wire [15:0] BA;         // buffered address bus
    wire [7:0]  DB;         // buffered system data bus
    wire        memr_n, memw_n, iord_n, iowr_n, inta_n;
    wire        intr;
    wire        busen_n = 1'b0;       // bus always enabled
    wire        buf_oe_n = 1'b0, buf_t = 1'b1;   // 8286: enabled, CPU->bus

    // ---- chip selects + memory enables ----
    wire        cs_pic_n, cs_ppi0_n, cs_sio0_n, cs_ppi1_n;
    wire        cs_pit0_n, cs_pit1_n, cs_pit2_n, cs_fdc_n;
    wire        rom_sel_n, ram_sel_n, rev, roe_n, prom_en_n;
    wire [1:0]  mem_mode;

    // ============ CPU core (the discrete chips) ============
    cpu_8080  U_CPU (.phi1(phi1), .phi2(phi2), .ready(ready), .reset(reset_sys),
                     .hold(1'b0), .intr(intr), .A(A), .D(D),
                     .dbin(dbin), .wr_n(wr_n), .sync(sync), .hlda(hlda),
                     .inte(inte), .wait_o(wait_o));

    // (no 8224 instance — clock/reset/ready/ststb arrive from the discrete subsystem above)

    sysctl_8238 U_SYS (.D(D), .DB(DB), .dbin(dbin), .wr_n(wr_n), .hlda(hlda),
                       .ststb_n(ststb_n), .busen_n(busen_n),
                       .memr_n(memr_n), .memw_n(memw_n),
                       .iord_n(iord_n), .iowr_n(iowr_n), .inta_n(inta_n));

    buf_8286  U_BUFL (.Ain(A[7:0]),  .Aout(BA[7:0]),  .oe_n(buf_oe_n), .t(buf_t));
    buf_8286  U_BUFH (.Ain(A[15:8]), .Aout(BA[15:8]), .oe_n(buf_oe_n), .t(buf_t));

    // ============ decode glue (board 74xx/PROM) ============
    io_decode U_IODEC (.A(BA[7:0]), .ior_n(iord_n), .iow_n(iowr_n),
        .cs_pic_n(cs_pic_n), .cs_ppi0_n(cs_ppi0_n), .cs_sio0_n(cs_sio0_n),
        .cs_ppi1_n(cs_ppi1_n), .cs_pit0_n(cs_pit0_n), .cs_pit1_n(cs_pit1_n),
        .cs_pit2_n(cs_pit2_n), .cs_fdc_n(cs_fdc_n));

    // ============ memory map decode: D6 (К556РТ4 PROM) gated by D7 (ЛА3) ============
    la3_gate    U_D7     (.a(memr_n), .b(mem_mode[0]), .y(prom_en_n));   // mode/strobe -> PROM enable [assumed]
    decode_prom U_DECODE (.a(BA[15:8]), .v_en_n(prom_en_n),
                          .rom_n(rom_sel_n), .ram_n(ram_sel_n), .rev(rev), .roe_n(roe_n));

    // ============ memory chips on the buffered buses ============
    // EPROM array D15..D22 (8x 8Kx8): addr BA[12:0], data DB, OE<-ROE, CS<-decode [CS detail TBD]
    eprom_8k U_D15 (.a(BA[12:0]), .d(DB), .cs_n(rom_sel_n), .oe_n(roe_n));
    eprom_8k U_D16 (.a(BA[12:0]), .d(DB), .cs_n(rom_sel_n), .oe_n(roe_n));
    eprom_8k U_D17 (.a(BA[12:0]), .d(DB), .cs_n(rom_sel_n), .oe_n(roe_n));
    eprom_8k U_D18 (.a(BA[12:0]), .d(DB), .cs_n(rom_sel_n), .oe_n(roe_n));
    eprom_8k U_D19 (.a(BA[12:0]), .d(DB), .cs_n(rom_sel_n), .oe_n(roe_n));
    eprom_8k U_D20 (.a(BA[12:0]), .d(DB), .cs_n(rom_sel_n), .oe_n(roe_n));
    eprom_8k U_D21 (.a(BA[12:0]), .d(DB), .cs_n(rom_sel_n), .oe_n(roe_n));
    eprom_8k U_D22 (.a(BA[12:0]), .d(DB), .cs_n(rom_sel_n), .oe_n(roe_n));

    // DRAM: К565РУ5 64Kx1 array, one byte-bank bit-sliced D60..D67 (8 of the 20 chips;
    // 2nd bank + video plane TODO). Address is MULTIPLEXED (MA) by the address-mux
    // subsystem (boundary); RAS/CAS from RAM control (boundary).
    wire [7:0] MA;                 // muxed row/col address  (from address mux)
    wire ras_n, cas_n;             // (from RAM control / refresh)
    dram_64kx1 U_D60 (.ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[0]), .do_(DB[0]));
    dram_64kx1 U_D61 (.ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[1]), .do_(DB[1]));
    dram_64kx1 U_D62 (.ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[2]), .do_(DB[2]));
    dram_64kx1 U_D63 (.ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[3]), .do_(DB[3]));
    dram_64kx1 U_D64 (.ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[4]), .do_(DB[4]));
    dram_64kx1 U_D65 (.ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[5]), .do_(DB[5]));
    dram_64kx1 U_D66 (.ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[6]), .do_(DB[6]));
    dram_64kx1 U_D67 (.ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[7]), .do_(DB[7]));

    // ============ peripherals (on the buffered buses) ============
    ppi_8255  U_PPI0 (.A(BA[1:0]), .D(DB), .cs_n(cs_ppi0_n), .rd_n(iord_n), .wr_n(iowr_n),
                      .reset(reset_sys), .portc_lo(mem_mode));
    ppi_8255  U_PPI1 (.A(BA[1:0]), .D(DB), .cs_n(cs_ppi1_n), .rd_n(iord_n), .wr_n(iowr_n),
                      .reset(reset_sys), .portc_lo());
    pit_8253  U_PIT0 (.A(BA[1:0]), .D(DB), .cs_n(cs_pit0_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(phi2ttl));
    pit_8253  U_PIT1 (.A(BA[1:0]), .D(DB), .cs_n(cs_pit1_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(phi2ttl));
    pit_8253  U_PIT2 (.A(BA[1:0]), .D(DB), .cs_n(cs_pit2_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(phi2ttl));
    usart_8251 U_SIO0(.A(BA[0]),   .D(DB), .cs_n(cs_sio0_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(phi2ttl));
    fdc_1793  U_FDC  (.A(BA[1:0]), .D(DB), .cs_n(cs_fdc_n),  .rd_n(iord_n), .wr_n(iowr_n), .clk(phi2ttl));
    pic_8259  U_PIC  (.A(BA[0]),   .D(DB), .cs_n(cs_pic_n),  .rd_n(iord_n), .wr_n(iowr_n),
                      .intr(intr), .inta_n(inta_n));

endmodule
`default_nettype wire
