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
    // READY section A is represented by D30 below; native sheet-2 D38.8 exports
    // active-low STB to sheet-1 -SSTB/D30.1 on the D38 side of factory wire W8.
    // STSTB(8238) comes from D38.8 over factory wire 8.
    wire        phi1, phi2, phi1_d35, phi2_d35, phi2ttl, ready, reset_sys, ststb_n;
    wire        stb_d38;
    wire        sclk_i;   // shared sim sampling clock (CPU + DRAM + intr): external `osc`, or self-clocked

    // ---- buffered board buses + control strobes (out of the CPU core) ----
    wire [15:0] BA;         // buffered address bus
`ifdef YOSYS
    wire [7:0]  DB;         // buffered system data bus (see D above re: tri1 vs wire)
`else
    tri1 [7:0]  DB;
`endif
    wire        memr_n, memr_n_d7, memw_n, memw_n_d7p2, iord_n, iowr_raw_n, iowr_n, inta_n;
    wire        intr;
    wire        busen_n = 1'b0;       // bus always enabled
    wire        buf_oe_n = 1'b0, buf_t = 1'b1;   // 8286: enabled, CPU->bus

    // ---- chip selects + memory enables ----
    wire        cs_pic_n, cs_ppi0_n, cs_sio0_n, cs_ppi1_n;
    wire        cs_pit0_n, cs_pit1_n, cs_pit2_n, cs_fdc_n;
    wire        d6_v_enable;
`ifdef YOSYS
    wire        d6_rom_select_n, d6_ram_output_n;
    wire        d6_rev_physical, d6_roe_physical;
`else
    // Physical R11..R14 recover the four open-collector D6 outputs high.
    tri1        d6_rom_select_n, d6_ram_output_n;
    tri1        d6_rev_physical, d6_roe_physical;
`endif
`ifdef YOSYS
    // Structural/LVS path: chip-removed continuity preserves separate D6.12
    // ROM-select and D6.11 RAM-select conductors.
    wire        rev = d6_rev_physical, roe_n = d6_roe_physical;
    wire        rom_sel_n = d6_rom_select_n, ram_sel_n = d6_ram_output_n;
`else
    // The 2026-07-19 revision-3 reread fixed the original reader's reversed
    // four-channel packing. The corrected physical `.038` table now drives all
    // four traced outputs directly and boots byte-identical to cosim; no sim-only
    // output polarity fit remains. A7 is the measured D7.8 I/O-cycle qualifier
    // shared with D105.1.
    wire        rev       = d6_rev_physical;
    wire        roe_n     = d6_roe_physical;
    wire        rom_sel_n = d6_rom_select_n;
    wire        ram_sel_n = d6_ram_output_n;
`endif
    wire        io_strobe_h, io_cycle_h, d9_g1_w; // D7.11 decode strobe; D7.8 raw I/O-cycle qualifier
    wire [3:0]  d103_q; wire d103_co, d103_ld;   // the /13 divider (D103+D33 loop, traced s2_d103)
    wire [7:0]  ppi0_pc;
    wire        d3_o4_d6_a6, d3_o6_d6_a5;
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
    wire osc_clk, clkg_d33, clkg_d36, d39_y, d33_o6, xtal16m_w; wire [3:0] d40_q;
    // sheet-2 LATCH/LOAD chain (D41 ИР16 -> D37 gate2 -> D33 inv; D38 gate2 -> D59 inv).
    // Full-resolution bundle read: D41.LD joins rail17/D36.B2; D41.CK joins rail8/D42.G/D43.G.
    wire d41_qa, d41_qa_d41, d41_qb, d36_b2_tag17, shift_g, d37_latch_pre, latch_sig, d39_o8, d59_o10_tag10, load_pre, load_vid;
    ir16      U_D41 (.a(1'b0), .b(1'b0), .c(1'b0), .d(1'b0), .ld(d36_b2_tag17), .g(1'b1), .ck(shift_g),
                     .ds(1'b1), .qd(), .qa(d41_qa_d41), .qb(d41_qb), .qc());
    net_boundary U_W10 (.a(d41_qa), .b(d41_qa_d41));
    wire pst_clk;
    wire osc_fb, osc_pre;
    ln1_osc   U_D59 (.sclk(clk), .xin(osc_pre), .osc(osc_clk), .i13(load_pre), .o12(load_vid), .i11(d39_o8), .o10(d59_o10_tag10),
                     .i3(osc_clk), .o4(pst_clk), .i5(1'bz), .o6(), .i9(osc_fb), .o8(osc_pre));
    assign osc_fb = 1'bz; // R31/R32/Z1 meet here physically; analog crystal loop is outside HDL
    wire d40_ctrl_pull;
    net_boundary U_R34LNK (.a(1'b1), .b(d40_ctrl_pull));
    ct16_ctr  U_D40 (.clk(osc_clk), .r_n(d40_ctrl_pull), .ep(1'b1), .et(1'b1), .pe_n(d40_ctrl_pull), .d(4'bzzzz), .q(d40_q), .co());
    // Native sheet 2 labels D40 Q3/Q2/Q1/Q0 as 1/2/4/8 MHz respectively.
    // Recovered .009 sheet 3 carries all four rails into the D95 FDC clock mux.
    wire clk1m = d40_q[3];
    wire clk2m = d40_q[2];
    wire clk4m = d40_q[1];
    wire clk8m = d40_q[0];
    // D92 is the native sheet-2 RAM-access combiner.  Section 1 qualifies a
    // read from ROE, PHI2TTL, and -MRD; section 2 qualifies
    // a write from PHI2TTL, -MWR, and -RAM SEL.  Section 3 NORs those results
    // (the write result is intentionally tied to two inputs) into D92.8, the
    // "no CPU RAM access" input of D39.5. Native sheet labels prove that
    // factory wire 11 extends the global -MRD conductor from D92.13 to D7.1.
    wire d92_rd_nor, d92_wr_nor, d92_noacc;
    le4_nor3 U_D92 (.a1(roe_n), .b1(phi2ttl), .c1(memr_n), .y1(d92_rd_nor),
                    .a2(phi2ttl), .b2(memw_n), .c2(ram_sel_n), .y2(d92_wr_nor),
                    .a3(d92_wr_nor), .b3(d92_wr_nor), .c3(d92_rd_nor), .y3(d92_noacc));
    // D39 sections 3+4: NAND(rail1, gate-T) -> out3 -> rail 4 + own pin 4;
    // then NAND(out3, D92.8) -> out6 -> D52 B/A select.
    wire d39_memcyc, vid_cpu_sel;
    la3_gate  U_D39 (.a(d40_q[1]), .b(d40_q[0]), .y(d39_y), .a2(latch_sig), .b2(xtal16m_w), .y2(d39_o8),  // pin9 <- D33.12 LATCH; pin10 <- local control rail3 / 16MHz
                     .a3(phi2ttl), .b3(1'b0), .y3(d39_memcyc),                                   // 1,2->3: pin1 <- Ф2TTL; pin2 <- grounded control rail1 (shared D43.DS)
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
    net_boundary U_D36B2LNK (.a(1'b1), .b(d36_b2_tag17));
    la12_gate U_D36 (.a(d40_q[1]), .b(d33_o6), .y(clkg_d36),   // pin5(A)<-D40.Q1(=D39.12), pin4(B)<-D33.6, pin6->D35.11 [traced]
                     .a2(cas_n), .b2(d36_b2_tag17), .y2(d36_y2),       // 1,2->3 -> D33.11; pin 2 <- rail 17 boundary
                     .a3(memw_n), .b3(d33_o10), .y3(),         // 9,10->8: W-strobe NAND(WR, CAS-delay) -> rail 16 (y3 on the board side of the W16 boundary)
                     .a4(d36_cas_in), .b4(d36_cas_in), .y4()); // 12,13->11 -> R57 -> rail 15 (CAS)
    wire vert_rtr, frame_int;
    clk_phase U_D35 (.osc(clkg_d36), .phsel(d40_q[1]), .phi1(phi1_d35), .phi2(phi2_d35), .phi2ttl(phi2ttl),
                     .i1(1'bz), .o2(), .i3(ppi0_pc[7]), .o4(), .i5(1'bz), .o6(),
                     .i9(vert_rtr), .o8(frame_int));
    net_boundary U_W7  (.a(phi1_d35), .b(phi1));
    net_boundary U_W14 (.a(phi2_d35), .b(phi2));
    wire d30_q, d30_qn, d30_q2, d30_q2n, d13_o4, iorc_n;
    wire d105_memw_inv, d105_dbin_n, d105_dbin_gated;
    wire [3:1] d2_nc; // factory symbol draws only D0/pin12; D1-D3 are intentional NCs
`ifdef YOSYS
    wire d105_h, ready_d, d30b_d_pre_n, d30_pre1_n;
    wire wreq_n;
