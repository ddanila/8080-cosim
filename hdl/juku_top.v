// Juku processor module — structural top level (discrete-chip granularity).
// Mirrors the schematic (ref/schematics/, drawing DGSh5.109.006 E3): the CPU core
// is 8080 + 8224 clock + 8238 system controller + 8286 address buffers, producing
// the BUFFERED address bus (BA) / system data bus (DB) + strobes that the rest of
// the board hangs off. Each instance = a chip; wires = board nets. This is the LVS
// target. The authoritative endpoint model is kicad/juku.board.json.
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
    // READY section A is now represented by D30 below; its off-sheet -SSTB source and section B
    // remain boundaries. STSTB(8238) comes from D13/D38.
    wire        phi1, phi2, phi2ttl, ready, reset_sys, ststb_n;   // ststb_n = D38.8 [WIRE 8]
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
    wire        rom_sel_n, ram_sel_n, rev, roe_n;
    wire        io_strobe_h, d9_g1_w;      // D7 strobe-NAND out -> R17/C99 (net_boundary) -> D9.G1
    wire [3:0]  d103_q; wire d103_co, d103_ld;   // the /13 divider (D103+D33 loop, traced s2_d103)
    wire [7:0]  ppi0_pc;               // D26 Port C: PC2/3/4 -> D6 A5/6/7; PC4 also -> FDC DDEN
    // DRAM strobes (hoisted: the D36 CAS-rail tap reads cas_n in the mesh block). Array read:
    // R is PER BANK (rails 11/12/13/14 <- the D53 Y ladder), C (rail 15) + W (rail 16) are shared.
    wire        cas_n;
    wire        ras0_n, ras1_n, ras2_n, ras3_n;   // bank 0-3 RAS; populated bank D84-91 = ras3_n (rail 14 <- D53.Y0)

    // ============ CPU core (the discrete chips) ============
    cpu_8080  U_CPU (.sclk(sclk_i), .phi1(phi1), .phi2(phi2), .ready(ready), .reset(reset_sys),
                     .vss_gnd(1'b0), .vbb_m5v(1'b0), .vcc_5v(1'b1), .vdd_12v(1'b1),
                     .hold(1'b0), .intr(intr), .A(A), .D(D),
                     .dbin(dbin), .wr_n(wr_n), .sync(sync), .hlda(hlda),
                     .inte(inte), .wait_o(wait_o));

    // ---- discrete clock subsystem (faithful mesh; see board JSON provenance) ----
    // Z1 -> D59 (ЛН1 osc) -> OSC -> D40 (СТ16 divider) -> gate mesh D33(ЛН1)/D39(ЛА3)/D36(ЛА12)
    // -> D38 (ЛА1) = STB, and -> D35 (ЛН5) = Φ1/Φ2. D59/D40/D33/D39 are now FUNCTIONAL (not stubs)
    // and the divider->gate feedback nets D40.Q1->D39.12, D40.Q2->D33.5 are wired per the 2026-07
    // re-crop trace (see clock-mesh_tb for the running-divider proof). The boot-tb ties D59.xin=0 so
    // the divider is frozen at 0 -> d39_y=clkg_d33=1 -> ststb_n=~sync, i.e. boot stays byte-identical.
    wire osc_clk, clkg_d33, clkg_d36, d39_y, d33_o6; wire [3:0] d40_q;
    // sheet-2 LATCH/LOAD chain (D41 ИР16 -> D37 gate2 -> D33 inv; D38 gate2 -> D59 inv). Inputs of
    // D41/D38-2/D39-2 are deferred boundaries (numbered timing wires 1/2/4/15 + РЕ3 states).
    wire d41_qa, d41_qb, d41_ld_boundary, d41_ck_boundary, d37_latch_pre, latch_sig, d39_o8, d59_o10_tag10, load_pre, load_vid;
    net_boundary U_D41LDLNK (.a(1'b1), .b(d41_ld_boundary));
    net_boundary U_D41CKLNK (.a(1'b0), .b(d41_ck_boundary));
    ir16      U_D41 (.a(1'b0), .b(1'b0), .c(1'b0), .d(1'b0), .ld(d41_ld_boundary), .g(1'b1), .ck(d41_ck_boundary),
                     .ds(1'b1), .qd(), .qa(d41_qa), .qb(d41_qb), .qc());
    wire pst_clk;
    wire osc_fb, osc_pre;
    ln1_osc   U_D59 (.sclk(clk), .xin(osc_pre), .osc(osc_clk), .i13(load_pre), .o12(load_vid), .i11(d39_o8), .o10(d59_o10_tag10),
                     .i3(osc_clk), .o4(pst_clk), .i5(1'bz), .o6(), .i9(osc_fb), .o8(osc_pre));
    assign osc_fb = 1'bz; // R31/R32/Z1 meet here physically; analog crystal loop is outside HDL
    wire d40_ctrl_pull;
    net_boundary U_R34LNK (.a(1'b1), .b(d40_ctrl_pull));
    ct16_ctr  U_D40 (.clk(osc_clk), .r_n(d40_ctrl_pull), .ep(1'b1), .et(1'b1), .pe_n(d40_ctrl_pull), .d(4'bzzzz), .q(d40_q), .co());
    // D39 sections 3+4 (bite-2): NAND(rail1, gate-T) -> out3 -> rail 4 + own pin 4; then NAND(out3,
    // D92.8 "no CPU RAM access") -> out6 -> D52 B/A select. Gate-T (D39.1 = D92.2 = D92.3) and the
    // rail-1/rail-4 fanouts are pending; D92 is unmapped, so tri1 defaults keep the leg inert in sim.
`ifdef YOSYS
    wire d92_noacc;
`else
    tri1 d92_noacc;
`endif
    wire d39_memcyc, vid_cpu_sel;
    la3_gate  U_D39 (.a(d40_q[1]), .b(d40_q[0]), .y(d39_y), .a2(latch_sig), .b2(1'b1), .y2(d39_o8),  // pin9 <- D33.12 LATCH; pin10 remains pending; output8 -> D59.11
                     .a3(phi2ttl), .b3(1'b1), .y3(d39_memcyc),                                   // 1,2->3: pin1 <- Ф2TTL (bite-3; = ex gate-T), pin2 <- rail 1 [pending]
                     .a4(d39_memcyc), .b4(d92_noacc), .y4(vid_cpu_sel));                         // 4,5->6 -> D52.1
    wire d33_o4, d36_y2, d33_o10;
    wire d33_clk_rc;
    net_boundary U_R46LNK (.a(d40_q[0]), .b(d33_clk_rc));
    ln1_dual  U_D33 (.i9(d33_clk_rc), .i5(d40_q[2]), .o8(clkg_d33), .o6(d33_o6), .i13(d37_latch_pre), .o12(latch_sig),
                     .i1(d103_co), .o2(d103_ld),   // sect 1->2: D103 CO -> LD reload (the /13 divider loop, traced)
                     .i3(memr_n), .o4(d33_o4),  // + 13->12 = LATCH; 3->4 = ~MRD -> D37.5 (sheet-2)
                     .i11(d36_y2), .o10(d33_o10));  // 11->10 = CAS strobe-chain delay leg (bite-2)
    // D36 bite-2 sections: pin 1 TAPS the CAS rail (input); 12,13 (tied) = the CAS-driver NAND input
    // [west source pending]; its out 11 -> R57 -> rail 15 sits on the BOARD side of the R57 net
    // boundary, so cas_n itself stays driven by the sim scaffold in the DRAM block (boot unchanged).
`ifdef YOSYS
    wire d36_cas_in;
`else
    tri1 d36_cas_in;
`endif
    wire d36_b2_tag17;
    net_boundary U_D36B2LNK (.a(1'b1), .b(d36_b2_tag17));
    la12_gate U_D36 (.a(d40_q[1]), .b(d33_o6), .y(clkg_d36),   // pin5(A)<-D40.Q1(=D39.12), pin4(B)<-D33.6, pin6->D35.11 [traced]
                     .a2(cas_n), .b2(d36_b2_tag17), .y2(d36_y2),       // 1,2->3 -> D33.11; pin 2 <- rail 17 boundary
                     .a3(memw_n), .b3(d33_o10), .y3(),         // 9,10->8: W-strobe NAND(WR, CAS-delay) -> rail 16 (y3 on the board side of the W16 boundary)
                     .a4(d36_cas_in), .b4(d36_cas_in), .y4()); // 12,13->11 -> R57 -> rail 15 (CAS)
    wire pof_boundary;
    net_boundary U_D35POFLNK (.a(1'bz), .b(pof_boundary));
    clk_phase U_D35 (.osc(clkg_d36), .phsel(d40_q[1]), .phi1(phi1), .phi2(phi2), .phi2ttl(phi2ttl),
                     .i1(1'bz), .o2(), .i3(pof_boundary), .o4(), .i5(1'bz), .o6(), .i9(1'bz), .o8());
    wire d30_q, d30_qn, d30_q2, d30_q2n, d13_o4;
    wire d105_mrd_inv, d105_wait_stage;
`ifdef YOSYS
    wire d2_wait_raw, d105_h, d105_gate1_y, d105_wait_preinv;
`else
    tri1 d2_wait_raw;
    tri0 d105_h;
    wire d105_gate1_y, d105_wait_preinv;
`endif
    la3_gate U_D105 (.a(memr_n), .b(memr_n), .y(d105_mrd_inv),
                     .a2(memw_n), .b2(d13_o4), .y2(d105_gate1_y),
                     .a3(d105_wait_stage), .b3(d105_wait_stage), .y3(d105_wait_preinv),
                     .a4(d2_wait_raw), .b4(d105_h), .y4(d105_wait_stage)); // pin10 is named off-sheet H, not a proved supply
`ifdef YOSYS
    wire d30b_d_pre_n;
`else
    tri1 d30b_d_pre_n;
`endif
    // Sheet-1 proves D30 pins 10 (/PRE2) and 12 (D2) share this boundary net.
    tm2_dff U_D30 (.clr1_n(1'b1), .d1(1'b1), .clk1(phi2ttl), .pre1_n(1'b1),
                   .q1(d30_q), .q1_n(d30_qn), .clr2_n(d105_mrd_inv), .d2(d30b_d_pre_n),
                   .clk2(1'b0), .pre2_n(d30b_d_pre_n), .q2(d30_q2), .q2_n(d30_q2n));
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
    wire d38_load_i5, d38_load_i4, d38_load_i2, d38_load_i1;
    net_boundary U_D38I5LNK (.a(1'b1), .b(d38_load_i5));
    net_boundary U_D38I4LNK (.a(1'b1), .b(d38_load_i4));
    net_boundary U_D38I2LNK (.a(1'b1), .b(d38_load_i2));
    net_boundary U_D38I1LNK (.a(1'b1), .b(d38_load_i1));
    la1_gate  U_D38 (.i0(clkg_d33), .i1(sync), .i2(d39_y), .i3(d39_y), .y(stb_d38),   // pin12(I1) <- SYNC [WIRE 9]; pins 13+10 tied <- D39.11 (bite-3, ex-assumed D39Y)
                     .i4(d38_load_i5), .i5(d38_load_i4), .i6(d38_load_i2), .i7(d38_load_i1), .y2(load_pre));  // sect2 (5,4,2,1->6) = LOAD; four distinct timing-bundle boundaries
    // D13 (ТЛ2, Sheet-1) = the REAL 8238 status-strobe source (discrete, no 8224): section B STSTB =
    // ~sync -> ststb_n -> D5 STB(pin1); section A = RESIN Schmitt -> RES (boundary). Byte-identical
    // (same ~sync the D38 model produced) but now sourced from the faithful chip. [cpu-core.md]
    wire d37_y3;                      // D37 sect-3 out -> D58.OE (RAM-read gate, sheet-2)
    wire ram_out_en;                  // RAMOUTEN rail: DRIVEN by D13.2 (traced); load = D37.4 (sheet 2)
    // D13 = К555ТЛ2 hex Schmitt inverter (traced + census). Section 1->2 = the RAMOUTEN driver:
    // in <- D6.9 "-RAMOUTEN" (roe_n, modeled permissive-low => ram_out_en stays 1 = the old tri1
    // boot-verified value). Section 5->6 = RESIN Schmitt -> RES (boundary). Old dual-4-NAND
    // stand-in retired; STSTB comes from D38 directly (beeper wires 8/9).
    tl2_hex   U_D13 (.i1(roe_n), .o2(ram_out_en), .i3(1'b1), .o4(d13_o4),
                     .i5(1'b1), .o6(reset_sys), .i9(1'b1), .o8(),
                     .i11(1'b1), .o10(), .i13(1'b1), .o12());
    assign ststb_n = stb_d38;

    sysctl_8238 U_SYS (.D(D), .DB(DB), .dbin(dbin), .wr_n(wr_n), .hlda(hlda),
                       .vss_gnd(1'b0), .vcc_5v(1'b1),
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
`ifdef YOSYS
    wire int7_raw, int6_raw;
`else
    tri1 int7_raw, int6_raw;  // undriven expansion inputs idle inactive in simulation
`endif
    va87_out U_D23 (.Ain(BA[7:0]),  .Aout(adr_lo), .oe_n(1'b0), .t(1'b1));
    va87_out U_D24 (.Ain(BA[15:8]), .Aout(adr_hi), .oe_n(1'b0), .t(1'b1));
    wire d25_t_w;   // data-bus turnaround: D7 ЛА3 sect (5,4->6) -> D25.T (traced s1_egates2); inputs unread -> held transmit
    va87_out U_D25 (.Ain(DB),       .Aout(dat),    .oe_n(1'b0), .t(d25_t_w));
    expansion_conn U_X1 (.inhib_n(inhib_n), .cclck(cclck), .iom_n(iom_n), .mwc_n(mwc_n),
                         .mrc_n(mrc_n), .amwc_n(amwc_n), .iorc_n(iorc_n), .iowc_n(iowc_n),
                         .int7_raw(int7_raw), .int6_raw(int6_raw),
                         .dat(dat), .adr_lo(adr_lo), .adr_hi(adr_hi));

    // ============ I/O chip-select decode: К555ИД7 (74138) ============
    // A2:A0 select group, I/ORD & I/OWR enable; Y0..Y7 -> the chip-selects.
    // (refdes placeholder DID7; decode wiring is the standard 74138 pattern [assumed])
    wire [7:0] d8_d;
    re3_prom  U_D8   (.a(BA[15:11]), .e_n(rom_sel_n), .d(d8_d));   // A4..A0 = BA15..BA11; E_N <- D6.ROM_N (traced: the "12 ROM" rail into pin 15). Pager for ALL 8 sockets; see reconstructed-prom-fallbacks.md.
    net_boundary U_R17LNK (.a(io_strobe_h), .b(d9_g1_w));   // R17 200R (+C99 160pF deglitch) in series [traced]
    io_dec138 U_DID7 (.a(BA[10]), .b(BA[11]), .c(BA[12]),   // A10-A12 rails [sheet-1; = port bits 2-4 via IO mirror]
                      .g1(d9_g1_w), .g2a_n(rev), .g2b_n(rev),   // traced: G1 <- RC'd D7.11 strobe-NAND; G2A+G2B bridged <- REV
        .y_n({cs_fdc_n, cs_pit2_n, cs_pit1_n, cs_pit0_n, cs_ppi1_n, cs_sio0_n, cs_ppi0_n, cs_pic_n}));

    // ============ memory map decode: D6 (К556РТ4 PROM) gated by D7 (ЛА3) ============
    wire d7_a1_boundary, d7_b1_boundary, d7_y2_boundary, d7_a3_boundary, d7_b3_boundary, d7_y4_tag8;
    net_boundary U_D7A1LNK (.a(iowr_n), .b(d7_a1_boundary));
    net_boundary U_D7B1LNK (.a(iord_n), .b(d7_b1_boundary));
    net_boundary U_D7A3LNK (.a(1'b0), .b(d7_a3_boundary));
    net_boundary U_D7B3LNK (.a(1'b0), .b(d7_b3_boundary));
    la3_gate    U_D7     (.a(d7_a1_boundary), .b(d7_b1_boundary), .y(io_strobe_h),     // physical origins of pins12/13 unresolved; sim keeps prior IOWR/IORD semantics through boundaries
                          .a2(1'b1), .b2(memw_n), .y2(d7_y2_boundary),   // sect2: pin2 <- MEMW [WIRE 19, beeper]; pin1 <- D92.13 [WIRE 11, D92 unmapped]; pin3 far destination unread
                          .a3(d7_b3_boundary), .b3(d7_a3_boundary), .y3(d25_t_w),
                          .a4(iord_n), .b4(iowr_n), .y4(d7_y4_tag8));   // sect4 pins9/10 = IORD/IOWR; output8 -> tag8 boundary
    wire d6_v_enable;
    net_boundary U_D6VENLNK (.a(1'b0), .b(d6_v_enable));
    decode_prom U_DECODE (.a({BA[15:11], ppi0_pc[2], ppi0_pc[3], ppi0_pc[4]}),   // traced sheet-1: PC2/3/4 pins16/17/13 -> tags1/2/3 -> D6 pins2/1/15
                          .v_en_n(d6_v_enable),                               // V1/V2 are one source-visible, upstream-unread boundary
                          .rom_n(rom_sel_n), .ram_n(ram_sel_n), .rev(rev), .roe_n(roe_n));

    // ============ memory chips on the buffered buses ============
    // EPROM: 8 ROM sockets on the board, only 2 POPULATED (M2764 8Kx8 = the 16KB BIOS in the
    // leftmost field positions = D15/D16). ALL EIGHT CEs come from the D8 РЕ3 pager (traced
    // 2026-07: group-line tags 1..8 = D8.D4,D5,D6,D7,D0,D1,D2,D3 -> D15..D22 CS risers).
    eprom_8k #(.HALF(0)) U_D15 (.a(BA[12:0]), .d(DB), .cs_n(d8_d[4]), .oe_n(memr_n));  // BIOS low 8K (tag 1)
    eprom_8k #(.HALF(1)) U_D16 (.a(BA[12:0]), .d(DB), .cs_n(d8_d[5]), .oe_n(memr_n));  // BIOS high 8K (tag 2)
    // D17-D21 = unpopulated for the .009 boot config. D22 can be populated in sim with
    // +cart=<readmemh file> to model MAME's optional BASIC cartridge at 0x4000-0x5FFF.
    eprom_socket U_D17 (.a(BA[12:0]), .d(DB), .cs_n(d8_d[6]), .oe_n(memr_n));  // expansion (tag 3; no factory РЕ3 program selects it)
    eprom_socket U_D18 (.a(BA[12:0]), .d(DB), .cs_n(d8_d[7]), .oe_n(memr_n));  // expansion (tag 4)
    eprom_socket U_D19 (.a(BA[12:0]), .d(DB), .cs_n(d8_d[0]), .oe_n(memr_n));  // A000-BFFF bank (.117 one-cold D0; traced CS riser code 5)
    eprom_socket U_D20 (.a(BA[12:0]), .d(DB), .cs_n(d8_d[1]), .oe_n(memr_n));  // 8000-9FFF bank (code 6)
    eprom_socket U_D21 (.a(BA[12:0]), .d(DB), .cs_n(d8_d[2]), .oe_n(memr_n));  // 6000-7FFF bank (code 7)
    exprom_8k    U_D22 (.a(BA[12:0]), .d(DB), .cs_n(d8_d[3]), .oe_n(memr_n));  // 4000-5FFF bank (code 8), optional BASIC cartridge

    // DRAM: К565РУ5 64Kx1 array. 32 sockets on the board (4 banks x 8), only 8 POPULATED
    // = one byte-bank bit-sliced D84..D91 = the real 64KB RAM. The other 24 sockets are
    // bank-expansion (up to 256KB), unpopulated. There is NO separate video plane -- the
    // video reads this same bank via the КП14 µP/video mux. Address is MULTIPLEXED (MA);
    // RAS/CAS from the D53 ИД7 decoder + АГ3 timing (see board JSON provenance).
    wire [7:0] MA;                 // muxed row/col address  (from address mux)
    // (ras_n/cas_n declared with the chip-select wires up top: the D36 CAS-rail tap needs them early)
    // W rail (rail 16): every DRAM W pin hangs on rail 16, driven by D36.8 (the strobe-chain write
    // leg -- array read). The sim cannot reproduce that RC/delay chain, so behaviorally the write
    // strobe stays MEMW through a net_boundary (boot-identical); D36 pin 8 is omitted from the LVS
    // pinmap accordingly (documented in W_RAIL16's src note -- the copper follows the real net).
    wire dram_we_n;
    net_boundary U_W16LNK (.a(memw_n), .b(dram_we_n));
    wire [15:0] vid_addr;          // video raster address into the framebuffer (РУ5 2nd port)
    wire [7:0]  vbyte;             // framebuffer byte at vid_addr (from the 8 РУ5 video reads)
    // DRAM datapath (sheet-2 confirmed): WRITE = DB -> РУ5 DI directly (DI rails 31-38 are the
    // DB inter-sheet codes); READ = РУ5 DO bus (rails 1-8) -> D58 ИР82 latch -> DB, OE-gated by
    // the D37 read strobe. (The earlier write-latch reading of D58 was reversed.)
        // D58 = RAM READ-data latch (sheet-2 confirmed): РУ5 DO bus (rails 1-8) -> D -> Q -> DB,
    // OE = D37 sect-3 read strobe. Writes go DB -> РУ5 DI directly (rails 31-38 = DB codes).
    wire [7:0] rdo;                    // РУ5 DO read bus
    wire d58_stb_tag5;
    net_boundary U_D58STBLNK (.a(1'b0), .b(d58_stb_tag5));
    ir82_latch U_D58 (.d(rdo), .stb(d58_stb_tag5), .oe_n(d37_y3), .q(DB));
    // Populated bank = D84-D91 (bottom array row) per the official ДГШ5.109.009 ПЭЗ; board #1
    // (rev 7.102.100) had the TOP row (D60-67) stuffed instead -- a per-revision factory choice.
    dram_64kx1 U_D84 (.sclk(sclk_i), .ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[0]), .do_(rdo[0]), .va(vid_addr), .vq(vbyte[0]));
    dram_64kx1 U_D85 (.sclk(sclk_i), .ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[1]), .do_(rdo[1]), .va(vid_addr), .vq(vbyte[1]));
    dram_64kx1 U_D86 (.sclk(sclk_i), .ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[2]), .do_(rdo[2]), .va(vid_addr), .vq(vbyte[2]));
    dram_64kx1 U_D87 (.sclk(sclk_i), .ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[3]), .do_(rdo[3]), .va(vid_addr), .vq(vbyte[3]));
    dram_64kx1 U_D88 (.sclk(sclk_i), .ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[4]), .do_(rdo[4]), .va(vid_addr), .vq(vbyte[4]));
    dram_64kx1 U_D89 (.sclk(sclk_i), .ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[5]), .do_(rdo[5]), .va(vid_addr), .vq(vbyte[5]));
    dram_64kx1 U_D90 (.sclk(sclk_i), .ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[6]), .do_(rdo[6]), .va(vid_addr), .vq(vbyte[6]));
    dram_64kx1 U_D91 (.sclk(sclk_i), .ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[7]), .do_(rdo[7]), .va(vid_addr), .vq(vbyte[7]));
    // ---- unpopulated DRAM rows 0-2 (D60-D83): sockets wired to the shared MA/CAS/WE + per-bit
    // DIN/DOUT buses and per-row RAS. Passive (no chip installed) -> boot-safe. Completes the
    // 4x8 РУ5 array for the PCB.
    ru5_socket U_D60 (.ma(MA), .ras_n(ras0_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[0]), .do_(rdo[0]));
    ru5_socket U_D61 (.ma(MA), .ras_n(ras0_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[1]), .do_(rdo[1]));
    ru5_socket U_D62 (.ma(MA), .ras_n(ras0_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[2]), .do_(rdo[2]));
    ru5_socket U_D63 (.ma(MA), .ras_n(ras0_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[3]), .do_(rdo[3]));
    ru5_socket U_D64 (.ma(MA), .ras_n(ras0_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[4]), .do_(rdo[4]));
    ru5_socket U_D65 (.ma(MA), .ras_n(ras0_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[5]), .do_(rdo[5]));
    ru5_socket U_D66 (.ma(MA), .ras_n(ras0_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[6]), .do_(rdo[6]));
    ru5_socket U_D67 (.ma(MA), .ras_n(ras0_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[7]), .do_(rdo[7]));
    ru5_socket U_D68 (.ma(MA), .ras_n(ras1_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[0]), .do_(rdo[0]));
    ru5_socket U_D69 (.ma(MA), .ras_n(ras1_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[1]), .do_(rdo[1]));
    ru5_socket U_D70 (.ma(MA), .ras_n(ras1_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[2]), .do_(rdo[2]));
    ru5_socket U_D71 (.ma(MA), .ras_n(ras1_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[3]), .do_(rdo[3]));
    ru5_socket U_D72 (.ma(MA), .ras_n(ras1_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[4]), .do_(rdo[4]));
    ru5_socket U_D73 (.ma(MA), .ras_n(ras1_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[5]), .do_(rdo[5]));
    ru5_socket U_D74 (.ma(MA), .ras_n(ras1_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[6]), .do_(rdo[6]));
    ru5_socket U_D75 (.ma(MA), .ras_n(ras1_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[7]), .do_(rdo[7]));
    ru5_socket U_D76 (.ma(MA), .ras_n(ras2_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[0]), .do_(rdo[0]));
    ru5_socket U_D77 (.ma(MA), .ras_n(ras2_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[1]), .do_(rdo[1]));
    ru5_socket U_D78 (.ma(MA), .ras_n(ras2_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[2]), .do_(rdo[2]));
    ru5_socket U_D79 (.ma(MA), .ras_n(ras2_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[3]), .do_(rdo[3]));
    ru5_socket U_D80 (.ma(MA), .ras_n(ras2_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[4]), .do_(rdo[4]));
    ru5_socket U_D81 (.ma(MA), .ras_n(ras2_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[5]), .do_(rdo[5]));
    ru5_socket U_D82 (.ma(MA), .ras_n(ras2_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[6]), .do_(rdo[6]));
    ru5_socket U_D83 (.ma(MA), .ras_n(ras2_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[7]), .do_(rdo[7]));

    // ---- video address counters + address mux + RAS/CAS decoder (drive РУ5 MA/RAS/CAS) ----
    // sel/en + counter preset are the assumed parts; chips D44-D50/D53 are scan-verified.
    // Video-address counter chain (sheet-2 verified 74193s): VA[15:0], CO->UP cascade.
    // Presets: D44 A-D grounded; S3.1-2 -> D45 C/D; S3.3-6 -> both D46 and D47 A-D [drawn].
    // LD sources (D34 XOR chain) + CLR rail = boundaries.
    wire [15:0] VA; wire co0, co1, co2;
    wire [3:0] s3_hi_preset;
    net_boundary U_S3P0LNK (.a(1'b0), .b(s3_hi_preset[0]));
    net_boundary U_S3P1LNK (.a(1'b0), .b(s3_hi_preset[1]));
    net_boundary U_S3P2LNK (.a(1'b0), .b(s3_hi_preset[2]));
    net_boundary U_S3P3LNK (.a(1'b0), .b(s3_hi_preset[3]));
    wire ctr_ld_n;                     // D34 XOR-RC-XOR pulse (LD of D44/D45)
`ifdef YOSYS
    wire d34_b2;
`else
    tri0 d34_b2;                       // RC node (C5) boundary: idle low -> ctr_ld_n = 1 (counting)
`endif
    wire d56_q2, d56_q2_n, d34_sync_phys, d34_rc_drive, d34_a1_tag2;
    net_boundary U_D34A1LNK (.a(1'b0), .b(d34_a1_tag2));
    lp5_xor U_D34 (.a1(d34_a1_tag2), .b1(1'b0), .y1(d34_rc_drive), .a2(1'b1), .b2(d34_b2), .y2(ctr_ld_n),
                   .a3(d56_q2), .b3(d56_q2_n), .y3(d34_sync_phys), .a4(d103_q[3]), .b4(1'b1), .y4());
    ie7_ctr  U_D44 (.up(pst_clk), .down(1'b1), .load_n(ctr_ld_n), .clr(1'b0), .d(4'b0), .q(VA[3:0]),   .co(co0), .bo());   // UP <- PST CLK [D59.4, sheet-2]
    ie7_ctr  U_D45 (.up(co0),     .down(1'b1), .load_n(ctr_ld_n), .clr(1'b0), .d(4'b0), .q(VA[7:4]),   .co(co1), .bo());
    // D46/D47 share one LD vertical (bite-2); its driver = the D59.12 "LOAD" inverter [likely,
    // path not continuously traced] -> tri1 boundary (1 = not loading, boot-identical to the old
    // 1'b1 ties). The S3 preset rails are explicit in the board netlist; simulation keeps the
    // default all-switches-closed preset value at zero until configuration controls are exposed.
`ifdef YOSYS
    wire vid_hi_ld_n;   // DOWN pins tie to rail "A" = +5V (bite-3) -> plain 1'b1 constants
`else
    tri1 vid_hi_ld_n;
`endif
    ie7_ctr  U_D46 (.up(co1),     .down(1'b1), .load_n(vid_hi_ld_n), .clr(1'b0), .d(s3_hi_preset), .q(VA[11:8]),  .co(co2), .bo());
    ie7_ctr  U_D47 (.up(co2),     .down(1'b1), .load_n(vid_hi_ld_n), .clr(1'b0), .d(s3_hi_preset), .q(VA[15:12]), .co(), .bo());
    // DRAM address mux: sel=Φ1 puts the ROW (BA[15:8]) on MA during RAS, the COL (BA[7:0]) during
    // CAS. (CPU row/col realized; the video path through this mux is the un-modeled boundary.)
    // NOTE sheet-2 draws the Y->MA rail order as pins 4,12,9,7; we keep the consistent
    // 4,7,9,12 order until the mux INPUT rails are read (a line-swap must be applied to both
    // sides at once or the video-va path desyncs). Queued in round-2 notes.
`ifdef YOSYS
    wire cpu_mux_g_n;                 // E13 strap -> D48/D49 G (posts: 1=rail, 2=+5, 4=GND)
`else
    tri0 cpu_mux_g_n;                 // undriven boundary; tri0 = strap-enabled default (CPU pair drives MA)
`endif
    kp14_mux U_D48 (.a({BA[1], BA[2], BA[3], BA[0]}), .b({BA[13], BA[11], BA[10], BA[9]}),
                    .sel(phi1), .en_n(cpu_mux_g_n), .y({MA[1], MA[2], MA[3], MA[0]}));
    kp14_mux U_D49 (.a({BA[5], BA[6], BA[7], BA[4]}), .b({BA[14], BA[15], BA[8], BA[12]}),
                    .sel(phi1), .en_n(cpu_mux_g_n), .y({MA[5], MA[6], MA[7], MA[4]}));
    // D50/D51 = the VIDEO-address mux pair on the SAME tri-state MA bus (sheet-2: Q -> rails
    // 21-28). A/B ins <- video counters + S3 config [unread boundaries]; G enables alternate
    // with D48/D49 on the video cycle [source unread] -- held disabled here (z), so the CPU
    // pair keeps driving MA and boot stays identical. SEL <- D41.QA [WIRE 10, beeper ✓].
`ifdef YOSYS
    wire vid_mux_g_n;                 // E14 strap -> D50/D51 G (video-cycle enable; boundary)
`else
    tri1 vid_mux_g_n;                 // undriven boundary; tri1 = E14's +5 strap default (video pair disabled)
`endif
    kp14_mux U_D50 (.a({VA[1], VA[2], VA[3], VA[0]}), .b({VA[13], VA[11], VA[10], VA[9]}),
                    .sel(d41_qa), .en_n(vid_mux_g_n), .y({MA[1], MA[2], MA[3], MA[0]}));
    kp14_mux U_D51 (.a({VA[5], VA[6], VA[7], VA[4]}), .b({VA[14], VA[15], VA[8], VA[12]}),
                    .sel(d41_qa), .en_n(vid_mux_g_n), .y({MA[5], MA[6], MA[7], MA[4]}));
    // RAS/CAS strobes: RAM-select (ram_sel_n) gated by Φ1 (RAS) / Φ2 (CAS). [assumed timing]
    wire mem_active = ~(memr_n & memw_n);   // a memory read or write is in progress
    // D53 per sheet-2: A/B from the D52 КП14 mux via the E2/E3 config jumpers (2-3 position ties
    // them to Φ1/Φ2 -- the traced/boot config), C + G2 grounded. Bite-2: D52 ins = µP ADDRESS
    // codes 8,9 (BA7/BA8) vs VIDEO ADDRESS codes 8,9 (VA7/VA8), select <- D39.6, G grounded;
    // D53.G3's drawn feed = a long west line [pending] -> net_boundary keeps the sim's RAM-decode
    // enable (boot unchanged) while LVS reflects the unknown wiring. Y0-Y3 leave through the
    // R49-R52 100R series ladder to the PER-BANK RAS rails (array read): Y0->rail 14 = bank 3
    // (D84-91, the populated bank), Y1->rail 13 = bank 2, Y2->rail 12 = bank 1, Y3->rail 11 =
    // bank 0. C (rail 15) and W (rail 16) are shared across banks; the real CAS driver is
    // D36.11 -> R57 (mesh block) -- cas_n here is the sim scaffold behind that boundary, carried
    // on the SIM-ONLY cas_sim leg (same LVS contract as SACTIVE).
    wire [3:0] d52_y; wire e2_com, e3_com;
    wire d53_g_in; wire [3:0] d53_y; wire d53_cas_sim;
    kp14_mux  U_D52 (.a({2'bzz, BA[8], BA[7]}), .b({2'bzz, VA[8], VA[7]}),
                     .sel(vid_cpu_sel), .en_n(1'b0), .y(d52_y));   // video/µP addr mux (bite-2)
    jumper3   U_E2  (.p1(d52_y[0]), .p3(phi1), .p2(e2_com));
    jumper3   U_E3  (.p1(d52_y[1]), .p3(phi2), .p2(e3_com));
    net_boundary U_G3LNK  (.a(ram_sel_n), .b(d53_g_in));   // -> ram_en_sim (SIM-ONLY DRAM-enable semantics)
    rascas_dec U_D53 (.a(e2_com), .b(e3_com), .c(1'b0), .g(vid_cpu_sel), .g2a_n(phi2ttl), .g2b_n(1'b0),
                      .sactive(mem_active), .ram_en_sim(d53_g_in),
                      .y_n(d53_y), .y_n4(), .y_n5(), .y_n6(), .y_n7(), .cas_sim(d53_cas_sim));
    net_boundary U_R49LNK (.a(d53_y[0]), .b(ras3_n));   // Y0 -> R49 -> rail 14 (bank 3, POPULATED)
    net_boundary U_R50LNK (.a(d53_y[1]), .b(ras2_n));   // Y1 -> R50 -> rail 13 (bank 2 sockets)
    net_boundary U_R51LNK (.a(d53_y[2]), .b(ras1_n));   // Y2 -> R51 -> rail 12 (bank 1 sockets)
    net_boundary U_R52LNK (.a(d53_y[3]), .b(ras0_n));   // Y3 -> R52 -> rail 11 (bank 0 sockets)
    net_boundary U_R57LNK (.a(d53_cas_sim), .b(cas_n)); // sim CAS scaffold -> rail 15

    // ---- video dot clock: АГ3 D56 (16 MHz RC one-shot) -> ИЕ10 D103 divider (-> 1.23 MHz) ----
    wire xtal16m_w;   // the 16MHz crystal rail, bundle tag 14 (traced s2_dotclk_bend); OSC-merge pending
    wire sync_b_w;   // D57.OUT2 "SYNC B." -> both D56 triggers (traced s2_a_rows/s2_pin2_corner)
    wire d56_clr_w;   // shared CLR rail = R61 12k pullup (traced); boundary-driven so yosys keeps the net
    net_boundary U_D56CLRLNK (.a(1'b1), .b(d56_clr_w));
    ag3_oneshot U_D56  (.a_n(1'b1), .b(sync_b_w), .clr_n(d56_clr_w), .a2_n(1'b1), .b2(sync_b_w), .clr2_n(d56_clr_w),
                        .q(), .q_n(), .q2(d56_q2), .q2_n(d56_q2_n));
    ie10_ctr    U_D103 (.clk(xtal16m_w), .clr_n(1'b1), .load_n(d103_ld), .enp(1'b1), .ent(1'b1), .d(4'b0), .q(d103_q), .co(d103_co));   // QD (pin 11) = the 1.23MHz rail -> D57.CLK2 (traced s2_d103)

    // ---- runnable video-output stage: raster-scan the framebuffer -> ИР16 serialize -> ЛП5 combine
    // Reads the РУ5 framebuffer via its sim-only 2nd port (vid_addr -> vbyte) at the raster address,
    // serializes each byte at the dot clock through the ИР16, and drives the composite video the
    // display sees. Driven by the sim `dotclk`. The RUNNABLE demo uses the abstracted 8-bit ir16_sr
    // (U_IR16) -> lp5_xor (U_D34V); the REAL chips D42/D43 (ИР16) are instantiated below for the LVS
    // structure (traced sheet-2 top-right; see board JSON provenance). The 2x4-bit +
    // analog node-"A" byte->pixel scheme + the КП14 µP/video arbitration remain physical boundaries.
    wire vpixel, vshl_n;
    video_raster U_VRAS (.dotclk(dotclk), .vid_addr(vid_addr), .shl_n(vshl_n));  // raster scan (unmapped)
    ir16_sr U_IR16 (.clk(dotclk), .clk_inh(1'b0), .shl_n(vshl_n), .clr_n(1'b1), .si(1'b0),
                    .d(vbyte), .so(vpixel));                            // abstracted serializer (runnable)
    lp5_xor1 U_D34V (.a(vpixel), .b(1'b0), .y(vid_out));                 // composite video out (runnable)
    // Real pixel serializers (LVS structure): D42 = high nibble, D43 = low nibble. Parallel data
    // reads the REAL system data bus DB (the bit-sliced РУ5 drives the byte there during a video
    // read); CK joins the dot-clock net; DS = GND; shared load VID_LD; Q -> node "A" (analog mix =
    // boundary). The video-read SLOT timing (КП14 µP/video arbitration + РЕ3/АГ3) stays a boundary.
    wire d42_q, d43_q;
    // D42/D43 = the PIXEL SHIFT REGISTERS (array read, 3rd and geometry-anchored reading of this
    // zone -- supersedes both the "bank-select latch" and "VA-state latch" [finding-24 registry]
    // interpretations, which both fell into the reused-code trap): parallel ins = the РУ5 DO rails
    // 1-8 (D67.DO enters D42.D directly on the sheet), D43.Q -> D42.DS cascade, CK = ctrl-rail 3
    // (dot clock), LD = ctrl-rail 6 = D59.12 (the INVERTED load strobe: D38.6 -> D59.13, and
    // 13->12 feeds rail 6 -- one-inversion correction of the earlier array read; net LOAD_VID).
    // G <- ctrl-rail 8 [pending]. Q -> D37 inverter -> analog video mix.
    wire shift_g;
    net_boundary U_SHIFTGLNK (.a(1'b1), .b(shift_g));
    ir16 U_D42 (.d(rdo[7]), .c(rdo[6]), .b(rdo[5]), .a(rdo[4]),
                .ld(load_vid), .g(shift_g), .ck(xtal16m_w), .ds(d43_q), .qd(d42_q), .qa(), .qb(), .qc());
    ir16 U_D43 (.d(rdo[3]), .c(rdo[2]), .b(rdo[1]), .a(rdo[0]),
                .ld(load_vid), .g(shift_g), .ck(xtal16m_w), .ds(1'b0), .qd(d43_q), .qa(), .qb(), .qc());
    // D37 (ЛА3) inverts D42's serial output (pins 12,13 tied to D42.Q pin10) before the analog
    // node-"A" summing mix; its output (pin 11) enters that resistor mix (R38 1k) -> boundary.
    wire d37_out;
    la3_gate U_D37 (.a(d42_q), .b(d42_q), .y(d37_out), .a2(d41_qb), .b2(d40_q[3]), .y2(d37_latch_pre),
                    .a3(d33_o4), .b3(ram_out_en), .y3(d37_y3), .a4(1'bz), .b4(1'bz), .y4());  // sect3 = RAM-read gate: 5<-~MRD, 4<-RAM OUT EN [WIRE 12], 6 -> D58.OE [sheet-2]; sect4 undrawn/NC

    // ============ FDC quadrant scaffold (.009): ВГ93 + РЕ3 .092 + ВА87 bus buffer ============
    // Bus side traced (CS7/sheet-3 delta + MAME 1C-1F + WD1793 datasheet); support logic
    // (КП12 muxes, АГ3 one-shots, drive cable) = owner-session territory. Stubs are inert.
    wire [7:0] fdc_dal; wire fdc_drq, fdc_intrq;
    wire fdc_prom_re_n, fdc_prom_cs_n, fdc_prom_we_n;
    vg93_fdc   U_D93  (.cs_n(fdc_prom_cs_n), .re_n(fdc_prom_re_n), .we_n(fdc_prom_we_n), .a0(BA[0]), .a1(BA[1]),
                       .mr_n(1'b1), .clk(1'b0), .dden(ppi0_pc[4]), .dal(fdc_dal),
                       .drq(fdc_drq), .intrq(fdc_intrq));
    wire d100_oe_boundary, d100_t_boundary;
    net_boundary U_D100OELNK (.a(1'b1), .b(d100_oe_boundary));
    net_boundary U_D100TLNK  (.a(1'b1), .b(d100_t_boundary));
    buf_8287   U_D100 (.a(DB), .b(fdc_dal), .oe_n(d100_oe_boundary), .t(d100_t_boundary), .vss_gnd(1'b0), .vcc_5v(1'b1));
    wire d94_d3, d94_d4, d94_d5, d94_d6, d94_d7;
`ifdef YOSYS
    wire d94_en_boundary;
`else
    tri0 d94_en_boundary;
`endif
    // July-2026 two-sided local photo registration + continuous component
    // copper: D94.1(D0)->D93.4 RE, .2(D1)->D93.3 CS, .3(D2)->D93.2 WE.
    // The photographs show no branch to the formerly assumed global I/O rails.
    re3_prom_092 U_D94 (.a(BA[15:11]), .e_n(d94_en_boundary),
                        .d({d94_d7, d94_d6, d94_d5, d94_d4,
                            d94_d3, fdc_prom_we_n, fdc_prom_cs_n, fdc_prom_re_n}));

    // ============ peripherals (on the buffered buses) ============
    wire [7:0] kbd_pa;                 // -> X9 (SC0-3, STB) + AUDC/PREN boundaries
    ppi_8255  U_PPI0 (.A(BA[1:0]), .D(DB), .cs_n(cs_ppi0_n), .rd_n(iord_n), .wr_n(iowr_n),
                      .pa(kbd_pa), .pb(8'hFF),
                      .reset(reset_sys), .pc(ppi0_pc),
                      .kbd_en(kbd_en), .kbd_pressed(kbd_pressed), .kbd_shift(kbd_shift),
                      .kcol(kbd_kcol), .kbit(kbd_kbit));
    ppi_8255  U_PPI1 (.A(BA[1:0]), .D(DB), .cs_n(cs_ppi1_n), .rd_n(iord_n), .wr_n(iowr_n),
                      .pa(), .pb(8'hFF),
                      .reset(reset_sys), .pc(),
                      .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0), .kcol(4'b0), .kbit(3'b0));
    // PIT cascade per the pinned MAME driver: D54 horiz -> D55 vert -> FRAME INT.
    // 1 MHz = D40 QD (the same /16 tap that feeds the D37 latch chain, net LATCH_B); 2 MHz =
    // D40 QC; 1.23 MHz (D57 baud clk0) = D103 /13 [boundary, undriven].
    wire clk1m = d40_q[3];
    wire clk2m = d40_q[2];
    wire clk123m;
    wire pit_hchain, pit_hsync_dsl, pit_vchain, frame_int, pit_baud, pit_sound;
    pit_8253  U_PIT0 (.A(BA[1:0]), .D(DB), .cs_n(cs_pit0_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(),
                      .clk0(clk1m), .gate0(1'b1), .clk1(clk1m), .gate1(pit_hchain),
                      .clk2(clk1m), .gate2(pit_hchain),
                      .out0(pit_hchain), .out1(), .out2(pit_hsync_dsl));
    pit_8253  U_PIT1 (.A(BA[1:0]), .D(DB), .cs_n(cs_pit1_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(),
                      .clk0(pit_hchain), .gate0(1'b1), .clk1(pit_hsync_dsl), .gate1(pit_vchain),
                      .clk2(pit_hsync_dsl), .gate2(pit_vchain),
                      .out0(pit_vchain), .out1(frame_int), .out2());
    pit_8253  U_PIT2 (.A(BA[1:0]), .D(DB), .cs_n(cs_pit2_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(),
                      .clk0(d103_q[3]), .gate0(1'b1), .clk1(clk2m), .gate1(1'b1),
                      .clk2(d103_q[3]), .gate2(1'b1),   // traced: CLK0+CLK2 share 1.23M = D103.QD
                      .out0(pit_baud), .out1(pit_sound), .out2(sync_b_w));   // OUT1 = SOUND beeper; OUT2 = SYNC B. -> D56 (traced)
    wire ser_txd, ser_rts, ser_dtr, ser_rxd, ser_cts_n, ser_dsr_n, ser_syndet;
    usart_8251 U_SIO0(.A(BA[0]),   .D(DB), .cs_n(cs_sio0_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(d13_o4),
                      .vss_gnd(1'b0), .vcc_5v(1'b1),
                      .rxc(pit_baud), .txc(pit_baud),
                      .txd(ser_txd), .rts(ser_rts), .dtr(ser_dtr), .rxrdy(), .txrdy(), .syndet(ser_syndet), .txempty(),
                      .rxd(ser_rxd), .cts_n(ser_cts_n), .reset(reset_sys), .dsr_n(ser_dsr_n));
    // ---- serial-port drivers -> X3 connector (К170АП2/УП2 + ЛА18; owner scan img). Buffer the USART
    // serial side out to the RS-232 connector; all off the CPU bus -> boot-safe. D14=SOUT, D32=RTS/DTP,
    // D3=TTL SOUT, D12=OC SOUT, D104=SIN receiver. TxD fans to the SOUT/TTL/OC drivers (same data, diff levels).
    wire s_sout, s_rts, s_dtp, s_ttl, s_oc, s_sin, s_cts, s_dsr, ser_txd_inv;
    ap2_drv U_D14 (.i3(ser_txd), .i2(1'b1),    .o6(s_sout), .o7());
    ap2_drv U_D32 (.i3(ser_rts), .i2(ser_dtr), .o6(s_rts),  .o7(s_dtp));
    wire ir7_sig, ir6_buf, ir6_sig;
    ln2_inv U_D3  (.a(ser_txd), .y(s_ttl),
                   .i13(int7_raw), .o12(ir7_sig), .i1(int6_raw), .o2(ir6_buf),
                   .i3(1'bz), .o4(), .i5(1'bz), .o6(),
                   .i9(ser_txd), .o8(ser_txd_inv));
    // S4 selects PIC IR6 between buffered -INT6 and USART SYNDET. The photographed
    // build defaults to the external-interrupt throw for simulation.
    spdt_switch U_S4 (.syndet_throw(ser_syndet), .int6_throw(ir6_buf), .ir6_common(ir6_sig));
    la18_oc U_D12 (.i1(ser_txd_inv), .i2(ser_txd_inv), .o3(s_oc));
    up2_rcv U_D104(.sin_in(s_sin), .sin_out(ser_rxd),
                   .cts_in(s_cts), .cts_out(ser_cts_n),
                   .dsr_in(s_dsr), .dsr_out(ser_dsr_n));
    serial_conn U_X3 (.pullup_io(), .aux2(s_oc), .ttl_sout(s_ttl), .sin(s_sin),
                      .cts(s_cts), .dsr(s_dsr), .aux7(), .aux8(),
                      .sout(s_sout), .rts(s_rts), .dtp(s_dtp), .oc_sout(s_oc));
    fdc_1793  U_FDC  (.A(BA[1:0]), .D(DB), .cs_n(cs_fdc_n),  .rd_n(iord_n), .wr_n(iowr_n),
                      .nc_back_bias(1'bz), .vss_gnd(1'b0), .vcc_5v(1'b1), .vdd_12v(1'b1),
                      .mr_n(1'b1), .clk(sclk_i), .dden(ppi0_pc[4]), .motor_on(ppi0_pc[2]), .side(ppi0_pc[6]),
                      .step(), .dirc(), .early(), .late(), .test(1'b1), .hlt(1'b1),
                      .rg(), .rclk(1'b0), .raw_read(1'b1), .hld(), .tg43(), .wg(), .wdata(),
                      .ready(1'b1), .wf_vfoe(), .tr00(1'b0), .index(1'b0), .wprt(1'b0),
                      .drq(fdc_drq), .intrq(fdc_intrq));
    wire pic_sp_en = 1'b1; // sheet-1 A-rail strap: standalone/master 8259
    pic_8259  U_PIC  (.A(BA[0]),   .D(DB), .cs_n(cs_pic_n),  .rd_n(iord_n), .wr_n(iowr_n),
                      .vss_gnd(1'b0), .vcc_5v(1'b1),
                      .ir7(ir7_sig), .ir6(ir6_sig), .ir5(frame_int), .ir3(1'b0), .ir2(1'b0), .ir1(fdc_drq), .ir0(fdc_intrq),
                      .cas0(), .cas1(), .cas2(), .sp_en(pic_sp_en), .intr(intr), .inta_n(inta_n));
    // 8259 interrupt/vector behavior (sim adjunct to U_PIC; unmapped -> LVS-invisible). Drives
    // the shared INT net (pic_8259 leaves it z) and injects the CALL vector during INTA.
    intr_ctl  U_INTR (.osc(sclk_i), .dbin(dbin), .inta_n(inta_n), .iowr_n(iowr_n),
                      .cs_pic_n(cs_pic_n), .a0(BA[0]), .frame_tick(frame_tick), .DB(DB), .intr(intr));

endmodule
`default_nettype wire
