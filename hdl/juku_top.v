// Juku processor module — structural top level (discrete-chip granularity).
// Mirrors the schematic (ref/schematics/, drawing DGSh5.109.006 E3): the CPU core
// is 8080 + 8224 clock + 8238 system controller + 8286 address buffers, producing
// the BUFFERED address bus (BA) / system data bus (DB) + strobes that the rest of
// the board hangs off. Each instance = a chip; wires = board nets. This is the LVS
// target. See docs/transcription/cpu-core.md.
`default_nettype none

module juku_top (
    input  wire clk,        // board oscillator (crystal Z1 -> D59), feeds the clock subsystem
    input  wire reset_n,
    input  wire osc,        // SIM-ONLY: vm80a die-replica sampling clock (not a real КР580ВМ80А
                            // pin). Wired only to U_CPU below, so the LVS (>=2-endpoint nets) drops it.
    // SIM-ONLY keyboard stimulus (opt-in via kbd_en). Wired only to U_PPI0 below, so -- like
    // osc -- the LVS drops these 1-endpoint nets. A typed key = (kbd_kcol,kbd_kbit,kbd_shift).
    input  wire kbd_en, kbd_pressed, kbd_shift,
    input  wire [3:0] kbd_kcol,
    input  wire [2:0] kbd_kbit,
    input  wire frame_tick,     // SIM-ONLY: 8253 VER-RTR -> 8259 IR5 frame interrupt (a boundary).
                                // Drives the U_INTR adjunct (unmapped -> LVS-invisible).
    input  wire dotclk,         // SIM-ONLY video dot clock (real: D56 АГ3 16MHz -> D103 ИЕ10). Drives
                                // the video-output stage below (unmapped chips -> LVS-invisible).
    output wire vid_out         // composite video out (pixel stream from the framebuffer)
);
    // ---- CPU-local buses (between 8080 and its buffers/controller) ----
    wire [15:0] A;          // CPU address out -> 8286 buffers
    // CPU data/status (mux) <-> 8238. tri1 (pull-up like the real open bus) so the idle
    // bus floats to 0xFF, not z/x -- z/x poisons the die-accurate vm80a's internal capture.
    // yosys's frontend has no tri1; it only needs connectivity, so it reads a plain wire.
`ifdef YOSYS
    wire [7:0]  D;
`else
    tri1 [7:0]  D;
`endif
    wire        dbin, wr_n, sync, hlda, inte, wait_o;

    // ---- clock / reset domain (boundary to a DISCRETE subsystem) ----
    // The real board has NO 8224: clock = crystal Z1 + D59 (ЛН1) oscillator +
    // phase gates D33/D38/D36/D35 (Φ1/Φ2 via D35, STB via D38); RESET from D13,
    // READY from D30, STSTB(8238) from D13. Driven by that subsystem, not modeled here.
    wire        phi1, phi2, phi2ttl, ready, reset_sys, ststb_n;
    wire        sclk_i;   // shared sim sampling clock (CPU + DRAM + intr): external `osc`, or self-clocked

    // ---- buffered board buses + control strobes (out of the CPU core) ----
    wire [15:0] BA;         // buffered address bus
`ifdef YOSYS
    wire [7:0]  DB;         // buffered system data bus (see D above re: tri1 vs wire)
`else
    tri1 [7:0]  DB;