`else
    tri1 d105_h, ready_d, d30b_d_pre_n, d30_pre1_n;
    tri1 wreq_n;
`endif
`ifdef YOSYS
    assign wreq_n = d6_ram_output_n; // chip-removed continuity: D6.11 -> D2.15/-WREQ
`endif
    wait_prom_037 U_D2 (.a({wreq_n, A[10], iorc_n, A[14], cas_n, A[9], A[15], A[12]}),
                        .v1_n(1'b0), .v2_n(1'b0),
                        .d({d2_nc, ready_d}));
    la3_gate U_D105 (.a(memw_n), .b(memw_n), .y(d105_memw_inv),
                     .a2(io_cycle_h), .b2(d13_o4), .y2(iowr_n),
                     .a3(d105_dbin_n), .b3(d105_dbin_n), .y3(d105_dbin_gated),
                     .a4(dbin), .b4(d105_h), .y4(d105_dbin_n));
    // Owner continuity: D2.12 + R6 -> D30.D1; Q1 -> R29 -> CPU READY.
    // D30.10/.12 share the R5 pull-up; D105.11 clears section B from ~MEMW.
    tm2_dff #(.FUNCTIONAL(1)) U_D30 (.clr1_n(stb_d38), .d1(ready_d), .clk1(phi2ttl), .pre1_n(d30_pre1_n),
                   .q1(d30_q), .q1_n(d30_qn), .clr2_n(d105_memw_inv), .d2(d30b_d_pre_n),
                   .clk2(d13_o4), .pre2_n(d30b_d_pre_n), .q2(d30_q2), .q2_n(d30_q2n));
    net_boundary U_R29LNK (.a(d30_q), .b(ready));
    // vm80a sampling clock. Default = external `osc` (forced-clock boot tbs). With SELF_CLOCK the CPU
    // is driven entirely by the mesh: sclk = D40 divider LSB, phases = D35 from d40_q[1]. This exactly
    // reproduces the boot-tb's waveform (osc posedge mid-phase, one per phase) but self-generated.
`ifdef SELF_CLOCK
    assign sclk_i = d40_q[0];
`else
    assign sclk_i = osc;
