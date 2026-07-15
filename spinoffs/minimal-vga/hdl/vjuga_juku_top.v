// VJUGA Verilog twin (Phase 1): the real Juku ekta37 firmware on a Z80 (tv80),
// with RAM served by the REAL К565РУ5 model (dram_64kx1) reused verbatim from
// the recreation's hdl/devices.v. Boots roms/ekta37_z80.bin and dumps the
// framebuffer so sim/boot_check-style comparison against the cosim oracle can
// confirm it byte-for-byte.
//
// Reused from the 8080-cosim recreation:
//   * dram_64kx1  -- the К565РУ5 bit-slice (this is the "test DRAM" goal)
//   * roms/ekta37_z80.bin -- the Z80-patched Juku firmware
//   * the Juku memory map (modes 0..3 via 8255 Port C), faithful to cosim
//   * cosim as the reference oracle (comparison done in sim/vjuga_boot_check.sh)
//
// Deliberately simple per the VJUGA charter: single memory-decode + a compact
// RAS/CAS DRAM sequencer with CPU wait-states, no FDC, no interrupts (the ekta37
// banner draws without them, exactly as cosim runs it). The D6 РТ4 decode PROM
// is NOT yet in the path (that is Phase 2, blocked on the D6 polarity routing
// question); Phase 1 uses the explicit mode map + the real РУ5 RAM.
`default_nettype none
module vjuga_juku_top #(
    parameter rom_file  = "ekta37_z80.hex",
    parameter vw_limit  = 6000,
    parameter dump_file = "vjuga_v_vram.bin"
) (
    input  wire clk,
    input  wire reset_n
);
    // ---- CPU (tv80, Z80 mode) ----
    wire        m1_n, mreq_n, iorq_n, rd_n, wr_n, rfsh_n, halt_n, busak_n;
    wire [15:0] A;
    wire [7:0]  cpu_do;
    reg  [7:0]  cpu_di;
    reg         wait_n;

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

    // ---- real К565РУ5 RAM bank (8 bit-slices), driven by a compact sequencer ----
    reg  [7:0] dram_ma;
    reg        dram_ras_n = 1'b1, dram_cas_n = 1'b1, dram_we_n = 1'b1;
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
    // dram_64kx1 un-permutes the row byte internally (row_lin) to model the D48-D51
    // scramble, so the row it is FED must be pre-scrambled; this is the inverse
    // permutation (identical to hdl/sim/dram_unit_tb.v raw_row) so mem stays linear.
    function [7:0] raw_row(input [7:0] lin);
        raw_row = {lin[0], lin[7], lin[6], lin[4], lin[2], lin[3], lin[5], lin[1]};
    endfunction

    localparam S_IDLE=0, S_ROW=1, S_RAS=2, S_COL=3, S_CAS=4, S_DONE=5;
    reg [2:0]  st = S_IDLE;
    reg [7:0]  ram_rdata;
    reg        acc_write;
    reg [15:0] acc_addr;

    wire ram_access = (mreq_n == 1'b0) && (rd_n == 1'b0 || wr_n == 1'b0) && !overlay(A);

    always @(posedge clk) begin
        if (!reset_n) begin
            st <= S_IDLE; dram_ras_n <= 1'b1; dram_cas_n <= 1'b1; dram_we_n <= 1'b1;
            mode <= 2'b00; portc <= 8'h00;
        end else begin
            // Drive RAS/CAS/WE EXPLICITLY per state -- no blanket default. A default
            // "<= 1" followed by a per-state "<= 0" made iverilog emit a spurious RAS
            // transition that re-triggered dram_64kx1's row latch after dram_ma had
            // switched to the column (row captured the column). Explicit per-state
            // values give RAS/CAS one clean edge each. One signal changes per state,
            // mirroring the proven hdl/sim/dram_unit_tb.v drive ordering.
            case (st)
                S_IDLE: begin
                            dram_ras_n <= 1'b1; dram_cas_n <= 1'b1; dram_we_n <= 1'b1;
                            if (ram_access) begin
                                acc_addr  <= A; acc_write <= ~wr_n; ram_wdata <= cpu_do;
                                dram_ma   <= raw_row(A[15:8]);   // present row (pre-scrambled)
                                st <= S_ROW;
                            end
                        end
                S_ROW:  begin dram_ras_n <= 1'b0; dram_cas_n <= 1'b1; dram_we_n <= 1'b1;
                              st <= S_RAS; end                    // RAS falls (row on bus, stable)
                S_RAS:  begin dram_ras_n <= 1'b0; dram_cas_n <= 1'b1; dram_we_n <= ~acc_write;
                              dram_ma <= acc_addr[7:0];           // switch to column (row already latched)
                              st <= S_COL; end
                S_COL:  begin dram_ras_n <= 1'b0; dram_cas_n <= 1'b0; dram_we_n <= ~acc_write;
                              st <= S_CAS; end                    // CAS falls -> read/write strobe
                S_CAS:  begin dram_ras_n <= 1'b0; dram_cas_n <= 1'b0; dram_we_n <= ~acc_write;
                              ram_rdata <= rdo; st <= S_DONE; end
                S_DONE: begin dram_ras_n <= 1'b1; dram_cas_n <= 1'b1; dram_we_n <= 1'b1;
                              st <= S_IDLE; end
            endcase

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

    // Wait-state the CPU on a RAM access until the sequencer has the data.
    always @* begin
        if (ram_access && st != S_DONE) wait_n = 1'b0;
        else                            wait_n = 1'b1;
    end

    // CPU read bus: ROM overlay / empty cart / sequenced RAM / IO latch.
    always @* begin
        if (mreq_n == 1'b0 && rd_n == 1'b0) begin
            if (overlay(A)) cpu_di = is_cart ? 8'hFF : rom[rom_idx(A)];
            else            cpu_di = ram_rdata;
        end else if (iorq_n == 1'b0 && rd_n == 1'b0) begin
            cpu_di = out_last[A[7:0]];
        end else cpu_di = 8'hFF;
    end

    // ---- framebuffer dump via the РУ5 video port, then finish ----
    reg [15:0] va_r = 16'hD800;
    assign vid_addr = va_r;
    reg [31:0] vw = 0;
    reg        prev_wr_ram = 0;
    wire       ram_write_now = (st == S_COL) && acc_write && (acc_addr >= 16'hD800);
    always @(posedge clk) begin
        if (!reset_n) begin vw <= 0; prev_wr_ram <= 0; end
        else begin
            if (ram_write_now && !prev_wr_ram) vw <= vw + 1;
            prev_wr_ram <= ram_write_now;
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
        $display("VJUGA-V: framebuffer dumped after %0d video writes (mode=%0d)", vw_limit, mode);
        $finish;
    end
endmodule
`default_nettype wire