`endif
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
    cpu_8080  U_CPU (.sclk(sclk_i), .phi1(phi1), .phi2(phi2), .ready(ready), .reset(reset_sys),
                     .hold(1'b0), .intr(intr), .A(A), .D(D),
                     .dbin(dbin), .wr_n(wr_n), .sync(sync), .hlda(hlda),
                     .inte(inte), .wait_o(wait_o));

    // ---- discrete clock subsystem (faithful mesh; docs/transcription/clock-subsystem.md) ----
    // Z1 -> D59 (ЛН1 osc) -> OSC -> D40 (СТ16 divider) -> gate mesh D33(ЛН1)/D39(ЛА3)/D36(ЛА12)
    // -> D38 (ЛА1) = STB, and -> D35 (ЛН5) = Φ1/Φ2. D59/D40/D33/D39 are now FUNCTIONAL (not stubs)
    // and the divider->gate feedback nets D40.Q1->D39.12, D40.Q2->D33.5 are wired per the 2026-07
    // re-crop trace (see clock-mesh_tb for the running-divider proof). The boot-tb ties D59.xin=0 so
    // the divider is frozen at 0 -> d39_y=clkg_d33=1 -> ststb_n=~sync, i.e. boot stays byte-identical.
    wire osc_clk, clkg_d33, clkg_d36, d39_y, d33_o6; wire [3:0] d40_q;
    // sheet-2 LATCH/LOAD chain (D41 ИР16 -> D37 gate2 -> D33 inv; D38 gate2 -> D59 inv). Inputs of
    // D41/D38-2/D39-2 are deferred boundaries (numbered timing wires 1/2/4/15 + РЕ3 states).
    wire d41_qa, d41_qb, d37_latch_pre, latch_sig, d39_o8, load_pre;
    ir16      U_D41 (.a(1'b0), .b(1'b0), .c(1'b0), .d(1'b0), .ld(1'b1), .g(1'b1), .ck(1'b0),
                     .ds(1'b0), .qa(d41_qa), .qb(d41_qb));
    ln1_osc   U_D59 (.xin(clk), .osc(osc_clk), .i13(load_pre), .i11(d39_o8));
    ct16_ctr  U_D40 (.clk(osc_clk), .r_n(1'b1), .ep(1'b1), .et(1'b1), .pe_n(1'b1), .d(4'b0), .q(d40_q), .co());
    la3_gate  U_D39 (.a(d40_q[1]), .b(d40_q[0]), .y(d39_y), .a2(1'b1), .b2(1'b1), .y2(d39_o8));  // pin13(B)<-D40.Q0(14), pin12(A)<-D40.Q1(13) [traced]; sect2 9,10->8 -> D59.11 (sheet-2, ins deferred)
    wire d33_o4;
    ln1_dual  U_D33 (.i9(1'b0), .i5(d40_q[2]), .o8(clkg_d33), .o6(d33_o6), .i13(d37_latch_pre), .o12(latch_sig),
                     .i3(memr_n), .o4(d33_o4));  // + 13->12 = LATCH; 3->4 = ~MRD -> D37.5 (sheet-2)
    la12_gate U_D36 (.a(d40_q[1]), .b(d33_o6), .y(clkg_d36));  // pin5(A)<-D40.Q1(=D39.12), pin4(B)<-D33.6, pin6->D35.11 [traced]
    clk_phase U_D35 (.osc(clkg_d36), .phsel(d40_q[1]), .phi1(phi1), .phi2(phi2), .phi2ttl(phi2ttl));
    // vm80a sampling clock. Default = external `osc` (forced-clock boot tbs). With SELF_CLOCK the CPU
    // is driven entirely by the mesh: sclk = D40 divider LSB, phases = D35 from d40_q[1]. This exactly
    // reproduces the boot-tb's waveform (osc posedge mid-phase, one per phase) but self-generated.
`ifdef SELF_CLOCK
    assign sclk_i = d40_q[0];
