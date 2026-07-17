// VJUGA rev B — passive backplane (top-level wiring of the cards).
// Instantiates the CPU / Memory / Video / I/O cards and wires them per
// spinoffs/minimal-vga/docs/rev-b-bus-contract.md. The backplane itself is
// passive: it only carries the bus, resolves the shared data bus (open lines
// read 0xFF, one driver at a time), and defaults MODE0/1 (handled by the I/O
// card here). For B0 there is no /WAIT contention (Video card asserts none yet),
// so wait_n is tied high. Boots ekta37 and the Video card dumps the framebuffer
// for sim/revb_boot_check.sh to compare byte-for-byte against cosim.
`default_nettype none
module revb_backplane_top #(
    parameter rom_file      = "ekta37_z80.hex",
    parameter vw_limit      = 6000,
    parameter dump_file     = "revb_vram.bin",
    parameter DECODE_MODE   = 0,
    parameter VIDEO_PRESENT = 1,   // 0 = minimum tier (no Video card)
    parameter USART_REAL    = 0    // 1 = real 8251 on the I/O card (bring-up twin)
) (
    input  wire clk,
    input  wire reset_n
);
    // ---- bus ----
    wire [15:0] A;
    wire        m1_n, mreq_n, iorq_n, rd_n, wr_n, rfsh_n, halt_n, busak_n;
    wire        MODE0, MODE1;

    // Per-card data outputs + output-enables (open-drain bus modeled as a
    // priority mux resolving to 0xFF; one-hot(0) of the OEs is asserted in T0.6).
    wire [7:0] cpu_do, mem_do, video_do, io_do;
    wire       cpu_oe, mem_oe, video_oe, io_oe;

    wire [7:0] D = cpu_oe   ? cpu_do   :
                   mem_oe   ? mem_do   :
                   video_oe ? video_do :
                   io_oe    ? io_do    : 8'hFF;

    // B0: no wait-state source yet (SRAM is fast, Video /WAIT is B2). Interrupt
    // lines idle (no PIC populated in this tier).
    wire wait_n  = 1'b1;
    wire int_n   = 1'b1;
    wire nmi_n   = 1'b1;
    wire busrq_n = 1'b1;

    revb_cpu_card U_CPU (
        .clk(clk), .reset_n(reset_n), .wait_n(wait_n),
        .int_n(int_n), .nmi_n(nmi_n), .busrq_n(busrq_n),
        .D_in(D), .D_out(cpu_do), .D_oe(cpu_oe),
        .A(A), .m1_n(m1_n), .mreq_n(mreq_n), .iorq_n(iorq_n),
        .rd_n(rd_n), .wr_n(wr_n), .rfsh_n(rfsh_n), .halt_n(halt_n), .busak_n(busak_n));

    revb_mem_card #(.rom_file(rom_file), .DECODE_MODE(DECODE_MODE)) U_MEM (
        .clk(clk), .reset_n(reset_n), .A(A), .D_in(D),
        .mreq_n(mreq_n), .rd_n(rd_n), .wr_n(wr_n),
        .MODE0(MODE0), .MODE1(MODE1), .D_out(mem_do), .D_oe(mem_oe));

    generate
      if (VIDEO_PRESENT) begin : g_video
        revb_video_card #(.vw_limit(vw_limit), .dump_file(dump_file)) U_VIDEO (
            .clk(clk), .reset_n(reset_n), .A(A), .D_in(D),
            .mreq_n(mreq_n), .rd_n(rd_n), .wr_n(wr_n),
            .MODE0(MODE0), .MODE1(MODE1), .D_out(video_do), .D_oe(video_oe));
      end else begin : g_novideo
        assign video_do = 8'h00;
        assign video_oe = 1'b0;
      end
    endgenerate

    revb_io_card #(.USART_REAL(USART_REAL)) U_IO (
        .clk(clk), .reset_n(reset_n), .A(A), .D_in(D),
        .iorq_n(iorq_n), .rd_n(rd_n), .wr_n(wr_n),
        .D_out(io_do), .D_oe(io_oe), .MODE0(MODE0), .MODE1(MODE1));

    // Passive bus-conflict assertion (never two drivers on D0-D7).
    wire bus_conflict;
    revb_bus_monitor U_MON (
        .cpu_oe(cpu_oe), .mem_oe(mem_oe), .video_oe(video_oe), .io_oe(io_oe),
        .A(A), .conflict(bus_conflict));
endmodule
`default_nettype wire