`endif
    // D38 (ЛА1) is the clock-mesh gate producing active-low status STB on pin 8.
    // It reaches D30.1 directly and D5.1 only across factory wire W8.
    wire timing_tag2;
    net_boundary U_D38I4LNK (.a(1'b1), .b(timing_tag2));
    la1_gate  U_D38 (.i0(clkg_d33), .i1(sync), .i2(d39_y), .i3(d39_y), .y(stb_d38),   // pin12(I1) <- SYNC [WIRE 9]; pins 13+10 tied <- D39.11 (bite-3, ex-assumed D39Y)
                     .i4(d39_memcyc), .i5(timing_tag2), .i6(1'b0), .i7(cas_n), .y2(load_pre));  // sect2 LOAD: pins5/4/2/1 <- rails4/2/1/15; only rail2 origin remains pending
    // D38.8 is the physical 8238 status-strobe source: ~sync -> ststb_n -> D5 STB(pin1).
    // D13 remains the separate Schmitt inverter package for RAMOUTEN, system-clock handoff,
    // reset, and the D6/D105 edge path. [cpu-core.md]
    wire d37_y3;                      // D37 sect-3 out -> D58.OE (owner-confirmed D37.6-D58.9)
    wire ram_out_en;                  // RAMOUTEN rail: owner-confirmed D13.2 -> D37.4
    // D13 = К555ТЛ2 hex Schmitt inverter (traced + census). Section 1->2 = the RAMOUTEN driver:
    // in <- D6.9 "-RAMOUTEN" (roe_n, modeled permissive-low => ram_out_en stays 1 = the old tri1
    // boot-verified value). Section 5->6 = RESIN Schmitt -> RES (boundary). Old dual-4-NAND
    // stand-in retired; STSTB comes from D38 directly (beeper wires 8/9).
    tl2_hex   U_D13 (.i1(roe_n), .o2(ram_out_en), .i3(wr_n), .o4(d13_o4),
                     .i5(1'b1), .o6(reset_sys), .i9(1'b1), .o8(),
                     .i11(1'b1), .o10(), .i13(d105_h), .o12(d6_v_enable));
    // Factory wire A:8 is an assembly conductor, not PCB copper. Keeping it as
    // a mapped boundary cell makes its two registered landing islands visible
    // to LVS while preserving the zero-delay runnable behavior.
    net_boundary U_W8 (.a(stb_d38), .b(ststb_n));

    sysctl_8238 U_SYS (.D(D), .DB(DB), .dbin(d105_dbin_gated), .wr_n(wr_n), .hlda(hlda),
                       .vss_gnd(1'b0), .vcc_5v(1'b1),
                       .ststb_n(ststb_n), .busen_n(busen_n),
                       .memr_n(memr_n), .memw_n(memw_n),
                       .iord_n(iord_n), .iowr_n(iowr_raw_n), .inta_n(inta_n));
    net_boundary U_W11 (.a(memr_n_d7), .b(memr_n));
    net_boundary U_W19 (.a(memw_n_d7p2), .b(memw_n));

    buf_8286  U_BUFL (.Ain(A[7:0]),  .Aout(BA[7:0]),  .oe_n(buf_oe_n), .t(buf_t));
    buf_8286  U_BUFH (.Ain(A[15:8]), .Aout(BA[15:8]), .oe_n(buf_oe_n), .t(buf_t));

    // ============ expansion/backplane interface (Phase B, sheet 1 -- bus-interface.md) ============
    // D29 (ВА86) = the full bus-command transceiver, 8 signals (B0..B7 per owner's scan read):
    //   B0 -INHIB, B1 -CCLCK, B2 -IO/M, B3 -MWC, B4 -MRC, B5 -AMWC, B6 -IORC, B7 -IOWC.
    // A-side reads the four direct strobes plus D7.3 -> A5 -> -AMWC and the
    // shared D7.5/D29.3 status boundary -> A0 -> -INHIB. Owner continuity puts
    // physical D29.4/A2 on IORD; the older D7.8->D29.4 IOM_STATUS reading is
    // retained only as a recheck boundary. The remaining CCLCK
    // source stays an inactive boundary. One-way (never drives the
    // strobe nets -> boot-safe).
    wire inhib_n, cclck, iom_n, mwc_n, mrc_n, amwc_n, iowc_n;
    wire d7_y2_amw_n;  // D7.3 destination remains a boundary; former D29.5 assignment was disproved
    wire d7_b3_inhib_status;  // D7.5 shares semantic command A0 on physical D29 A2/pin3; physical B2/pin17 is -INHIB
    va86_out U_D29 (.Ain ({d30_q2n, iord_n, iowr_n, memr_n, memw_n, iord_n, 1'b1, d7_b3_inhib_status}),
                    .Aout({iowc_n, iorc_n, amwc_n, mrc_n,  mwc_n,  iom_n, cclck, inhib_n}),
                    .oe_n(1'b0), .t(1'b1));
    // Address/data backplane transceivers (ВА87; refdes confirmed by owner from scan):
    //   D23 = addr LOW  (BA[7:0]  -> -ADR0..-ADR7)
    //   D24 = addr HIGH (BA[15:8] -> -ADR8..-ADRF)
    //   D25 = data      (DB       -> -DAT0..-DAT7)
    // D23/D24 are strapped A->B. D25 is bidirectional under its traced T control;
    // an absent expansion card leaves the connector side released and boot-safe.
    wire [7:0] adr_lo, adr_hi, dat;
`ifdef YOSYS
    wire int7_raw, int6_raw;