`else
    assign sclk_i = osc;
`endif
    // D38 (ЛА1) is a clock-mesh gate producing a strobe (STB, pin 8) -- NOT the 8238 STSTB (that's D13,
    // per cpu-core.md). Re-homed: no SYNC input; output -> boundary stb_d38.
    wire stb_d38;
    la1_gate  U_D38 (.i0(clkg_d33), .i1(1'b1), .i2(1'b1), .i3(d39_y), .y(stb_d38),
                     .i4(1'b1), .i5(1'b1), .i6(1'b1), .i7(1'b1), .y2(load_pre));  // sect2 (5,4,2,1->6) = LOAD; ins <- timing wires 4/2/1/15 [boundary]
    // D13 (ТЛ2, Sheet-1) = the REAL 8238 status-strobe source (discrete, no 8224): section B STSTB =
    // ~sync -> ststb_n -> D5 STB(pin1); section A = RESIN Schmitt -> RES (boundary). Byte-identical
    // (same ~sync the D38 model produced) but now sourced from the faithful chip. [cpu-core.md]
    wire d13_res;
    tl2_dual  U_D13 (.i1(1'b1), .i2(1'b1), .i4(1'b1), .i5(1'b1), .o6(d13_res),
                     .i9(sync), .i10(1'b1), .i12(1'b1), .i13(1'b1), .o8(ststb_n));

    sysctl_8238 U_SYS (.D(D), .DB(DB), .dbin(dbin), .wr_n(wr_n), .hlda(hlda),
                       .ststb_n(ststb_n), .busen_n(busen_n),
                       .memr_n(memr_n), .memw_n(memw_n),
                       .iord_n(iord_n), .iowr_n(iowr_n), .inta_n(inta_n));

    buf_8286  U_BUFL (.Ain(A[7:0]),  .Aout(BA[7:0]),  .oe_n(buf_oe_n), .t(buf_t));
    buf_8286  U_BUFH (.Ain(A[15:8]), .Aout(BA[15:8]), .oe_n(buf_oe_n), .t(buf_t));

    // ============ expansion/backplane interface (Phase B, sheet 1 -- bus-interface.md) ============
    // D29 (ВА86) = the full bus-command transceiver, 8 signals (B0..B7 per owner's scan read):
    //   B0 -INHIB, B1 -CCLCK, B2 -IO/M, B3 -MWC, B4 -MRC, B5 -AMWC, B6 -IORC, B7 -IOWC.
    // A-side reads the internal strobes for the 4 known commands (memw->-MWC, memr->-MRC,
    // iord->-IORC, iowr->-IOWC); the other 4 sources (-INHIB/-CCLCK/-IO/M/-AMWC) aren't modelled
    // here -> tied inactive (boundary). One-way (never drives the strobe nets -> boot-safe).
    wire inhib_n, cclck, iom_n, mwc_n, mrc_n, amwc_n, iorc_n, iowc_n;
    va86_out U_D29 (.Ain ({iowr_n, iord_n, 1'b1,   memr_n, memw_n, 1'b1,  1'b1,    1'b1}),
                    .Aout({iowc_n, iorc_n, amwc_n, mrc_n,  mwc_n,  iom_n, cclck, inhib_n}),
                    .oe_n(1'b0), .t(1'b1));
    // Address/data backplane transceivers (ВА87, one-way A->B; refdes confirmed by owner from scan):
    //   D23 = addr LOW  (BA[7:0]  -> -ADR0..-ADR7)
    //   D24 = addr HIGH (BA[15:8] -> -ADR8..-ADRF)
    //   D25 = data      (DB       -> -DAT0..-DAT7)
    // A-side reads the buffered bus (never drives it -> boot-safe); B-side drives the connector.
    wire [7:0] adr_lo, adr_hi, dat;
    va87_out U_D23 (.Ain(BA[7:0]),  .Aout(adr_lo), .oe_n(1'b0), .t(1'b1));
    va87_out U_D24 (.Ain(BA[15:8]), .Aout(adr_hi), .oe_n(1'b0), .t(1'b1));
    va87_out U_D25 (.Ain(DB),       .Aout(dat),    .oe_n(1'b0), .t(1'b1));
    expansion_conn U_X1 (.inhib_n(inhib_n), .cclck(cclck), .iom_n(iom_n), .mwc_n(mwc_n),
                         .mrc_n(mrc_n), .amwc_n(amwc_n), .iorc_n(iorc_n), .iowc_n(iowc_n),
                         .dat(dat), .adr_lo(adr_lo), .adr_hi(adr_hi));

    // ============ I/O chip-select decode: К555ИД7 (74138) ============
    // A2:A0 select group, I/ORD & I/OWR enable; Y0..Y7 -> the chip-selects.
    // (refdes placeholder DID7; decode wiring is the standard 74138 pattern [assumed])
    wire [7:0] d8_d;
    re3_prom  U_D8   (.a(BA[15:11]), .e_n(1'b0), .d(d8_d));   // A4..A0 = BA15..BA11 -- DERIVED from firmware .117: the 4000-BFFF window pager (see docs/re3-decode.md)
    io_dec138 U_DID7 (.a(d8_d[0]), .b(d8_d[1]), .c(d8_d[2]),
                      .sa(BA[2]), .sb(BA[3]), .sc(BA[4]), .g1(1'b1), .g2a_n(iord_n), .g2b_n(iowr_n),
        .y_n({cs_fdc_n, cs_pit2_n, cs_pit1_n, cs_pit0_n, cs_ppi1_n, cs_sio0_n, cs_ppi0_n, cs_pic_n}));

    // ============ memory map decode: D6 (К556РТ4 PROM) gated by D7 (ЛА3) ============
    la3_gate    U_D7     (.a(1'b1), .b(mem_mode[0]), .y(prom_en_n));     // ЛА3 as inverter: prom_en_n = ~(Port-C mode bit) [assumed]
    decode_prom U_DECODE (.a(BA[15:8]), .v_en_n(prom_en_n),
                          .rom_n(rom_sel_n), .ram_n(ram_sel_n), .rev(rev), .roe_n(roe_n));

    // ============ memory chips on the buffered buses ============
    // EPROM: 8 ROM sockets on the board, only 2 POPULATED (M2764 8Kx8 = the 16KB BIOS).
    // Model the populated pair; the other 6 sockets are unpopulated (Phase-B PCB detail).
    eprom_8k #(.HALF(0)) U_D15 (.a(BA[12:0]), .d(DB), .cs_n(rom_sel_n), .oe_n(memr_n));  // low 8K
    eprom_8k #(.HALF(1)) U_D16 (.a(BA[12:0]), .d(DB), .cs_n(rev),       .oe_n(memr_n));  // high 8K (CE=rev)
    // D17-D22 = the 6 UNPOPULATED ROM sockets: wired to the shared address/data + OE, passive (no chip
    // -> boot-safe). Per-socket CS from the ROM bank decode (not traced -> tied deselected = gap).
    eprom_socket U_D17 (.a(BA[12:0]), .d(DB), .cs_n(1'b1), .oe_n(memr_n));
    eprom_socket U_D18 (.a(BA[12:0]), .d(DB), .cs_n(1'b1), .oe_n(memr_n));
    eprom_socket U_D19 (.a(BA[12:0]), .d(DB), .cs_n(1'b1), .oe_n(memr_n));
    eprom_socket U_D20 (.a(BA[12:0]), .d(DB), .cs_n(1'b1), .oe_n(memr_n));
    eprom_socket U_D21 (.a(BA[12:0]), .d(DB), .cs_n(1'b1), .oe_n(memr_n));
    eprom_socket U_D22 (.a(BA[12:0]), .d(DB), .cs_n(1'b1), .oe_n(memr_n));

    // DRAM: К565РУ5 64Kx1 array. 32 sockets on the board (4 banks x 8), only 8 POPULATED
    // = one byte-bank bit-sliced D60..D67 = the real 64KB RAM. The other 24 sockets are
    // bank-expansion (up to 256KB), unpopulated. There is NO separate video plane -- the
    // video reads this same bank via the КП14 µP/video mux. Address is MULTIPLEXED (MA);
    // RAS/CAS from the D53 ИД7 decoder + АГ3 timing (see docs/transcription/dram-video-timing.md).
    wire [7:0] MA;                 // muxed row/col address  (from address mux)
    wire ras_n, cas_n;             // (from RAM control / refresh)
    wire [15:0] vid_addr;          // video raster address into the framebuffer (РУ5 2nd port)
    wire [7:0]  vbyte;             // framebuffer byte at vid_addr (from the 8 РУ5 video reads)
    // D58 (К580ИР82) = DRAM write-data latch: latches DB and drives the РУ5 DIN bus (write_data),
    // holding write data stable across CAS/WE. Modeled transparent (write_data = DB) -> boot identical.
    // РУ5 DIN <- write_data (via D58); РУ5 DOUT stays on DB (read path). STB/OE = boundary for now.
    wire [7:0] write_data;
    ir82_latch U_D58 (.d(DB), .stb(1'b0), .oe_n(1'b0), .q(write_data));
    dram_64kx1 U_D60 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(write_data[0]), .do_(DB[0]), .va(vid_addr), .vq(vbyte[0]));
    dram_64kx1 U_D61 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(write_data[1]), .do_(DB[1]), .va(vid_addr), .vq(vbyte[1]));
    dram_64kx1 U_D62 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(write_data[2]), .do_(DB[2]), .va(vid_addr), .vq(vbyte[2]));
    dram_64kx1 U_D63 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(write_data[3]), .do_(DB[3]), .va(vid_addr), .vq(vbyte[3]));
    dram_64kx1 U_D64 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(write_data[4]), .do_(DB[4]), .va(vid_addr), .vq(vbyte[4]));
    dram_64kx1 U_D65 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(write_data[5]), .do_(DB[5]), .va(vid_addr), .vq(vbyte[5]));
    dram_64kx1 U_D66 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(write_data[6]), .do_(DB[6]), .va(vid_addr), .vq(vbyte[6]));
    dram_64kx1 U_D67 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(write_data[7]), .do_(DB[7]), .va(vid_addr), .vq(vbyte[7]));
    // ---- unpopulated DRAM banks 1-3 (D68-D91): sockets wired to the shared MA/RAS/WE + per-bit
    // DIN/DOUT buses, per-bank CAS. Passive (no chip installed) -> boot-safe. Bank-select CAS
    // decode not yet traced [assumed]. Completes the 4x8 РУ5 array for the PCB.
    wire cas1, cas2, cas3;
    ru5_socket U_D68 (.ma(MA), .ras_n(ras_n), .cas_n(cas1), .we_n(memw_n), .di(write_data[0]), .do_(DB[0]));
    ru5_socket U_D69 (.ma(MA), .ras_n(ras_n), .cas_n(cas1), .we_n(memw_n), .di(write_data[1]), .do_(DB[1]));
    ru5_socket U_D70 (.ma(MA), .ras_n(ras_n), .cas_n(cas1), .we_n(memw_n), .di(write_data[2]), .do_(DB[2]));
    ru5_socket U_D71 (.ma(MA), .ras_n(ras_n), .cas_n(cas1), .we_n(memw_n), .di(write_data[3]), .do_(DB[3]));
    ru5_socket U_D72 (.ma(MA), .ras_n(ras_n), .cas_n(cas1), .we_n(memw_n), .di(write_data[4]), .do_(DB[4]));
    ru5_socket U_D73 (.ma(MA), .ras_n(ras_n), .cas_n(cas1), .we_n(memw_n), .di(write_data[5]), .do_(DB[5]));
    ru5_socket U_D74 (.ma(MA), .ras_n(ras_n), .cas_n(cas1), .we_n(memw_n), .di(write_data[6]), .do_(DB[6]));
    ru5_socket U_D75 (.ma(MA), .ras_n(ras_n), .cas_n(cas1), .we_n(memw_n), .di(write_data[7]), .do_(DB[7]));
    ru5_socket U_D76 (.ma(MA), .ras_n(ras_n), .cas_n(cas2), .we_n(memw_n), .di(write_data[0]), .do_(DB[0]));
    ru5_socket U_D77 (.ma(MA), .ras_n(ras_n), .cas_n(cas2), .we_n(memw_n), .di(write_data[1]), .do_(DB[1]));
    ru5_socket U_D78 (.ma(MA), .ras_n(ras_n), .cas_n(cas2), .we_n(memw_n), .di(write_data[2]), .do_(DB[2]));
    ru5_socket U_D79 (.ma(MA), .ras_n(ras_n), .cas_n(cas2), .we_n(memw_n), .di(write_data[3]), .do_(DB[3]));
    ru5_socket U_D80 (.ma(MA), .ras_n(ras_n), .cas_n(cas2), .we_n(memw_n), .di(write_data[4]), .do_(DB[4]));
    ru5_socket U_D81 (.ma(MA), .ras_n(ras_n), .cas_n(cas2), .we_n(memw_n), .di(write_data[5]), .do_(DB[5]));
    ru5_socket U_D82 (.ma(MA), .ras_n(ras_n), .cas_n(cas2), .we_n(memw_n), .di(write_data[6]), .do_(DB[6]));
    ru5_socket U_D83 (.ma(MA), .ras_n(ras_n), .cas_n(cas2), .we_n(memw_n), .di(write_data[7]), .do_(DB[7]));
    ru5_socket U_D84 (.ma(MA), .ras_n(ras_n), .cas_n(cas3), .we_n(memw_n), .di(write_data[0]), .do_(DB[0]));
    ru5_socket U_D85 (.ma(MA), .ras_n(ras_n), .cas_n(cas3), .we_n(memw_n), .di(write_data[1]), .do_(DB[1]));
    ru5_socket U_D86 (.ma(MA), .ras_n(ras_n), .cas_n(cas3), .we_n(memw_n), .di(write_data[2]), .do_(DB[2]));
    ru5_socket U_D87 (.ma(MA), .ras_n(ras_n), .cas_n(cas3), .we_n(memw_n), .di(write_data[3]), .do_(DB[3]));
    ru5_socket U_D88 (.ma(MA), .ras_n(ras_n), .cas_n(cas3), .we_n(memw_n), .di(write_data[4]), .do_(DB[4]));
    ru5_socket U_D89 (.ma(MA), .ras_n(ras_n), .cas_n(cas3), .we_n(memw_n), .di(write_data[5]), .do_(DB[5]));
    ru5_socket U_D90 (.ma(MA), .ras_n(ras_n), .cas_n(cas3), .we_n(memw_n), .di(write_data[6]), .do_(DB[6]));
    ru5_socket U_D91 (.ma(MA), .ras_n(ras_n), .cas_n(cas3), .we_n(memw_n), .di(write_data[7]), .do_(DB[7]));

    // ---- video address counters + address mux + RAS/CAS decoder (drive РУ5 MA/RAS/CAS) ----
    // sel/en + counter preset are the assumed parts; chips D44-D50/D53 are scan-verified.
    wire [3:0] vctr_lo, vctr_hi; wire co0, co1, co2; wire [1:0] rc_nc;
    ie7_ctr  U_D44 (.clk(phi2ttl), .load_n(1'b1), .d(4'b0), .q(vctr_lo), .co(co0));
    ie7_ctr  U_D45 (.clk(co0),     .load_n(1'b1), .d(4'b0), .q(vctr_hi), .co(co1));
    ie7_ctr  U_D46 (.clk(co1),     .load_n(1'b1), .d(4'b0), .q(),        .co(co2));
    ie7_ctr  U_D47 (.clk(co2),     .load_n(1'b1), .d(4'b0), .q(),        .co());
    // DRAM address mux: sel=Φ1 puts the ROW (BA[15:8]) on MA during RAS, the COL (BA[7:0]) during
    // CAS. (CPU row/col realized; the video path through this mux is the un-modeled boundary.)
    kp14_mux U_D48 (.a(BA[3:0]), .b(BA[11:8]),  .sel(phi1), .en_n(1'b0), .y(MA[3:0]));
    kp14_mux U_D49 (.a(BA[7:4]), .b(BA[15:12]), .sel(phi1), .en_n(1'b0), .y(MA[7:4]));
    // RAS/CAS strobes: RAM-select (ram_sel_n) gated by Φ1 (RAS) / Φ2 (CAS). [assumed timing]
    wire mem_active = ~(memr_n & memw_n);   // a memory read or write is in progress
    // D53 per sheet-2: A/B from the D52 КП14 mux via the E2/E3 config jumpers (2-3 position ties
    // them to Φ1/Φ2 -- the traced/boot config), C grounded, G1 = RAM_SEL. mem_active stays as the
    // sim-only qualifier (SACTIVE).
    wire [3:0] d52_y; wire e2_com, e3_com;
    kp14_mux  U_D52 (.a(4'b0), .b(4'b0), .sel(1'b0), .en_n(1'b1), .y(d52_y));   // video/µP addr mux [ins deferred]
    jumper3   U_E2  (.p1(d52_y[0]), .p3(phi1), .p2(e2_com));
    jumper3   U_E3  (.p1(d52_y[1]), .p3(phi2), .p2(e3_com));
    rascas_dec U_D53 (.a(e2_com), .b(e3_com), .c(1'b0), .g(ram_sel_n), .sactive(mem_active),
                      .y_n({ras_n, cas_n, rc_nc}));

    // ---- video dot clock: АГ3 D56 (16 MHz RC one-shot) -> ИЕ10 D103 divider (-> 1.23 MHz) ----
    wire dotclk_16m;
    ag3_oneshot U_D56  (.a_n(1'b1), .b(1'b1), .clr_n(1'b1), .q(dotclk_16m), .q_n());
    ie10_ctr    U_D103 (.clk(dotclk_16m), .clr_n(1'b1), .load_n(1'b1), .d(4'b0), .q(), .co());

    // ---- video-output stage (arc V2): raster-scan the framebuffer -> ИР16 serialize -> ЛП5 combine
    // Reads the РУ5 framebuffer via its sim-only 2nd port (vid_addr -> vbyte) at the raster address,
    // serializes each byte at the dot clock through the ИР16, and drives the composite video the
    // display sees. Driven by the sim `dotclk`. The RUNNABLE demo uses the abstracted 8-bit ir16_sr
    // (U_IR16) -> lp5_xor (U_D34V); the REAL chips D42/D43 (ИР16) are instantiated below for the LVS
    // structure (traced sheet-2 top-right, docs/transcription/dram-video-timing.md). The 2x4-bit +
    // analog node-"A" byte->pixel scheme + the КП14 µP/video arbitration are the V3/boundary items.
    wire vpixel, vshl_n;
    video_raster U_VRAS (.dotclk(dotclk), .vid_addr(vid_addr), .shl_n(vshl_n));  // raster scan (unmapped)
    ir16_sr U_IR16 (.clk(dotclk), .clk_inh(1'b0), .shl_n(vshl_n), .clr_n(1'b1), .si(1'b0),
                    .d(vbyte), .so(vpixel));                            // abstracted serializer (runnable)
    lp5_xor U_D34V (.a(vpixel), .b(1'b0), .y(vid_out));                 // composite video out (runnable)
    // Real pixel serializers (LVS structure): D42 = high nibble, D43 = low nibble. Parallel data
    // reads the REAL system data bus DB (the bit-sliced РУ5 drives the byte there during a video
    // read); CK joins the dot-clock net; DS = GND; shared load VID_LD; Q -> node "A" (analog mix =
    // boundary). The video-read SLOT timing (КП14 µP/video arbitration + РЕ3/АГ3) stays a boundary.
    wire d42_q, d43_q;
    ir16 U_D42 (.d(DB[7]), .c(DB[6]), .b(DB[5]), .a(DB[4]),
                .ld(vshl_n), .g(1'b1), .ck(dotclk_16m), .ds(1'b0), .q(d42_q));
    ir16 U_D43 (.d(DB[3]), .c(DB[2]), .b(DB[1]), .a(DB[0]),
                .ld(vshl_n), .g(1'b1), .ck(dotclk_16m), .ds(1'b0), .q(d43_q));
    // D37 (ЛА3) inverts D42's serial output (pins 12,13 tied to D42.Q pin10) before the analog
    // node-"A" summing mix; its output (pin 11) enters that resistor mix (R38 1k) -> boundary.
    wire d37_out;
    la3_gate U_D37 (.a(d42_q), .b(d42_q), .y(d37_out), .a2(d41_qb), .b2(d40_q[3]), .y2(d37_latch_pre),
                    .a3(d33_o4), .b3(1'b1), .y3());  // sect2: LATCH gate; sect3: 5<-~MRD (4 unread, 6 dangling)

    // ============ peripherals (on the buffered buses) ============
    ppi_8255  U_PPI0 (.A(BA[1:0]), .D(DB), .cs_n(cs_ppi0_n), .rd_n(iord_n), .wr_n(iowr_n),
                      .reset(reset_sys), .portc_lo(mem_mode),
                      .kbd_en(kbd_en), .kbd_pressed(kbd_pressed), .kbd_shift(kbd_shift),
                      .kcol(kbd_kcol), .kbit(kbd_kbit));
    ppi_8255  U_PPI1 (.A(BA[1:0]), .D(DB), .cs_n(cs_ppi1_n), .rd_n(iord_n), .wr_n(iowr_n),
                      .reset(reset_sys), .portc_lo(),
                      .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0), .kcol(4'b0), .kbit(3'b0));
    pit_8253  U_PIT0 (.A(BA[1:0]), .D(DB), .cs_n(cs_pit0_n), .rd_n(iord_n), .wr_n(iowr_n), .clk());
    pit_8253  U_PIT1 (.A(BA[1:0]), .D(DB), .cs_n(cs_pit1_n), .rd_n(iord_n), .wr_n(iowr_n), .clk());
    pit_8253  U_PIT2 (.A(BA[1:0]), .D(DB), .cs_n(cs_pit2_n), .rd_n(iord_n), .wr_n(iowr_n), .clk());
    wire ser_txd, ser_rts, ser_dtr, ser_rxd;
    usart_8251 U_SIO0(.A(BA[0]),   .D(DB), .cs_n(cs_sio0_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(),
                      .txd(ser_txd), .rts(ser_rts), .dtr(ser_dtr), .rxd(ser_rxd));
    // ---- serial-port drivers -> X3 connector (К170АП2/УП2 + ЛА18; owner scan img). Buffer the USART
    // serial side out to the RS-232 connector; all off the CPU bus -> boot-safe. D14=SOUT, D32=RTS/DTP,
    // D3=TTL SOUT, D12=OC SOUT, D104=SIN receiver. TxD fans to the SOUT/TTL/OC drivers (same data, diff levels).
    wire s_sout, s_rts, s_dtp, s_ttl, s_oc, s_sin;
    ap2_drv U_D14 (.i3(ser_txd), .i2(1'b1),    .o6(s_sout), .o7());
    ap2_drv U_D32 (.i3(ser_rts), .i2(ser_dtr), .o6(s_rts),  .o7(s_dtp));
    wire int7_raw, int6_raw, ir7_sig, ir6_sig;
    assign int7_raw = 1'b1; assign int6_raw = 1'b1;   // X1 expansion -INT7/-INT6 [boundary: idle high]
    ln2_inv U_D3  (.a(ser_txd), .y(s_ttl),
                   .i13(int7_raw), .o12(ir7_sig), .i1(int6_raw), .o2(ir6_sig));  // sec 11->10: TTL SOUT = ~TxD; + INT6/INT7 inverters (sheet-1)
    la18_oc U_D12 (.i1(ser_txd), .i2(1'b1), .o3(s_oc));
    up2_rcv U_D104(.a(s_sin), .y(ser_rxd));
    serial_conn U_X3 (.sout(s_sout), .rts(s_rts), .dtp(s_dtp), .ttl_sout(s_ttl), .oc_sout(s_oc), .sin(s_sin));
    fdc_1793  U_FDC  (.A(BA[1:0]), .D(DB), .cs_n(cs_fdc_n),  .rd_n(iord_n), .wr_n(iowr_n), .clk());
    pic_8259  U_PIC  (.A(BA[0]),   .D(DB), .cs_n(cs_pic_n),  .rd_n(iord_n), .wr_n(iowr_n), .ir7(ir7_sig), .ir6(ir6_sig),
                      .intr(intr), .inta_n(inta_n));
    // 8259 interrupt/vector behavior (sim adjunct to U_PIC; unmapped -> LVS-invisible). Drives
    // the shared INT net (pic_8259 leaves it z) and injects the CALL vector during INTA.
    intr_ctl  U_INTR (.osc(sclk_i), .dbin(dbin), .inta_n(inta_n), .iowr_n(iowr_n),
                      .cs_pic_n(cs_pic_n), .a0(BA[0]), .frame_tick(frame_tick), .DB(DB), .intr(intr));

endmodule
`default_nettype wire
