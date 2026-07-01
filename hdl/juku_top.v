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
    ln1_osc   U_D59 (.xin(clk), .osc(osc_clk));
    ct16_ctr  U_D40 (.clk(osc_clk), .r_n(1'b1), .ep(1'b1), .et(1'b1), .pe_n(1'b1), .d(4'b0), .q(d40_q), .co());
    la3_gate  U_D39 (.a(d40_q[1]), .b(d40_q[0]), .y(d39_y));  // pin13(B)<-D40.Q0(14), pin12(A)<-D40.Q1(13) [traced]
    ln1_dual  U_D33 (.i9(1'b0), .i5(d40_q[2]), .o8(clkg_d33), .o6(d33_o6));  // pin8->D38.9; pin5<-D40.Q2, pin6->D36.4
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
    // STSTB = SYNC-qualified strobe: the discrete clock subsystem makes STSTB from SYNC (exact gate
    // un-traced -> feed SYNC into one of D38's deferred inputs [assumed]). With clkg_d33=d39_y=1 and
    // i3=1, ststb_n = ~sync -> the 8238 latches the status byte at SYNC's rising edge (T1 start).
    la1_gate  U_D38 (.i0(clkg_d33), .i1(sync), .i2(1'b1), .i3(d39_y), .y(ststb_n));
    // D38 (ЛА1) STB gate [traced 2026-07]: pin9<-D33.8(clkg_d33), pin12<-SYNC, pin10<-D39.11(d39_y),
    // pin13 tied high (4th NAND leg). ststb_n = ~(clkg_d33 & sync & d39_y) -- SYNC-qualified strobe.

    sysctl_8238 U_SYS (.D(D), .DB(DB), .dbin(dbin), .wr_n(wr_n), .hlda(hlda),
                       .ststb_n(ststb_n), .busen_n(busen_n),
                       .memr_n(memr_n), .memw_n(memw_n),
                       .iord_n(iord_n), .iowr_n(iowr_n), .inta_n(inta_n));

    buf_8286  U_BUFL (.Ain(A[7:0]),  .Aout(BA[7:0]),  .oe_n(buf_oe_n), .t(buf_t));
    buf_8286  U_BUFH (.Ain(A[15:8]), .Aout(BA[15:8]), .oe_n(buf_oe_n), .t(buf_t));

    // ============ expansion/backplane interface (Phase B, sheet 1 -- bus-interface.md) ============
    // D29 (ВА86) buffers the internal bus-command strobes out to the Multibus-style expansion
    // connector. t=1/oe=0 -> A-side reads memr_n/memw_n/iord_n/iowr_n as high-Z (never drives them
    // back -> boot-safe); B-side drives the connector command pins -MRC/-MWC/-IORC/-IOWC. A-side
    // spare inputs (real -IO/M / -AMWC sources) not yet modeled -> tied inactive (boundary).
    wire mrc_n, mwc_n, iorc_n, iowc_n; wire [3:0] d29_aout_hi;
    wire [3:0] d29_ain_hi = 4'b1111;   // A-side spare inputs (unmodeled -IO/M / -AMWC sources) inactive
    va86_out U_D29 (.Ain({d29_ain_hi, iowr_n, iord_n, memw_n, memr_n}),
                    .Aout({d29_aout_hi, iowc_n, iorc_n, mwc_n, mrc_n}), .oe_n(1'b0), .t(1'b1));
    // D24 (ВА87) buffers the system data bus DB out to the connector data pins -DAT0..-DAT7
    // (inverting). One-way: A-side reads DB (never drives it -> boot-safe); B-side drives the connector.
    wire [7:0] dat;
    va87_out U_D24 (.Ain(DB), .Aout(dat), .oe_n(1'b0), .t(1'b1));
    expansion_conn U_X1 (.mrc_n(mrc_n), .mwc_n(mwc_n), .iorc_n(iorc_n), .iowc_n(iowc_n), .dat(dat));

    // ============ I/O chip-select decode: К555ИД7 (74138) ============
    // A2:A0 select group, I/ORD & I/OWR enable; Y0..Y7 -> the chip-selects.
    // (refdes placeholder DID7; decode wiring is the standard 74138 pattern [assumed])
    io_dec138 U_DID7 (.a(BA[2]), .b(BA[3]), .c(BA[4]), .g1(1'b1), .g2a_n(iord_n), .g2b_n(iowr_n),
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

    // DRAM: К565РУ5 64Kx1 array. 32 sockets on the board (4 banks x 8), only 8 POPULATED
    // = one byte-bank bit-sliced D60..D67 = the real 64KB RAM. The other 24 sockets are
    // bank-expansion (up to 256KB), unpopulated. There is NO separate video plane -- the
    // video reads this same bank via the КП14 µP/video mux. Address is MULTIPLEXED (MA);
    // RAS/CAS from the D53 ИД7 decoder + АГ3 timing (see docs/transcription/dram-video-timing.md).
    wire [7:0] MA;                 // muxed row/col address  (from address mux)
    wire ras_n, cas_n;             // (from RAM control / refresh)
    wire [15:0] vid_addr;          // video raster address into the framebuffer (РУ5 2nd port)
    wire [7:0]  vbyte;             // framebuffer byte at vid_addr (from the 8 РУ5 video reads)
    dram_64kx1 U_D60 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[0]), .do_(DB[0]), .va(vid_addr), .vq(vbyte[0]));
    dram_64kx1 U_D61 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[1]), .do_(DB[1]), .va(vid_addr), .vq(vbyte[1]));
    dram_64kx1 U_D62 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[2]), .do_(DB[2]), .va(vid_addr), .vq(vbyte[2]));
    dram_64kx1 U_D63 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[3]), .do_(DB[3]), .va(vid_addr), .vq(vbyte[3]));
    dram_64kx1 U_D64 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[4]), .do_(DB[4]), .va(vid_addr), .vq(vbyte[4]));
    dram_64kx1 U_D65 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[5]), .do_(DB[5]), .va(vid_addr), .vq(vbyte[5]));
    dram_64kx1 U_D66 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[6]), .do_(DB[6]), .va(vid_addr), .vq(vbyte[6]));
    dram_64kx1 U_D67 (.sclk(sclk_i), .ma(MA), .ras_n(ras_n), .cas_n(cas_n), .we_n(memw_n), .di(DB[7]), .do_(DB[7]), .va(vid_addr), .vq(vbyte[7]));
    // (D68-D91 = the other 3 banks' sockets, unpopulated -- added in Phase B for the PCB.)

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
    rascas_dec U_D53 (.a(ram_sel_n), .b(phi1), .c(phi2), .g(mem_active), .y_n({rc_nc, cas_n, ras_n}));

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
    la3_gate U_D37 (.a(d42_q), .b(d42_q), .y(d37_out));

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
    usart_8251 U_SIO0(.A(BA[0]),   .D(DB), .cs_n(cs_sio0_n), .rd_n(iord_n), .wr_n(iowr_n), .clk());
    fdc_1793  U_FDC  (.A(BA[1:0]), .D(DB), .cs_n(cs_fdc_n),  .rd_n(iord_n), .wr_n(iowr_n), .clk());
    pic_8259  U_PIC  (.A(BA[0]),   .D(DB), .cs_n(cs_pic_n),  .rd_n(iord_n), .wr_n(iowr_n),
                      .intr(intr), .inta_n(inta_n));
    // 8259 interrupt/vector behavior (sim adjunct to U_PIC; unmapped -> LVS-invisible). Drives
    // the shared INT net (pic_8259 leaves it z) and injects the CALL vector during INTA.
    intr_ctl  U_INTR (.osc(sclk_i), .dbin(dbin), .inta_n(inta_n), .iowr_n(iowr_n),
                      .cs_pic_n(cs_pic_n), .a0(BA[0]), .frame_tick(frame_tick), .DB(DB), .intr(intr));

endmodule
`default_nettype wire
