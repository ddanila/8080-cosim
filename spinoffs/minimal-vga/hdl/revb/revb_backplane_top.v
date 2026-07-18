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
    parameter VIDEO_TTL     = 0,   // 1 = chip-level TTL video card (B2), asserts /WAIT
    parameter USART_REAL    = 0    // 1 = real 8251 on the I/O card (bring-up twin)
) (
    input  wire clk,
    input  wire dot_clk,           // 25.175 MHz scanout clock (only used when VIDEO_TTL)
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

    // Video card may assert open-drain /WAIT (B2, VIDEO_TTL). Interrupt lines idle.
    wire video_wait_n;
    wire wait_n  = video_wait_n;
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
      if (VIDEO_PRESENT && VIDEO_TTL) begin : g_video_ttl
        // Chip-level TTL card (B2): scanout on dot_clk, asserts /WAIT on CPU framebuffer
        // accesses that collide with the active region (D2.5). Scanout outputs unused here
        // (the boot oracle checks the framebuffer dump; scanout is a separate gate).
        revb_video_card_ttl #(.vw_limit(vw_limit), .dump_file(dump_file)) U_VIDEO (
            .dot_clk(dot_clk), .clk(clk), .reset_n(reset_n), .A(A), .D_in(D),
            .mreq_n(mreq_n), .rd_n(rd_n), .wr_n(wr_n),
            .MODE0(MODE0), .MODE1(MODE1), .D_out(video_do), .D_oe(video_oe),
            .wait_od_n(video_wait_n),
            .hsync_n(), .vsync_n(), .active(), .pixel(), .frame_tick());
      end else if (VIDEO_PRESENT) begin : g_video
        revb_video_card #(.vw_limit(vw_limit), .dump_file(dump_file)) U_VIDEO (
            .clk(clk), .reset_n(reset_n), .A(A), .D_in(D),
            .mreq_n(mreq_n), .rd_n(rd_n), .wr_n(wr_n),
            .MODE0(MODE0), .MODE1(MODE1), .D_out(video_do), .D_oe(video_oe));
        assign video_wait_n = 1'b1;
      end else begin : g_novideo
        assign video_do = 8'h00;
        assign video_oe = 1'b0;
        assign video_wait_n = 1'b1;
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
        .rfsh_n(rfsh_n), .A(A), .conflict(bus_conflict));
endmodule
`default_nettype wire
