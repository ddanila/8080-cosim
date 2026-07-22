// VJUGA Verilog twin (Phases 1-2): the real Juku ekta37 firmware on a Z80 (tv80),
// with RAM served by the REAL К565РУ5 model (dram_64kx1) and the ROM/RAM decode
// routed through the REAL К556РТ4 (D6, decode_prom) and К155РЕ3 (D8, re3_prom)
// PROMs -- all reused verbatim from the recreation's hdl/devices.v. Boots
// roms/ekta37_z80.bin and dumps the framebuffer so sim/vjuga_boot_check.sh can
// confirm it byte-for-byte against the cosim oracle.
//
// Reused from the 8080-cosim recreation (this is the "test the scarce chips" goal):
//   * dram_64kx1  -- the К565РУ5 DRAM bit-slice (workbench goal 2)
//   * decode_prom -- the D6 К556РТ4 memory-map decode, .038 dump (goal 3)
//   * re3_prom    -- the D8 К155РЕ3 ROM-select pager, .039 dump (goal 3)
//   * roms/ekta37_z80.bin -- the Z80-patched Juku firmware
//   * cosim as the reference oracle
//
// Deliberately simple per the VJUGA charter: a compact RAS/CAS DRAM sequencer
// with CPU wait-states, no FDC, no interrupts (the ekta37 banner draws without
// them, exactly as cosim runs it). Booting exercises D6/D8/РУ5 in the functional
// path, so a bad socketed chip on the bench diverges the boot from cosim.
// Corrected reader-3 packing proves physical D6 D0/pin12 is active-low ROM_N.
`default_nettype none
module vjuga_juku_top #(
    parameter rom_file  = "ekta37_z80.hex",
    parameter vw_limit  = 6000,
    parameter dump_file = "vjuga_v_vram.bin",
    // Decode mode = the physical MODE_B jumper (J94) in simulation.
    //   0 = Mode B: the real D6 РТ4 (decode_prom) drives ROM/RAM (chip test).
    //   1 = Mode A: the U5 GAL's internal decode, РТ4 socket empty (western
    //       baseline). Both are proven byte-identical to cosim.
    parameter DECODE_MODE = 0
) (
    input  wire clk,
    input  wire reset_n
);
    // ---- CPU (tv80, Z80 mode) ----
    wire        m1_n, mreq_n, iorq_n, rd_n, wr_n, rfsh_n, halt_n, busak_n;
    wire [15:0] A;
    wire [7:0]  cpu_do;
    reg  [7:0]  cpu_di;
    wire        wait_n;

    tv80s #(.Mode(0), .T2Write(0), .IOWait(1)) U_CPU (
        .reset_n(reset_n), .clk(clk), .wait_n(wait_n),
        .int_n(1'b1), .nmi_n(1'b1), .busrq_n(1'b1),
        .m1_n(m1_n), .mreq_n(mreq_n), .iorq_n(iorq_n), .rd_n(rd_n), .wr_n(wr_n),
        .rfsh_n(rfsh_n), .halt_n(halt_n), .busak_n(busak_n),
        .A(A), .di(cpu_di), .dout(cpu_do));

    // ---- ROM (the Z80-patched firmware) ----
    reg [7:0] rom [0:16383];
    initial $readmemh(rom_file, rom);

    // ---- memory map (cosim overlay: modes via Port C bits 1:0) ----
    reg [1:0]  mode = 2'b00;
    reg [7:0]  portc = 8'h00;
    reg [7:0]  out_last [0:255];
    integer    ii;
    initial for (ii = 0; ii < 256; ii = ii + 1) out_last[ii] = 8'h00;

    // overlay(a): 1 = served by ROM overlay (return idx), 0 = RAM
    function overlay(input [15:0] a);
        case (mode)
            2'b00: overlay = (a <= 16'h3FFF);
            2'b01: overlay = (a >= 16'hD800);
            2'b10: overlay = (a >= 16'h4000 && a <= 16'hBFFF) || (a >= 16'hD800);
            default: overlay = 1'b0;   // mode 3: all RAM
        endcase
    endfunction
    function [13:0] rom_idx(input [15:0] a);
        rom_idx = (mode == 2'b00) ? a[13:0] : (14'h1800 + (a - 16'hD800));
    endfunction
    wire is_cart = (mode == 2'b10) && (A >= 16'h4000 && A <= 16'hBFFF);

    // ---- Phase 2: route the ROM/RAM decision through the real Juku PROMs so
    // booting self-tests them. D6 (К556РТ4 decode_prom) decides ROM vs RAM;
    // D8 (К155РЕ3 re3_prom) is the ROM-select pager. Both reused verbatim from
    // hdl/devices.v with the validated .038/.039 dumps. D6 inputs mirror the Juku
    // (A6=/PC1, A5=/PC0, A7=0); corrected reader-3 packing preserves D0 as
    // active-low ROM_N. If either chip misbehaves on the bench,
    // the boot diverges from cosim -- that is the chip test.
    tri1 d6_rom_n, d6_ram_n, d6_rev, d6_roe;
    decode_prom U_D6 (.a({1'b0, ~portc[1], ~portc[0], A[11], A[12], A[13], A[14], A[15]}),
                      .v_en_n(1'b0),
                      .rom_n(d6_rom_n), .ram_n(d6_ram_n), .rev(d6_rev), .roe_n(d6_roe));
    // Mode B (J94 = B): the D6 РТ4 active-low D0/ROM_N decides ROM vs RAM.
    // Mode A (J94 = A): the coarse decode
    // the U5 GAL derives from A15/A14 alone (ROM = low 32K), needing neither the
    // РТ4 nor the Port C mode bits -- the western-parts bring-up baseline.
    wire is_rom_promB = ~d6_rom_n;           // physical D0/ROM_N low selects D8 and the ROM window
    wire is_rom_intA  = (A[15:14] == 2'b00);
    wire is_rom    = (DECODE_MODE == 1) ? is_rom_intA : is_rom_promB;
    wire rom_sel_n = ~is_rom;                // ROM select drives D8 /CE in both modes
    tri1 [7:0] d8_d;
    re3_prom U_D8 (.a(A[15:11]), .e_n(rom_sel_n), .d(d8_d));   // D8 РЕ3 ROM-select pager
    // Cross-check: D6's decision must match the reference mode map (flags a bad chip loudly).
    always @(posedge clk) if (reset_n && mreq_n == 1'b0 && (rd_n == 1'b0 || wr_n == 1'b0) && mode != 2'b10)
        if (is_rom !== overlay(A))
            $display("VJUGA-V: D6 decode MISMATCH @%04h mode=%0d D6=%b expected=%b", A, mode, is_rom, overlay(A));

    // ---- real К565РУ5 RAM bank (8 bit-slices), driven by a compact sequencer ----
    reg  [7:0] dram_ma;
    wire       dram_ras_n, dram_cas_n, dram_we_n;
    wire [7:0] rdo;                 // РУ5 data-out bus (open-collector-ish; model drives 0/1/z)
    reg  [7:0] ram_wdata;
    wire [15:0] vid_addr;           // video read address (sim-only 2nd port)
    wire [7:0]  vbyte;

    genvar b;
    generate for (b = 0; b < 8; b = b + 1) begin : ru5
        dram_64kx1 U_RU5 (.ma(dram_ma), .ras_n(dram_ras_n), .cas_n(dram_cas_n),
                          .we_n(dram_we_n), .di(ram_wdata[b]),
                          .nc_vbb_option(1'b0), .vcc_option(1'b1), .vss_gnd(1'b0),
                          .do_(rdo[b]), .va(vid_addr), .vq(vbyte[b]));
    end endgenerate

    // DRAM access sequencer + CPU wait-state handshake.
    // dram_64kx1 normalizes both the physical KP14 output inversion and the
    // D48-D51 row-bit permutation internally. This compact twin drives the RU5
    // pins directly, so pre-apply both effects here and keep mem[] CPU-linear.
    function [7:0] raw_row(input [7:0] lin);
        raw_row = ~{lin[0], lin[7], lin[6], lin[4], lin[2], lin[3], lin[5], lin[1]};
    endfunction

    localparam [2:0] S_IDLE=3'b000, S_ROW=3'b001, S_RAS=3'b011,
        S_COL=3'b010, S_CAS=3'b110, S_HOLD=3'b111,
        S_PRECHARGE=3'b101, S_DONE=3'b100;
    reg [7:0]  ram_rdata;
    reg        acc_write;
    reg [15:0] acc_addr;

    wire ram_access = (mreq_n == 1'b0) && (rd_n == 1'b0 || wr_n == 1'b0) && !(is_rom || is_cart);
    wire ram_ce_n_cpu = ~((mreq_n == 1'b0) && !(is_rom || is_cart));
    wire mem_rd_n_cpu = ~((mreq_n == 1'b0) && (rd_n == 1'b0));
    wire mem_wr_n_cpu = ~((mreq_n == 1'b0) && (wr_n == 1'b0));
    wire addrmux_sel_u24, video_ack_u24, refresh_tick_u24;
    wire u24_s0, u24_s1, u24_s2;
    wire [2:0] u24_state = {u24_s2, u24_s1, u24_s0};
    // tv80 presents its memory strobes for only one internal phase even when
    // WAIT is asserted. Hold the transaction captured above across U24's
    // remaining phases, matching the stable external bus contract of the
    // physical Z80 without bypassing any U24-generated DRAM control.
    wire u24_cpu_hold = u24_state != S_IDLE && u24_state != S_DONE &&
        !video_ack_u24 && !refresh_tick_u24;
    wire ram_ce_n_u24 = u24_cpu_hold ? 1'b0 : ram_ce_n_cpu;
    wire mem_rd_n_u24 = u24_cpu_hold ? acc_write : mem_rd_n_cpu;
    wire mem_wr_n_u24 = u24_cpu_hold ? ~acc_write : mem_wr_n_cpu;

    // The physical U24 GAL contract now drives the functional boot path. Its
    // corrected pinout uses pin 13 as an input and pins 14-23 as exactly ten
    // macrocells (seven functional outputs plus three Gray-state feedback bits).
    u24_dram_timing U_U24 (
        .clk(clk), .reset_n(reset_n), .ram_ce_n(ram_ce_n_u24),
        .mem_rd_n(mem_rd_n_u24), .mem_wr_n(mem_wr_n_u24),
        .rfsh_obs_n(rfsh_n), .video_req(1'b0), .decode_wait_n(1'b1),
        .refresh_q0(A[0]), .refresh_q1(A[1]),
        .refresh_q2(A[2]), .refresh_q3(A[3]),
        .ras_n(dram_ras_n), .cas_n(dram_cas_n), .dram_we_n(dram_we_n),
        .addrmux_sel(addrmux_sel_u24), .cpu_wait_n(wait_n),
        .video_ack(video_ack_u24), .refresh_tick(refresh_tick_u24),
        .state0(u24_s0), .state1(u24_s1), .state2(u24_s2)
    );

    always @(posedge clk) begin
        if (!reset_n) begin
            mode <= 2'b00; portc <= 8'h00;
        end else begin
            if (u24_state == S_IDLE && ram_access) begin
                acc_addr <= A;
                acc_write <= ~wr_n;
                ram_wdata <= cpu_do;
                dram_ma <= raw_row(A[15:8]);
            end
            // U24 enters COL after this edge; switch the external mux only
            // after RAS has latched the row.
            if (u24_state == S_RAS && !refresh_tick_u24)
                dram_ma <= ~acc_addr[7:0];
            // Sample while CAS is still low, immediately before PRECHARGE.
            if (u24_state == S_HOLD && !acc_write)
                ram_rdata <= rdo;

            // IO writes: latch + Port C bank control (once, on the WR strobe)
            if (iorq_n == 1'b0 && wr_n == 1'b0) begin
                out_last[A[7:0]] <= cpu_do;
                if (A[7:0] == 8'h06) begin portc <= cpu_do; mode <= cpu_do[1:0]; end
                else if (A[7:0] == 8'h07) begin
                    if (cpu_do[7]) begin portc <= 8'h00; mode <= 2'b00; end
                    else begin
                        portc[cpu_do[3:1]] <= cpu_do[0];
                        if (cpu_do[3:1] == 3'd0) mode[0] <= cpu_do[0];
                        if (cpu_do[3:1] == 3'd1) mode[1] <= cpu_do[0];
                    end
                end
            end
        end
    end

    // CPU read bus: ROM overlay / empty cart / sequenced RAM / IO latch.
    always @* begin
        if (mreq_n == 1'b0 && rd_n == 1'b0) begin
            if (is_rom || is_cart) cpu_di = is_cart ? 8'hFF : rom[rom_idx(A)];
            else            cpu_di = ram_rdata;
        end else if (iorq_n == 1'b0 && rd_n == 1'b0) begin
            cpu_di = out_last[A[7:0]];
        end else cpu_di = 8'hFF;
    end

    // ---- Phase 4 bench-observability emitters (opt-in via plusargs) ----
    // +capture=<file> logs every framebuffer write as "addr data" (hex), the
    //   exact stream tools/vjuga_fb_readback/reassemble.py replays -- so the
    //   readback tool is validated against this twin before any hardware exists.
    // +trace=<file> logs the first M1 opcode fetches in the same format the UNO
    //   single-step sketch prints, so a bench session diffs against this twin.
    integer capf = 0, trcf = 0, trc_count = 0;
    reg [1023:0] capname, trcname;
    reg m1_fetch_prev = 1'b0;
    initial begin
        if ($value$plusargs("capture=%s", capname)) capf = $fopen(capname, "w");
        if ($value$plusargs("trace=%s", trcname))   trcf = $fopen(trcname, "w");
    end

    // ---- framebuffer dump via the РУ5 video port, then finish ----
    reg [15:0] va_r = 16'hD800;
    assign vid_addr = va_r;
    reg [31:0] vw = 0;
    reg        prev_wr_ram = 0;
    wire       ram_write_now = (u24_state == S_CAS) && acc_write && (acc_addr >= 16'hD800);
    wire       m1_fetch_now  = (m1_n == 1'b0) && (mreq_n == 1'b0) && (rd_n == 1'b0);
    always @(posedge clk) begin
        if (!reset_n) begin vw <= 0; prev_wr_ram <= 0; m1_fetch_prev <= 1'b0; end
        else begin
            if (ram_write_now && !prev_wr_ram) begin
                vw <= vw + 1;
                if (capf != 0) $fwrite(capf, "%04h %02h\n", acc_addr, ram_wdata);
            end
            prev_wr_ram <= ram_write_now;
            if (trcf != 0 && m1_fetch_now && !m1_fetch_prev && trc_count < 256) begin
                $fwrite(trcf, "F%0d: addr=%04h data=%02h m1=%b mreq=%b rd=%b\n",
                        trc_count, A, cpu_di, m1_n, mreq_n, rd_n);
                trc_count <= trc_count + 1;
            end
            m1_fetch_prev <= m1_fetch_now;
        end
    end

    // Dump the 40x241 framebuffer at 0xD800. Read the 8 РУ5 bit-slices' mem
    // arrays by hierarchical reference rather than the video port: iverilog does
    // not re-evaluate the `assign vq = mem[va]` continuous read when only the
    // index changes, so a scan through the video port returns stale data.
    integer fo, i;
    reg [7:0] fb_byte;
    reg dumped = 0;
    always @(posedge clk) if (reset_n && vw_limit > 0 && vw == vw_limit && !dumped) begin
        dumped <= 1;
        fo = $fopen(dump_file, "wb");
        for (i = 0; i < 40*241; i = i + 1) begin
            fb_byte = {ru5[7].U_RU5.mem[16'hD800+i[15:0]], ru5[6].U_RU5.mem[16'hD800+i[15:0]],
                       ru5[5].U_RU5.mem[16'hD800+i[15:0]], ru5[4].U_RU5.mem[16'hD800+i[15:0]],
                       ru5[3].U_RU5.mem[16'hD800+i[15:0]], ru5[2].U_RU5.mem[16'hD800+i[15:0]],
                       ru5[1].U_RU5.mem[16'hD800+i[15:0]], ru5[0].U_RU5.mem[16'hD800+i[15:0]]};
            $fwrite(fo, "%c", fb_byte);
        end
        $fclose(fo);
        if (capf != 0) $fclose(capf);
        if (trcf != 0) $fclose(trcf);
        $display("VJUGA-V: framebuffer dumped after %0d video writes (mode=%0d)", vw_limit, mode);
        $finish;
    end
endmodule
`default_nettype wire