`else
    tri1 int7_raw, int6_raw;  // undriven expansion inputs idle inactive in simulation
`endif
    va87_out U_D23 (.Ain(BA[7:0]),  .Aout(adr_lo), .oe_n(1'b0), .t(1'b1));
    va87_out U_D24 (.Ain(BA[15:8]), .Aout(adr_hi), .oe_n(1'b0), .t(1'b1));
    wire d25_t_w;   // data-bus turnaround: D7 ЛА3 sect (5,4->6) -> D25.T; pin4=MEMW, pin5=-INHIB source boundary
    va87_out U_D25 (.Ain(DB),       .Aout(dat),    .oe_n(1'b0), .t(d25_t_w));
    expansion_conn U_X1 (.inhib_n(inhib_n), .cclck(cclck), .iom_n(iom_n), .mwc_n(mwc_n),
                         .mrc_n(mrc_n), .amwc_n(amwc_n), .iorc_n(iorc_n), .iowc_n(iowc_n),
                         .wreq_n(wreq_n),
                         .int7_raw(int7_raw), .int6_raw(int6_raw),
                         .dat(dat), .adr_lo(adr_lo), .adr_hi(adr_hi));

    // ============ I/O chip-select decode: К555ИД7 (74138) ============
    // A2:A0 select group, I/ORD & I/OWR enable; Y0..Y7 -> the chip-selects.
    // (refdes placeholder DID7; decode wiring is the standard 74138 pattern [assumed])
`ifdef YOSYS
    wire [7:0] d8_d;
`else
    // D8 is open collector; released socket-select rails recover high through
    // the physical TTL/pull-up environment without changing LVS connectivity.
    tri1 [7:0] d8_d;
`endif
    re3_prom  U_D8   (.a(BA[15:11]), .e_n(rom_sel_n), .d(d8_d));
    net_boundary U_R17LNK (.a(io_strobe_h), .b(d9_g1_w));   // R17 200R (+C99 160pF deglitch) in series [traced]
    io_dec138 U_DID7 (.a(BA[10]), .b(BA[11]), .c(BA[12]),   // A10-A12 rails [sheet-1; = port bits 2-4 via IO mirror]
                      .g1(d9_g1_w), .g2a_n(rev), .g2b_n(rev),   // traced: G1 <- RC'd D7.11 strobe-NAND; G2A+G2B bridged <- REV
        .y_n({cs_fdc_n, cs_pit2_n, cs_pit1_n, cs_pit0_n, cs_ppi1_n, cs_sio0_n, cs_ppi0_n, cs_pic_n}));

    // ============ memory map decode: D6 (К556РТ4 PROM) gated by D7 (ЛА3) ============
    // Physical first section is a propagation-delay strobe: pin12=SYNC and
    // pin13 feeds back from output pin11 before R17. Preserve that topology in
    // structural LVS; zero-delay runnable simulation retains the equivalent
    // decoded-I/O activity oracle to avoid a combinational feedback loop.
`ifdef YOSYS
    wire d7_a1_w = sync, d7_b1_w = io_strobe_h;
`else
    wire d7_a1_w = iowr_raw_n, d7_b1_w = iord_n;
`endif
    net_boundary U_D7B3LNK (.a(1'b0), .b(d7_b3_inhib_status));  // shared source is unread; low preserves the existing boot-safe D25 turnaround scaffold
    la3_gate    U_D7     (.a(d7_a1_w), .b(d7_b1_w), .y(io_strobe_h),
                          .a2(memr_n_d7), .b2(memw_n_d7p2), .y2(d7_y2_amw_n), // sect2: pin2 <- MEMW through W19; pin1 <- D92.13 through W11 / -MRD; pin3 destination remains a boundary
                          .a3(memw_n), .b3(d7_b3_inhib_status), .y3(d25_t_w),  // native sheet: pin4 T-joins MEMW/D29.1; pin5 shares D29.3 -INHIB source
                          .a4(iord_n), .b4(iowr_raw_n), .y4(io_cycle_h));  // D7.8 -> D105.1 + D6.A7: high during either I/O cycle
    decode_prom U_DECODE (.a({io_cycle_h, d3_o4_d6_a6, d3_o6_d6_a5, BA[11], BA[12], BA[13], BA[14], BA[15]}),
                          .v_en_n(d6_v_enable),
                          .rom_n(d6_rom_select_n), .ram_n(d6_ram_output_n),
                          .rev(d6_rev_physical), .roe_n(d6_roe_physical));
    // Functional decode oracle retired from the boot path (runnable selects now
    // come from U_DECODE above). `decode_prom_functional` stays defined in
    // devices.v only as the contrast reference for the B37A runtime diagnostic.

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
    eprom_socket U_D19 (.a(BA[12:0]), .d(DB), .cs_n(d8_d[0]), .oe_n(memr_n));  // traced CS riser code 5; physical .039 never asserts it
    eprom_socket U_D20 (.a(BA[12:0]), .d(DB), .cs_n(d8_d[1]), .oe_n(memr_n));  // code 6; physical .039 never asserts it
    eprom_socket U_D21 (.a(BA[12:0]), .d(DB), .cs_n(d8_d[2]), .oe_n(memr_n));  // code 7; physical .039 never asserts it
    exprom_8k    U_D22 (.a(BA[12:0]), .d(DB), .cs_n(d8_d[3]), .oe_n(memr_n));  // code 8; physical .039 never asserts it

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
    dram_64kx1 U_D84 (.ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[0]), .do_(rdo[0]), .va(vid_addr), .vq(vbyte[0]));
    dram_64kx1 U_D85 (.ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[1]), .do_(rdo[1]), .va(vid_addr), .vq(vbyte[1]));
    dram_64kx1 U_D86 (.ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[2]), .do_(rdo[2]), .va(vid_addr), .vq(vbyte[2]));
    dram_64kx1 U_D87 (.ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[3]), .do_(rdo[3]), .va(vid_addr), .vq(vbyte[3]));
    dram_64kx1 U_D88 (.ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[4]), .do_(rdo[4]), .va(vid_addr), .vq(vbyte[4]));
    dram_64kx1 U_D89 (.ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[5]), .do_(rdo[5]), .va(vid_addr), .vq(vbyte[5]));
    dram_64kx1 U_D90 (.ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[6]), .do_(rdo[6]), .va(vid_addr), .vq(vbyte[6]));
    dram_64kx1 U_D91 (.ma(MA), .ras_n(ras3_n), .cas_n(cas_n), .we_n(dram_we_n), .di(DB[7]), .do_(rdo[7]), .va(vid_addr), .vq(vbyte[7]));
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
    wire d56_qn, d56_q2, d56_q2_n, d34_sync_phys, d34_rc_drive, d34_a1_tag2;
    net_boundary U_D34A1LNK (.a(1'b0), .b(d34_a1_tag2));
    lp5_xor U_D34 (.a1(d34_a1_tag2), .b1(1'b0), .y1(d34_rc_drive), .a2(1'b1), .b2(d34_b2), .y2(ctr_ld_n),
                   .a3(d56_q2), .b3(d56_qn), .y3(d34_sync_phys), .a4(d103_q[3]), .b4(1'b1), .y4());
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
    net_boundary U_G3LNK  (.a(ram_sel_n), .b(d53_g_in));
    rascas_dec U_D53 (.a(e2_com), .b(e3_com), .c(1'b0), .g(vid_cpu_sel), .g2a_n(phi2ttl), .g2b_n(1'b0),
                      .sactive(mem_active), .ram_en_sim(d53_g_in),
                      .y_n(d53_y), .y_n4(), .y_n5(), .y_n6(), .y_n7(), .cas_sim(d53_cas_sim));
    net_boundary U_R49LNK (.a(d53_y[0]), .b(ras3_n));   // Y0 -> R49 -> rail 14 (bank 3, POPULATED)
    net_boundary U_R50LNK (.a(d53_y[1]), .b(ras2_n));   // Y1 -> R50 -> rail 13 (bank 2 sockets)
    net_boundary U_R51LNK (.a(d53_y[2]), .b(ras1_n));   // Y2 -> R51 -> rail 12 (bank 1 sockets)
    net_boundary U_R52LNK (.a(d53_y[3]), .b(ras0_n));   // Y3 -> R52 -> rail 11 (bank 0 sockets)
    net_boundary U_R57LNK (.a(d53_cas_sim), .b(cas_n)); // sim CAS scaffold -> rail 15

    // ---- video dot clock: 16 MHz crystal rail -> ИЕ10 D103 divider (-> 1.23 MHz) ----
    // D56 is the adjacent sync/one-shot chain; its Q_N is source-proved separate from this rail.
    // 16MHz source bundle tag14 becomes local control rail3 at D39/D42/D43; native-sheet
    // source-side chase cannot prove its expected physical merge with OSC, so LVS keeps it separate.
    wire sync_b_w;   // D57.OUT2 "SYNC B." -> both D56 triggers (traced s2_a_rows/s2_pin2_corner)
    wire d56_clr_w;   // shared CLR rail = R61 12k pullup (traced); boundary-driven so yosys keeps the net
    net_boundary U_D56CLRLNK (.a(1'b1), .b(d56_clr_w));
    ag3_oneshot U_D56  (.a_n(1'b0), .b(sync_b_w), .clr_n(d56_clr_w), .a2_n(1'b0), .b2(sync_b_w), .clr2_n(d56_clr_w),
                        .q(), .q_n(d56_qn), .q2(d56_q2), .q2_n(d56_q2_n));
    ie10_ctr    U_D103 (.clk(xtal16m_w), .clr_n(1'b1), .load_n(d103_ld), .enp(1'b1), .ent(1'b1), .d(4'b0011), .q(d103_q), .co(d103_co));   // D0/D1 high, D2/D3 low: traced /13 preset; QD (pin 11) = 1.23MHz -> D57.CLK2

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
    // G <- ctrl-rail 8, shared with D41.CK. Q -> D37 inverter -> analog video mix.
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

    // ============ Physical FDC quadrant (.009): КР1818ВГ93 + РЕ3 .092 + drive ВА87 ============
    // Recovered .009 Э3 sheet 3 closes the direct D0-D7 host bus, D93-to-D100
    // drive outputs, D26 MOTOR/S.SEL controls, and the first status/separator stages.
    wire fdc_drq, fdc_intrq;
    wire fdc_step, fdc_dir, fdc_hld, fdc_tg43, fdc_wg, fdc_wdata;
    wire fdc_early_boundary, fdc_late_boundary, fdc_test_wf_vfoe;
    wire fdc_rg_nc, fdc_rclk, fdc_raw_read;
    wire fdc_ready, fdc_tr00, fdc_index, fdc_wprt;
    wire fdc_clk, fdc_separator_clk;
    // D95 select A0 is FM/MFM (D26 PC4); select A1 is 5-inch/8-inch
    // (D26 PC3). Section A selects 1 MHz at A1=0 or 2 MHz at A1=1;
    // section B selects 8 MHz only at 00 and otherwise 4 MHz. Both enables
    // are sheet-grounded. Sheet 3 also closes D106: raw read loads 4'hf,
    // the unused UP clock and preset inputs are pulled high through R78,
    // CLR is grounded, DOWN receives this mux clock, and Q3 drives D28.9.
    kp12_mux U_D95 (.a0(ppi0_pc[4]), .a1(ppi0_pc[3]),
                     .oe0_n(1'b0), .oe1_n(1'b0),
                     .d0({clk2m, clk2m, clk1m, clk1m}),
                     .d1({clk4m, clk4m, clk4m, clk8m}),
                     .q0(fdc_clk), .q1(fdc_separator_clk));
    wire d106_preset_high;
    wire [3:0] d106_q;
    wire d106_co_unused, d106_bo_unused, d106_q3_to_d28;
    net_boundary U_D106PRESET (.a(1'b1), .b(d106_preset_high));
    ie7_ctr U_D106 (.up(d106_preset_high), .down(fdc_separator_clk),
                    .load_n(fdc_raw_read), .clr(1'b0), .d({4{d106_preset_high}}),
                    .q(d106_q), .co(d106_co_unused), .bo(d106_bo_unused));
    net_boundary U_D106Q3LNK (.a(d106_q[3]), .b(d106_q3_to_d28));
    // D28.2 is the open-collector inverter between D106.Q3 and D96.CLK1;
    // R85 provides its pull-up. Sheet 3 closes D96.1 as a divide-by-two
    // toggle: /Q feeds D, Q drives VG93 RCLK, and WREQ_N holds both
    // asynchronous controls inactive except during writes.
    wire d96_separator_clk, d96_q1_n, d96_q2n_test;
    wire d96_irq_conditioned_boundary, d96_irq_clock_boundary;
    wire d96_irq_q_sheet1_boundary;
    assign d96_separator_clk = ~d106_q3_to_d28;
    tm2_dff #(.FUNCTIONAL(1)) U_D96 (
        .clr1_n(wreq_n), .d1(d96_q1_n), .clk1(d96_separator_clk), .pre1_n(wreq_n),
        .q1(fdc_rclk), .q1_n(d96_q1_n),
        .clr2_n(1'bz), .d2(d96_irq_conditioned_boundary),
        .clk2(d96_irq_clock_boundary), .pre2_n(d96_irq_conditioned_boundary),
        .q2(d96_irq_q_sheet1_boundary), .q2_n(d96_q2n_test));
`ifdef YOSYS
    wire fdc_prom_re_n, fdc_prom_cs_n, fdc_prom_we_n;
`else
    // The physical RE3 outputs are open collector. The board pull-ups are not
    // yet identified, but their logic function is required by the runnable path.
    tri1 fdc_prom_re_n, fdc_prom_cs_n, fdc_prom_we_n;
`endif
    // D94 РЕ3 .092 outputs. D94.5 is NC; the visible short open PCB stub
    // belongs to the separate D93.1 boundary.
`ifdef YOSYS
    wire d94_d0_boundary;
`else
    // Owner inspection finds a pull-up on D0; retain its hidden-branch output
    // as a readable open-collector node in simulation without inventing a load.
    tri1 d94_d0_boundary;
`endif
    wire d94_d4, d94_d5, d94_d6, d94_d7;
`ifdef YOSYS
    wire d94_d1_d99_a2n;
`else
    // R89 pulls the measured D94.2-D99.9 node high.
    tri1 d94_d1_d99_a2n;
`endif
    wire d93_1_open_stub;
    wire d99_b_test_landing, d99_q1n_boundary, d99_q2_boundary;
    wire d99_clr2_boundary, d99_q2n_boundary, d99_q1_nc;
    // Exact `.009` sheets join D13.6 RES continuation (3) directly to D93.19.
    // The sheet-3 `-RES` text/bubbled input conflicts with the sheet-1 RES name;
    // preserve that physical conductor here. The separate behavioral adjunct
    // below keeps its established inactive-reset fit until bench polarity is known.
    vg93_fdc   U_D93  (.nc_back_bias(d93_1_open_stub), .cs_n(fdc_prom_cs_n), .re_n(fdc_prom_re_n), .we_n(fdc_prom_we_n), .a0(BA[0]), .a1(BA[1]),
                       .mr_n(reset_sys), .clk(fdc_clk), .dden(ppi0_pc[4]), .dal(DB),
                       .vss_gnd(1'b0), .vcc_5v(1'b1), .vdd_12v(1'b1),
                       .step(fdc_step), .dirc(fdc_dir), .early(fdc_early_boundary), .late(fdc_late_boundary),
                       .test(fdc_test_wf_vfoe), .hlt(fdc_ready), .rg(fdc_rg_nc),
                       .rclk(fdc_rclk), .raw_read(fdc_raw_read), .hld(fdc_hld), .tg43(fdc_tg43),
                       .wg(fdc_wg), .wdata(fdc_wdata), .ready(fdc_ready),
                       .wf_vfoe(fdc_test_wf_vfoe), .tr00(fdc_tr00), .index(fdc_index), .wprt(fdc_wprt),
                       .drq(fdc_drq), .intrq(fdc_intrq));
    // Exact sheet 3 grounds D99 A1/CLR1 and omits Q1. B2 and the four
    // remaining signal outputs/clear leave through distinct remote paths;
    // the `(1)` beside B2 denotes a continuation to sheet 1, not logic high.
    wire d99_b2_sheet1_boundary;
    ag3_oneshot U_D99 (.a_n(1'b0), .b(d99_b_test_landing), .clr_n(1'b0),
                       .q(d99_q1_nc), .q_n(d99_q1n_boundary),
                       .a2_n(d94_d1_d99_a2n), .b2(d99_b2_sheet1_boundary),
                       .clr2_n(d99_clr2_boundary), .q2(d99_q2_boundary),
                       .q2_n(d99_q2n_boundary));
    wire d100_control_sheet1_boundary, d100_wrdata_in_boundary;
`ifndef YOSYS
    // Runnable fallback only: the three remote sheet-1 sources are not yet
    // known. Keep inactive defaults out of the LVS/physical netlist.
    assign d99_b2_sheet1_boundary = 1'b1;
    assign d100_control_sheet1_boundary = 1'b1;
`endif
    wire [7:0] d100_drive_in, d100_drive_out;
    assign d100_drive_in = {ppi0_pc[6], ppi0_pc[2], d100_wrdata_in_boundary,
                            fdc_wg, fdc_tg43, fdc_hld, fdc_step, fdc_dir};
    buf_8287 U_D100 (.a(d100_drive_in), .b(d100_drive_out),
                     .oe_n(d100_control_sheet1_boundary), .t(d100_control_sheet1_boundary),
                     .vss_gnd(1'b0), .vcc_5v(1'b1));
`ifdef YOSYS
    net_boundary U_D99B2LNK (.a(1'b1), .b(d99_b2_sheet1_boundary));
    net_boundary U_D100CTL1LNK (.a(1'b1), .b(d100_control_sheet1_boundary));
    net_boundary U_D100WDATALNK (.a(1'b1), .b(d100_wrdata_in_boundary));
`elsif FDC_VA87_CS_QUALIFIED
    wire d100_oe_boundary = fdc_prom_cs_n;
    wire d100_t_boundary = fdc_prom_re_n;
`elsif FDC_VA87_ALWAYS_ENABLED
    wire d100_oe_boundary = 1'b0;
    wire d100_t_boundary = fdc_prom_re_n;
`else
    wire d100_oe_boundary = 1'b1;
    wire d100_t_boundary = 1'b1;
`endif
`ifndef YOSYS
    // Diagnostic firmware-profile transform only. The recovered factory sheet
    // proves this is not physical D100; keeping the unmapped adjunct preserves
    // CMA/NOP profile regressions without asserting false PCB connectivity.
    wire [7:0] fdc_profile_dal;
`ifdef FDC_VA87_CS_QUALIFIED
    buf_8287 U_FDC_PROFILE_BUF (.a(DB), .b(fdc_profile_dal), .oe_n(d100_oe_boundary),
                                .t(d100_t_boundary), .vss_gnd(1'b0), .vcc_5v(1'b1));
`elsif FDC_VA87_ALWAYS_ENABLED
    buf_8287 U_FDC_PROFILE_BUF (.a(DB), .b(fdc_profile_dal), .oe_n(d100_oe_boundary),
                                .t(d100_t_boundary), .vss_gnd(1'b0), .vcc_5v(1'b1));
`endif
`endif
`ifdef YOSYS
    wire d94_a4_d101_q0;
`else
    // Simulation-only functional fallbacks do not assert copper identity. The
    // A4 is D101.Q0; its runnable behavior remains pulled high while the mux
    // inputs are unresolved. A3 is the now-measured D105.3 qualified /WR rail.
    supply1 d94_a4_d101_q0;
`endif
    // Owner continuity supersedes the earlier mirrored/numbering interpretation:
    // D94.2(D1)->D99.9+R89, D94.3(D2)->D93.4+R88, and
    // D94.4(D3)->D93.2+R87. D94.1(D0) has only the R8 2k pull-up.
    // Measured D94 inputs: A0=D93.A0/BA0, A1=D93.A1/BA1,
    // A2=IORD (D27.5 and D29.4), A3=D105.3 qualified peripheral /WR,
    // A4=D101.Q0. D104.7 is separate (~84 kohm to A3). The former scaffold is retired.
`ifdef YOSYS
    // Preserve the unresolved physical enable source in the LVS netlist.
    net_boundary U_D94CSLNK (.a(1'b1), .b(fdc_prom_cs_n));
`else
    // Simulation-only upstream fallback: the functional port decoder supplies
    // the shared D94.E_N/D93.CS_N level until its physical source is measured.
    net_boundary U_D94CSLNK (.a(cs_fdc_n), .b(fdc_prom_cs_n));
`endif
`ifdef YOSYS
    net_boundary U_D94D0LNK (.a(1'b1), .b(d94_d0_boundary));
`endif
    re3_prom_092 U_D94 (.a({d94_a4_d101_q0, iowr_n, iord_n, BA[1], BA[0]}), .e_n(fdc_prom_cs_n),
                        .d({d94_d7, d94_d6, d94_d5, d94_d4,
                            fdc_prom_we_n, fdc_prom_re_n,
                            d94_d1_d99_a2n, d94_d0_boundary}));

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
    // PIT cascade per the native sheets: D54 horizontal -> D55 vertical;
    // D55.OUT1/VER RTR then passes through D35.9->.8 to FRAME INT/D10.IR5.
    // 1 MHz = D40 QD (the same /16 tap that feeds the D37 latch chain, net LATCH_B); 2 MHz =
    // D40 QC; 1.23 MHz (D57 baud clk0) = the now-guarded D103/D33 /13 loop.
    // Its upstream physical XTAL16M source merge remains a continuity boundary.
    wire clk123m;
    wire pit_hchain, pit_hsync_dsl, pit_vchain, pit_baud, pit_sound;
    pit_8253  U_PIT0 (.A(BA[1:0]), .D(DB), .cs_n(cs_pit0_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(),
                      .clk0(clk1m), .gate0(1'b1), .clk1(clk1m), .gate1(pit_hchain),
                      .clk2(clk1m), .gate2(pit_hchain),
                      .out0(pit_hchain), .out1(), .out2(pit_hsync_dsl));
    pit_8253  U_PIT1 (.A(BA[1:0]), .D(DB), .cs_n(cs_pit1_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(),
                      .clk0(pit_hchain), .gate0(1'b1), .clk1(pit_hsync_dsl), .gate1(pit_vchain),
                      .clk2(pit_hsync_dsl), .gate2(pit_vchain),
                      .out0(pit_vchain), .out1(vert_rtr), .out2());
    pit_8253  U_PIT2 (.A(BA[1:0]), .D(DB), .cs_n(cs_pit2_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(),
                      .clk0(d103_q[3]), .gate0(1'b1), .clk1(clk2m), .gate1(1'b1),
                      .clk2(d103_q[3]), .gate2(1'b1),   // traced: CLK0+CLK2 share 1.23M = D103.QD
                      .out0(pit_baud), .out1(pit_sound), .out2(sync_b_w));   // OUT1 = SOUND beeper; OUT2 = SYNC B. -> D56 (traced)
    wire ser_txd, ser_rts, ser_dtr, ser_rxd, ser_cts_n, ser_dsr_n, ser_syndet, ser_rxrdy, ser_txrdy;
    usart_8251 U_SIO0(.A(BA[0]),   .D(DB), .cs_n(cs_sio0_n), .rd_n(iord_n), .wr_n(iowr_n), .clk(d13_o4),
                      .vss_gnd(1'b0), .vcc_5v(1'b1),
                      .rxc(pit_baud), .txc(pit_baud),
                      .txd(ser_txd), .rts(ser_rts), .dtr(ser_dtr), .rxrdy(ser_rxrdy), .txrdy(ser_txrdy), .syndet(ser_syndet), .txempty(),
                      .rxd(ser_rxd), .cts_n(ser_cts_n), .reset(reset_sys), .dsr_n(ser_dsr_n));
    // ---- serial-port drivers -> X3 connector (К170АП2/УП2 + ЛА18; owner scan img). Buffer the USART
    // serial side out to the RS-232 connector; all off the CPU bus -> boot-safe. D14=SOUT, D32=RTS/DTP,
    // D3=TTL SOUT, D12=OC SOUT, D104=SIN receiver. TxD fans to the SOUT/TTL/OC drivers (same data, diff levels).
    wire s_sout, s_rts, s_dtp, s_ttl, s_ttl_d3, s_oc, s_sin, s_cts, s_dsr, ser_txd_inv;
    ap2_drv U_D14 (.i3(ser_txd), .i2(1'b1),    .o6(s_sout), .o7());
    ap2_drv U_D32 (.i3(ser_rts), .i2(ser_dtr), .o6(s_rts),  .o7(s_dtp));
    wire ir7_sig, ir6_buf, ir6_sig;
    ln2_inv U_D3  (.a(ser_txd), .y(s_ttl_d3),
                   .i13(int7_raw), .o12(ir7_sig), .i1(int6_raw), .o2(ir6_buf),
                   .i3(ppi0_pc[1]), .o4(d3_o4_d6_a6),
                   .i5(ppi0_pc[0]), .o6(d3_o6_d6_a5),
                   .i9(ser_txd), .o8(ser_txd_inv));
    net_boundary U_W20 (.a(s_ttl_d3), .b(s_ttl));
    // S4 selects PIC IR6 between buffered -INT6 and USART SYNDET. The photographed
    // build defaults to the external-interrupt throw for simulation.
    spdt_switch U_S4 (.syndet_throw(ser_syndet), .int6_throw(ir6_buf), .ir6_common(ir6_sig));
    la18_oc U_D12 (.i1(ser_txd_inv), .i2(ser_txd_inv), .o3(s_oc));
    wire d104_x4_in_boundary, d104_x4_out_boundary;
    up2_rcv U_D104(.sin_in(s_sin), .sin_out(ser_rxd),
                   .cts_in(s_cts), .cts_out(ser_cts_n),
                   .dsr_in(s_dsr), .dsr_out(ser_dsr_n),
                   .x4_in(d104_x4_in_boundary), .x4_out(d104_x4_out_boundary));
    serial_conn U_X3 (.pullup_io(), .aux2(s_oc), .ttl_sout(s_ttl), .sin(s_sin),
                      .cts(s_cts), .dsr(s_dsr), .aux7(), .aux8(),
                      .sout(s_sout), .rts(s_rts), .dtp(s_dtp), .oc_sout(s_oc));
`ifdef YOSYS
    wire fdc_model_cs_n = cs_fdc_n;
    wire fdc_model_re_n = iord_n;
    wire fdc_model_we_n = iowr_n;
`else
    // Runnable behavioral core consumes the physical .092 PROM strobes. Only
    // the explicitly guarded upstream D94 sources above remain functional fits.
    wire fdc_model_cs_n = fdc_prom_cs_n;
    wire fdc_model_re_n = fdc_prom_re_n;
    wire fdc_model_we_n = fdc_prom_we_n;
`endif
    // Default functional core remains on logical DB. Two opt-in regressions use
    // the explicitly non-physical inverting firmware-profile adjunct above.
`ifdef FDC_VA87_CS_QUALIFIED
`define JUKU_FDC_DATA_BUS fdc_profile_dal
`elsif FDC_VA87_ALWAYS_ENABLED
`define JUKU_FDC_DATA_BUS fdc_profile_dal
`else
`define JUKU_FDC_DATA_BUS DB
`endif
    fdc_1793  U_FDC  (.A(BA[1:0]), .D(`JUKU_FDC_DATA_BUS), .cs_n(fdc_model_cs_n),  .rd_n(fdc_model_re_n), .wr_n(fdc_model_we_n),
                      .nc_back_bias(1'bz), .vss_gnd(1'b0), .vcc_5v(1'b1), .vdd_12v(1'b1),
                      .mr_n(1'b1), .clk(sclk_i), .dden(ppi0_pc[4]), .motor_on(ppi0_pc[2]), .side(ppi0_pc[6]),
                      .step(), .dirc(), .early(), .late(), .test(1'b1), .hlt(1'b1),
                      .rg(), .rclk(1'b0), .raw_read(1'b1), .hld(), .tg43(), .wg(), .wdata(),
                      .ready(1'b1), .wf_vfoe(), .tr00(1'b0), .index(1'b0), .wprt(1'b0),
                      .drq(fdc_drq), .intrq(fdc_intrq));
`undef JUKU_FDC_DATA_BUS
    wire pic_sp_en = 1'b1; // sheet-1 A-rail strap: standalone/master 8259
`ifdef YOSYS
    // Exact sheet 3 routes raw DRQ/INTRQ through D28/D96. The downstream
    // sheet-1 joins to PIC IR0/IR1 are not yet known, so retain distinct pins.
    wire pic_fdc_drq_boundary, pic_fdc_intrq_boundary;
`else
    wire pic_fdc_drq_boundary = fdc_drq;
    wire pic_fdc_intrq_boundary = fdc_intrq;
`endif
    pic_8259  U_PIC  (.A(BA[0]),   .D(DB), .cs_n(cs_pic_n),  .rd_n(iord_n), .wr_n(iowr_n),
                      .vss_gnd(1'b0), .vcc_5v(1'b1),
                      .ir7(ir7_sig), .ir6(ir6_sig), .ir5(frame_int), .ir3(ser_txrdy), .ir2(ser_rxrdy), .ir1(pic_fdc_drq_boundary), .ir0(pic_fdc_intrq_boundary),
                      .cas0(), .cas1(), .cas2(), .sp_en(pic_sp_en), .intr(intr), .inta_n(inta_n));
    // 8259 interrupt/vector behavior (sim adjunct to U_PIC; unmapped -> LVS-invisible). Drives
    // the shared INT net (pic_8259 leaves it z) and injects the CALL vector during INTA.
    intr_ctl  U_INTR (.osc(sclk_i), .dbin(dbin), .inta_n(inta_n), .iowr_n(iowr_n),
                      .cs_pic_n(cs_pic_n), .a0(BA[0]), .frame_tick(frame_tick), .DB(DB), .intr(intr));

endmodule
`default_nettype wire
