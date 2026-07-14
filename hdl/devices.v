// Device modules for juku_top.v. Port lists are the LVS contract; bodies are being
// functionalized (merge steps 1-3) so the LVS-checked juku_top.v itself boots.
`timescale 1ns/100ps
`default_nettype none

// ---- i8080A CPU (КР580ВМ80А): vm80a die-replica core ----
// Merge step 2: real core (was a stub). `osc` is the die-replica's high-speed sampling clock --
// a SIM artifact, NOT a pin on the real КР580ВМ80А (which derives timing from Φ1/Φ2 internally).
// In juku_top it is wired to a sim-only top input that connects to nothing else, so the LVS
// (which only compares nets with >=2 mapped-chip endpoints) drops it -- no spurious board net.
// vm80a is undefined in the LVS yosys read (devices.v + juku_top.v only) -> harmlessly blackboxed;
// the simulator compiles hdl/vendor/vm80a.v for the real boot.
module cpu_8080 (
    input  wire        sclk,       // SIM-ONLY die-replica sampling clock (distinct name from the
                                   // real crystal oscillator D59.OSC, so the LVS allowlist can drop
                                   // this without touching the real OSC net)
    input  wire        phi1, phi2, ready, reset, hold, intr,
    input  wire        vss_gnd, vbb_m5v, vcc_5v, vdd_12v, // physical supplies; logic body is voltage-abstracted
    output wire [15:0] A,
    inout  wire [7:0]  D,        // multiplexed data + status byte
    output wire        dbin, wr_n, sync, hlda, inte, wait_o
);
    vm80a u (.pin_clk(sclk), .pin_f1(phi1), .pin_f2(phi2), .pin_reset(reset),
             .pin_a(A), .pin_d(D), .pin_hold(hold), .pin_hlda(hlda), .pin_ready(ready),
             .pin_wait(wait_o), .pin_int(intr), .pin_inte(inte), .pin_sync(sync),
             .pin_dbin(dbin), .pin_wr_n(wr_n));
endmodule

// NOTE: no clk_8224 module — this board generates the clock discretely
// (crystal + ЛН1 oscillator D59 + phase gates D33/D35/D36/D38). To be modeled
// as its own clock subsystem; the CPU core treats Φ1/Φ2/RESET/READY as boundary nets.

// ---- i8238 system controller (КР580ВК38) ----
module sysctl_8238 (
    input  wire       vss_gnd, vcc_5v,
    inout  wire [7:0] D,         // CPU data/status side
    inout  wire [7:0] DB,        // buffered system data bus side
    input  wire       dbin, wr_n, hlda, ststb_n, busen_n,
    output wire       memr_n, memw_n, iord_n, iowr_n, inta_n
);
    // Merge step 2: real 8238 (was a stub). Latch the CPU status byte on STSTB, derive the four
    // command strobes from the status bits + DBIN/WR, and bridge D <-> DB (gated by BUSEN).
    // Status bits: [7]=MEMR? no -> [6]=INP, [4]=OUT, [0]=INTA, MEMR = read & !INP & !INTA.
    reg [7:0] status = 0;
    always @(negedge ststb_n) status <= D;            // STSTB strobe latches the status byte
    assign memr_n = ~(dbin  & ~status[6] & ~status[0]);
    assign iord_n = ~(dbin  &  status[6]);            // INP
    assign memw_n = ~(~wr_n & ~status[4]);            // memory write (not OUT)
    assign iowr_n = ~(~wr_n &  status[4]);            // OUT
    assign inta_n = ~(dbin  &  status[0]);            // INTA
    assign D  = (dbin  & ~busen_n) ? DB : 8'bz;       // read:  system bus -> CPU
    assign DB = (~wr_n & ~busen_n) ? D  : 8'bz;       // write: CPU -> system bus
endmodule

// ---- i8286 octal bus transceiver (КР580ВА86), used as address buffer ----
// Functional (merge step 1): t selects direction, oe_n enables. As an address buffer the board
// wires t=1, oe_n=0 (CPU A -> buffered BA), so Aout follows Ain. (Ain side undriven: CPU drives it.)
module buf_8286 (
    inout wire [7:0] Ain, Aout,
    input wire       oe_n, t
);
    assign Aout = (~oe_n &  t) ? Ain : 8'bz;
    assign Ain  = (~oe_n & ~t) ? Aout : 8'bz;
endmodule

// ВА86 modeled ONE-WAY (internal -> connector) for the backplane transceivers: the expansion cards
// don't drive back in the digital twin, so the A-side stays a pure INPUT and never drives the internal
// strobe/bus nets (boot-safe -- unlike the inout buf_8286, whose z-assign taps those nets). LVS
// connectivity is identical to a full ВА86 (same AIN/AOUT/OE_N/T pins).
module va86_out (input wire [7:0] Ain, input wire oe_n, t, output wire [7:0] Aout);
    assign Aout = (~oe_n & t) ? Ain : 8'bz;
endmodule
// ВА87 (8287) = the INVERTING octal transceiver; same pinout as ВА86, output = ~input. One-way
// (internal -> connector) for the backplane, like va86_out. Inversion is a boundary detail (the
// connector far side is off-board) -- it doesn't affect the boot or LVS net membership.
module va87_out (input wire [7:0] Ain, input wire oe_n, t, output wire [7:0] Aout);
    assign Aout = (~oe_n & t) ? ~Ain : 8'bz;
endmodule

// Expansion backplane connector (Multibus-style card slots). A BOUNDARY component: its far side is
// the off-board cards, so it carries no logic -- it exists so the transceiver->connector nets have a
// 2nd endpoint (LVS forbids 1-node nets). Stage-1 pins = the D29 bus-command signals; grows as more
// backplane transceivers (D23 addr, D24 data, D25 control) are wired. Endpoint truth lives in board JSON.
// К565РУ5 socket, UNPOPULATED (banks 1-3 of the 4-bank DRAM array). The sockets ARE on the board and
// wired (shared MA/CAS/WE + per-bit DIN/DOUT, per-row RAS), but no chip is installed -> modelled as a
// passive footprint: pins on the buses, NO logic (never drives DB/WD) -> boot-safe. Same RU5 pinmap as
// the populated row.
module ru5_socket (input wire [7:0] ma, input wire ras_n, cas_n, we_n, di,
                   input wire nc_vbb_option, vcc_option, vss_gnd, inout wire do_);
endmodule

// К580ИР82 (8282) octal latch. Here (D58) it's the DRAM WRITE-DATA latch: it latches the system data
// bus and drives the РУ5 DIN bus, holding the write data stable across the CAS/WE window -- the real
// reason the DRAM captures a settled value (our sim compensated by sampling writes on the master clock;
// D58 is the chip that does it in hardware). Modeled TRANSPARENT (q=d) so the RAM sees the same write
// data -> byte-identical boot; STB/OE are wired for LVS connectivity only.
module ir82_latch (input wire [7:0] d, input wire stb, oe_n, output wire [7:0] q);
    // RAM READ-data latch (sheet-2): D <- РУ5 DO bus, Q -> DB, OE = D37 read strobe.
    // Latch function still transparent (stb boundary); OE gating is real.
    assign q = oe_n ? 8'hzz : d;
endmodule

module expansion_conn (inout wire inhib_n, cclck, iom_n, mwc_n, mrc_n, amwc_n, iorc_n, iowc_n, wreq_n,
                       inout wire int7_raw, int6_raw,
                       inout wire [7:0] dat,
                       inout wire [7:0] adr_lo, inout wire [7:0] adr_hi);  // adr_lo[i]=-ADRi, adr_hi[i]=-ADR(8+i)
endmodule

// ---- I/O port decoder (board glue: 74xx138-style) ----
module io_decode (
    input  wire [7:0] A,
    input  wire       ior_n, iow_n,
    output wire       cs_pic_n, cs_ppi0_n, cs_sio0_n, cs_ppi1_n,
    output wire       cs_pit0_n, cs_pit1_n, cs_pit2_n, cs_fdc_n
);
    wire active = ~(ior_n & iow_n);          // some I/O cycle in progress
    wire [2:0] grp = A[4:2];                  // chip group select
    assign cs_pic_n  = ~(active & (grp == 3'd0) & (A[7:5] == 0)); // 0x00..0x03
    assign cs_ppi0_n = ~(active & (grp == 3'd1) & (A[7:5] == 0)); // 0x04..0x07
    assign cs_sio0_n = ~(active & (grp == 3'd2) & (A[7:5] == 0)); // 0x08..0x0B
    assign cs_ppi1_n = ~(active & (grp == 3'd3) & (A[7:5] == 0)); // 0x0C..0x0F
    assign cs_pit0_n = ~(active & (grp == 3'd4) & (A[7:5] == 0)); // 0x10..0x13
    assign cs_pit1_n = ~(active & (grp == 3'd5) & (A[7:5] == 0)); // 0x14..0x17
    assign cs_pit2_n = ~(active & (grp == 3'd6) & (A[7:5] == 0)); // 0x18..0x1B
    assign cs_fdc_n  = ~(active & (grp == 3'd7) & (A[7:5] == 0)); // 0x1C..0x1F
endmodule

// ---- memory bank decode: 4-mode ROM/RAM overlay (PPI0 PortC[1:0]) ----
module mem_decode (
    input  wire [15:0] A,
    input  wire        memr_n, memw_n,
    input  wire [1:0]  mode,
    output wire        rom_oe_n, ram_oe_n, ram_we_n
);
    // mode0: ROM 0x0000-0x3FFF ; mode1/2: ROM 0xD800-0xFFFF ; mode3: all RAM
    wire rom_lo = (mode == 2'd0) && (A <= 16'h3FFF);
    wire rom_hi = (mode == 2'd1 || mode == 2'd2) && (A >= 16'hD800);
    wire rom_sel = rom_lo || rom_hi;
    assign rom_oe_n = ~(rom_sel & ~memr_n);
    assign ram_oe_n = ~(~rom_sel & ~memr_n);
    assign ram_we_n = ~(~rom_sel & ~memw_n);   // writes under ROM overlay are dropped
endmodule

// ---- memory map decoder: К556РТ4 256x4 bipolar PROM (D6) ----
// Traced (crop bios_hunt1): address inputs = BA15..BA11 on pins 5,6,7,4,3 PLUS the mode bundle
// on pins 2,1,15 (tags 1,2,3 <- PPI Port C bits) -- the banking mode enters the PROM as ADDRESS,
// not through the V enable. V1/V2 (13,14) feed unread; modeled always-enabled (v_en_n ignored).
// Columns (traced): D0/12 = ROM_N -> D8.E_N pager enable; D1/11 = RAM_N -> sheet 2;
// D2/10 = REV -> D9 io-decode G2A/G2B region enable; D3/9 = "-RAMOUTEN" -> D13 Schmitt.
// The validated physical `.038` table is classified in docs/d6-physical-decode.md.
// On the `.009` board pins 11/12 are one measured open-collector conductor, so
// their older-sheet RAM_N/ROM_N names describe pin roles, not independent nets.
module decode_prom (input wire [7:0] a, input wire v_en_n,
                    output wire rom_n, ram_n, rev, roe_n);
    // Validated physical D6 `.038` table. Address bit order is the actual RT4
    // pin order: a[0:7] = pins 5,6,7,4,3,2,1,15 =
    // BA15,BA14,BA13,BA12,BA11,PC2,PC3,PC4.
`ifdef YOSYS
    wire [3:0] raw = 4'h0; // contents are irrelevant to structural LVS
`else
    reg [7:0] prom [0:255];
    initial $readmemh("ref/physical-proms/validated/d6_038.raw.hex", prom);
    wire [3:0] raw = prom[a][3:0];
`endif
    assign {roe_n, rev, ram_n, rom_n} = v_en_n ? 4'hF : raw;
endmodule

// Functional memory-map oracle used only by runnable simulation. The physical
// `.009` D6 pins 11/12 are joined and their downstream timing topology is not
// yet complete enough to reproduce the established EKTA/EKDOS execution path.
// Keep this behavior separate from `decode_prom`: it is neither PROM content
// nor an LVS-visible claim about the original board.
module decode_prom_functional (input wire [15:11] ba, input wire pc2,
                               output wire rom_n, ram_n, rev, roe_n);
    wire rom_region = ~pc2 ? (ba[15:14] == 2'b00) : (ba >= 5'b11011);
    assign rom_n = ~rom_region;
    assign ram_n = rom_region;
    assign rev   = ~(ba[15:13] == 3'b000);
    assign roe_n = 1'b0;
endmodule

// D2 КР556РТ4 `.037` bus/READY PROM. Three preserved owner captures agree at
// all 256 addresses (eight samples/address, zero unstable rows), including a
// full power-cycled read. All four physical output pins read identically.
module wait_prom_037 (input wire [7:0] a, input wire v1_n, v2_n,
                      output wire [3:0] d);
`ifdef YOSYS
    wire [3:0] raw = 4'h0; // contents are irrelevant to structural LVS
`else
    reg [7:0] prom [0:255];
    initial $readmemh("ref/physical-proms/validated/d2_037.raw.hex", prom);
    wire [3:0] raw = prom[a][3:0];
`endif
    assign d = (~v1_n && ~v2_n) ? raw : 4'hF;
endmodule

// ---- ЛА3 NAND gate section (D7) gating the PROM enable ----
module la3_gate (input wire a, b, a2, b2, a3, b3, a4, b4, output wire y, y2, y3, y4);   // the 4 ЛА3 sections
    assign y = ~(a & b);
    assign y2 = ~(a2 & b2);   // second section (D37: 1,2->3 LATCH gate; D39: 9,10->8), sheet-2
    assign y3 = ~(a3 & b3);   // third section (D37: 5,4->6; D39: 1,2->3 mem-cycle gate), sheet-2
    assign y4 = ~(a4 & b4);   // fourth section (D39: 4,5->6 -> D52 B/A video/µP address select), sheet-2
endmodule

// D92 К555ЛЕ4 (74LS27-class triple 3-input NOR).  The native sheet-2
// symbol uses the standard section order 1,2,13->12; 3,4,5->6; and
// 9,10,11->8.  D92 first qualifies RAM reads, the second qualifies RAM
// writes, and the third combines those two results into the no-access input
// of D39.5.
module le4_nor3 (input wire a1, b1, c1, input wire a2, b2, c2,
                 input wire a3, b3, c3, output wire y1, y2, y3);
    assign y1 = ~(a1 | b1 | c1);
    assign y2 = ~(a2 | b2 | c2);
    assign y3 = ~(a3 | b3 | c3);
endmodule

// ---- EPROM 8Kx8 (2764-class, D15/D16 populated) ----
// The 16KB ekta37 BIOS spans D15 (low 8K, HALF=0) + D16 (high 8K, HALF=1), each with its own CE
// from the decode PROM. oe_n is the read strobe (MEMR). Sample-and-hold: latch the byte at the
// read strobe and hold it through DBIN (8080 tOS1/tOS2 -- a combinational multi-hop drive corrupts
// vm80a's fixed-phase capture; this is a simulator timing accommodation).
// EPROM socket, UNPOPULATED (6 of the 8 ROM sockets: only D15/D16 hold the 16KB BIOS). Wired to the
// shared address/data + OE buses; no chip installed -> passive footprint (never drives DB) -> boot-safe.
// Per-socket CS comes from the ROM bank decode (not yet traced -> CS left as a documented gap). Same
// EPROM8K pinmap as the populated pair.
module eprom_socket (input wire [12:0] a, inout wire [7:0] d, input wire cs_n, oe_n);
endmodule

module exprom_8k (input wire [12:0] a, inout wire [7:0] d, input wire cs_n, oe_n);
    reg [7:0] rom [0:8191]; reg [1023:0] f; integer loaded = 0;
`ifndef YOSYS
    initial begin
        if ($value$plusargs("cart=%s", f)) begin
            $readmemh(f, rom);
            loaded = 1;
        end
    end
`endif
    reg [7:0] held;
    always @(negedge oe_n) if (loaded && ~cs_n) held <= rom[a];
    assign d = (loaded && ~cs_n & ~oe_n) ? held : 8'bz;
endmodule

module eprom_8k #(parameter HALF = 0) (input wire [12:0] a, inout wire [7:0] d, input wire cs_n, oe_n);
    reg [7:0] rom [0:16383]; reg [1023:0] f;
`ifndef YOSYS
    initial begin    // sim-only ROM load; yosys (LVS) defines YOSYS and skips this (body = memory for connectivity)
        if (!$value$plusargs("rom=%s", f)) f = "hdl/sim/ekta37.hex";
        $readmemh(f, rom);
    end
`endif
    reg [7:0] held;
    always @(negedge oe_n) if (~cs_n) held <= rom[{HALF[0], a}];   // latch at the read strobe
    assign d = (~cs_n & ~oe_n) ? held : 8'bz;
endmodule

// ===== clock subsystem (discrete; replaces the non-existent 8224) =====
module ln1_osc   (input wire sclk, xin, input wire i13, i11, i3, i5, i9,
                  output wire osc, o12, o10, o4, o6, o8);   // D59 ЛН1 complete hex-inverter package
    // sclk is the simulation drive only. Physical pin 1 (xin) is retained as the
    // D59.8 feedback landing; the analog Z1/C73/R31/R32 loop cannot be synthesized.
    assign osc = sclk;  // functional clock value; real OSC copper remains pin 2
    assign o12 = ~i13;  // section 13->12 = LOAD   (D38.6 -> D59.13, sheet-2)
    assign o10 = ~i11;  // section 11->10 = D39.8 -> D59.11 chain (sheet-2)
    assign o4  = ~i3;   // section 3->4 = PST CLK (3rd ring section; buffered osc out -> D44.UP)
    assign o6  = ~i5;   // physical section 5->6; board destination unresolved
    assign o8  = ~i9;   // section 9->8 returns through R31 to physical pin 1
endmodule
// D35 ЛН5 phase generator. Merge step 3: the discrete clock mesh feeding `osc` is an un-traced
// boundary (D36/D33/D40 gate inputs deferred), so realize the КР580 2-phase clock to functional
// INTENT here -- a non-overlapping Φ1/Φ2. This is a sim clock: it only sets the simulated VALUE;
// the D35->CPU net wiring (what LVS compares) is unchanged, so LVS stays IN SYNC.
module clk_phase (input wire osc, phsel, i1, i3, i5, i9,
                  output reg phi1, phi2, phi2ttl, output wire o2, o4, o6, o8);
    assign o2 = ~i1; assign o4 = ~i3; assign o6 = ~i5; assign o8 = ~i9;
    // osc = clkg_d36 (D36.6 -> D35.11, the LVS-visible mesh input). phsel = a clean divider phase bit
    // (d40_q[1], sim-only): the real D35 ЛН5 shapes Φ1/Φ2 by inverting the mesh output through RC
    // (R37/R36 360Ω + the CPU clock caps) -- an analog waveform not derivable from the netlist. So for
    // the SELF-CLOCKING sim we lock a valid non-overlapping two-phase to the divider phase directly.
    // Forced-clock boot tbs override phi1/phi2, so this body only takes effect in self-clocking mode.
    always @* begin phi1 = ~phsel; phi2 = phsel; phi2ttl = phsel; end
endmodule
module stb_gen   (input wire osc, output wire stb);                  // D38 (legacy stub, unused)
    assign stb = 1'bz; endmodule
// clock divider + gate mesh (board JSON provenance). Z1 -> D59 osc ->
// D40 divider -> D33/D39/D36 gates -> D38 (ЛА1) = STB and D35 (ЛН5) = Φ1/Φ2.
module ct16_ctr  (input wire clk, r_n, ep, et, pe_n, input wire [3:0] d,  // D40 СТ16 (74161-class)
                  output wire [3:0] q, output wire co);
    // Functional 4-bit synchronous counter (was a z-stub). Read as -lib blackbox for LVS, so the
    // body is sim-only. Frozen at 0 when clk is static (the boot-tb ties D59.xin=0 -> osc_clk=0).
    reg [3:0] cnt = 4'b0;
    always @(posedge clk or negedge r_n)
        if      (!r_n)     cnt <= 4'b0;
        else if (!pe_n)    cnt <= d;
        else if (ep & et)  cnt <= cnt + 1'b1;
    assign q  = cnt;
    assign co = et & (&cnt);
endmodule
module ln1_dual  (input wire i9, i5, i13, i3, i11, i1, output wire o8, o6, o12, o4, o10, o2);   // D33 ЛН1: used inverter sections
    assign o8 = ~i9;    // section pin 9 -> pin 8  = clkg_d33 -> D38.9  (pin 9 <- C6/R46 osc RC = boundary)
    assign o6 = ~i5;    // section pin 5 -> pin 6  = D36.4  (pin 5 <- D40.Q2, traced 2026-07)
    assign o12 = ~i13;  // section 13->12 = LATCH  (D37.3 -> D33.13, sheet-2)
    assign o4  = ~i3;   // section 3->4: -MRD -> D37.5 (RF/video-mix qualifier, sheet-2 bottom)
    assign o10 = ~i11;  // section 11->10: D36.3 -> D36.10 CAS strobe-chain delay leg (bite-2)
    assign o2  = ~i1;   // section 1->2: D103.CO -> LD reload loop (the /13 preset divider, traced s2_d103)
endmodule
// D36 К531ЛА12 (SN74S37-compatible quad 2-input NAND, high drive). Section 4,5->6 = clock mesh (traced 2026-07); bite-2
// added: 1,2->3 (pin1 taps rail 15 = CAS, pin2 <- rail 17) -> D33.11; 9,10->8 (-> rail 16); 12,13->11
// (inputs tied) -> R57 -> rail 15 = the populated-bank CAS driver.
module la12_gate (input wire a, b, a2, b2, a3, b3, a4, b4, output wire y, y2, y3, y4);
    assign y  = ~(a & b);
    assign y2 = ~(a2 & b2);
    assign y3 = ~(a3 & b3);
    assign y4 = ~(a4 & b4);
endmodule
// Net-boundary link: a series resistor or an unresolved-source junction on the real board. Passes
// the simulated value through unchanged, but as a -lib blackbox cell it keeps the two sides SEPARATE
// NETS for LVS -- the board netlist has the series part / unknown feed there, the sim does not.
module net_boundary (input wire a, output wire b); assign b = a; endmodule
// S4 ВДМ1-2 SPDT interrupt selector. The photographed build is simulated in
// the external-INT6 position; reading this file as a -lib cell keeps all three
// switch terminals as separate LVS-visible nets.
module spdt_switch (input wire syndet_throw, int6_throw, output wire ir6_common);
    assign ir6_common = int6_throw;
endmodule
// К555ТЛ2 hex Schmitt INVERTER (74LS14; census ВП p.3 x1 + drawn D13 symbol: 1-in/1-out with
// inversion = hex-inverter sections, NOT the earlier dual-4-NAND ТЛ1-shaped stand-in).
// D13 (Sheet-1): section 1->2 = the RAMOUTEN driver (in <- D6.9 "-RAMOUTEN" rail, out -> sheet-2
// D37.4, export "(2)" code 12); section 5->6 = RESIN Schmitt -> RES (boundary).
module tl2_hex (input wire i1, i3, i5, i9, i11, i13, output wire o2, o4, o6, o8, o10, o12);
    assign o2  = ~i1;
    assign o4  = ~i3;
    assign o6  = ~i5;
    assign o8  = ~i9;
    assign o10 = ~i11;
    assign o12 = ~i13;
endmodule
module la1_gate  (input wire i0, i1, i2, i3, i4, i5, i6, i7, output wire y, y2);   // both ЛА1 sections
    assign y = ~(i0 & i1 & i2 & i3);
    assign y2 = ~(i4 & i5 & i6 & i7);   // D38 second section (5,4,2,1 -> 6) = LOAD gate, sheet-2
endmodule

// ===== I/O chip-select decoder: К555ИД7 (74138) =====
// Functional (merge step 1): standard 1-of-8 active-low decode, enabled by g1 & !(g2a_n|g2b_n).
// On the board g2a_n/g2b_n = iord_n/iowr_n (enable on either strobe = the documented strobe-OR intent).
// D9 ИД7 takes its selects from the address rails; D8 is the separate РЕ3
// ROM-socket pager. Its validated physical `.039` table is implemented below.
module io_dec138 (input wire a, b, c, g1, g2a_n, g2b_n, output wire [7:0] y_n);
    // selects = A10/A11/A12 rails (sheet-1 rail-code table) = IO port bits 2-4 via the 8080's
    // A15-8 port mirror -- the REAL decode path (sim-only sa/sb/sc retired 2026-07).
    // REAL 74138 enable (traced 2026-07): G1 <- RC-deglitched strobe-NAND (D7.11 via R17/C99),
    // G2A_N+G2B_N <- REV region rail. en = G1 & !G2A & !G2B -- the genuine chip equation.
    wire en = g1 & ~g2a_n & ~g2b_n;
    assign y_n = en ? ~(8'b1 << {c, b, a}) : 8'hFF;
endmodule
// D8 К155РЕ3 (32x8 fusible PROM, programming drawing ДГШ5.106.039): the ROM-socket pager.
// Traced sheet-1: ALL EIGHT socket CEs hang on D8 via the R21-R28 group line (tags D4..D7 ->
// D15..D18, D0..D3 -> D19..D22), and E_N <- D6.ROM_N (mode-aware "some ROM responds" region).
module re3_prom (input wire [4:0] a, input wire e_n, output reg [7:0] d);
    // PHYSICAL CONTENT: three matching reads of the board's .039 part, including a
    // power-cycled read. The former MAME-derived reconstruction is retained only as
    // historical evidence; it differs at rows 08-1A and no longer drives this model.
    always @* begin
        if (e_n)              d = 8'hFF;
        else casez (a)
            5'b000??:         d = 8'hEF;   // 00-03: D4 -> D15 (BIOS low 8K, 0000-1FFF)
            5'b001??:         d = 8'hDF;   // 04-07: D5 -> D16 (BIOS high 8K, 2000-3FFF)
            5'b110??:         d = 8'hEF;   // 18-1B: D4 -> D15
            5'b111??:         d = 8'hDF;   // 1C-1F: E000-FFFF -> D16
            default:          d = 8'hFF;   // 08-17: all socket selects released
        endcase
    end
endmodule

// ===== video address generation + address mux (closes РУ5 MA/RAS/CAS) =====
// D44-47 ИЕ7 (К155ИЕ7 = 74193-class): 4-bit binary up-counter. Cascades via CO (carry-out
// pulses at terminal count 0xF) to form the video raster address. Functional for the video
// readout (was a connectivity stub); LVS reads this -lib so the body doesn't matter to it.
module ie7_ctr   (input wire up, down, load_n, clr, input wire [3:0] d,
                  output wire [3:0] q, output wire co, bo);   // real 74193/ИЕ7 pin set (sheet-2)
    reg [3:0] cnt = 0;
    always @(posedge up) if (~load_n) cnt <= d; else cnt <= cnt + 4'd1;   // down-count unused (DOWN idles high)
    assign q  = cnt;
    assign co = (cnt == 4'hF);           // terminal-count carry (feeds the next stage's UP)
    assign bo = 1'b1;                    // borrow idle (no down-counting modeled)
endmodule
// D48/D49 КП14 quad 2:1 mux: y = sel ? b : a (en_n low = enabled). For DRAM addressing, sel picks
// the ROW half (b) vs COL half (a) of the CPU address onto the 8-bit muxed bus MA.
module kp14_mux  (input wire [3:0] a, b, input wire sel, en_n, output wire [3:0] y);
    assign y = en_n ? 4'bz : (sel ? b : a); endmodule
// D53 ИД7 -- realized as the DRAM RAS/CAS strobe generator (the РЕ3/АГ3 timing it really comes from
// is un-modeled -> boundary). Repurposed inputs: a = RAM-select (ram_n, active-low), b = Φ1, c = Φ2.
// RAS falls on Φ1 of a RAM access (latches the row) and remains active through the Φ2/CAS
// column phase; CAS pulses during Φ2. A real 4164 requires this overlap -- a Φ1-only RAS pulse
// releases the row before the column transaction and makes write behavior simulator-dependent.
// ИД7 RAS/CAS decoder. g = decoder enable: only a real memory cycle pulses RAS/CAS, so an
// INTA / I/O cycle whose address happens to fall in the RAM region does NOT make the DRAM
// drive the bus (which would corrupt the 8259's injected interrupt vector). Normal read/write
// cycles keep g=1, so the boot timing is unchanged.
// D53 ИД7 (74S138-class). Structural inputs per sheet-2: A(1)<-E2 jumper, B(2)<-E3 jumper,
// C(3)=GND, G2(5)=GND, G1/G3 feeds pending; outputs Y0-Y3 = pins 15/14/13/12, each through its
// R49-R52 100R series (net_boundary in juku_top) onto the PER-BANK RAS rails 14/13/12/11 (array
// read: R is per bank, C/W shared). The behavioral RAS strobe is emitted on Y0 -- the populated
// bank D84-91 hangs on rail 14 <- Y0. `sactive` = sim-only mem_active qualifier; `cas_sim` =
// SIM-ONLY leg carrying the CAS scaffold to the rail-15 net_boundary (the real driver is D36.11;
// both are in lvs.py's SIM_ONLY contract). In the traced/boot jumper position (2-3) a=Φ1, b=Φ2.
// Real G wiring (chase c4_g3_src): G1(6) <- VID_CPU_SEL (memory-cycle qualifier), G2A_N(4) <-
// Ф2TTL (strobe window), G2B_N(5) = GND. The sim cannot reproduce that timing (frozen mesh), so
// g/g2a_n are connectivity-only here and the DRAM-enable semantics ride ram_en_sim -- a SIM-ONLY
// leg (lvs.py contract, like SACTIVE/CAS_SIM) fed from the RAM decode through a net_boundary.
module rascas_dec (input wire a, b, c, input wire g, g2a_n, g2b_n, input wire sactive, ram_en_sim,
                   output wire [3:0] y_n, output wire y_n4, y_n5, y_n6, y_n7,
                   output wire cas_sim);
    reg ras_sim_n = 1'b1;
    // Functional timing latch behind the SIM-ONLY access qualifier. Set RAS active in the row
    // phase, hold it through the CAS column pulse, and release it when the CPU RAM access ends.
    // The physical output/bank wiring remains represented by the D53/R49 path in juku_top.
    always @* begin
        if (~sactive || ram_en_sim) ras_sim_n = 1'b1;
        else if (a)                 ras_sim_n = 1'b0;
    end
    assign y_n[0]   = ras_sim_n;                       // behavioral RAS -> populated bank rail 14
    assign y_n[3:1] = 3'b111;                         // expansion-bank RAS rails (sockets empty)
    assign {y_n7, y_n6, y_n5, y_n4} = 4'b1111;       // physical pins are undrawn/NC on sheet 2
    assign cas_sim  = ~(sactive & ~ram_en_sim & b);   // behavioral CAS column pulse -> rail 15 boundary
endmodule
// Configuration jumper (Е2/Е3/Е10/Е13 family): 3 pads, position 1-2 or 2-3. Functional model =
// the 2-3 position (the traced/boot configuration): common follows p3.
module jumper3 (input wire p1, p3, output wire p2); assign p2 = p3; endmodule
// ---- video dot-clock chain (board JSON provenance, sheet-2 BR) ----
module ag3_oneshot (input wire a_n, b, clr_n, a2_n, b2, clr2_n,   // D56 АГ3 (74123) dual one-shot
                    output wire q, q_n, q2, q2_n);                 // both sections SYNC-B-triggered (traced)
    assign q = 1'bz; assign q_n = 1'bz; assign q2 = 1'bz; assign q2_n = 1'bz; endmodule
module ie10_ctr (input wire clk, clr_n, load_n, enp, ent, input wire [3:0] d,  // D103 ИЕ10 (СТ16): /N -> 1.23 MHz
                 output wire [3:0] q, output wire co);
    assign q = 4'bz; assign co = 1'bz; endmodule

// ---- ИР16 (factory К555ИР16): 8-bit parallel-in / serial-out shift register (PISO) ----
// The video pixel serializer. shl_n low = parallel-LOAD the framebuffer byte; high = SHIFT one bit
// per clk (MSB first) into the ЛП5 combine. clk_inh freezes it; clr_n clears. This is the piece that
// turns a framebuffer byte into the 8-pixel dot stream at the 16 MHz dot clock.
module ir16_sr (input wire clk, clk_inh, shl_n, clr_n, si, input wire [7:0] d, output wire so);
    reg [7:0] q = 0;
    always @(posedge clk) if (~clr_n) q <= 8'b0;
                          else if (~clk_inh) q <= ~shl_n ? d : {q[6:0], si};  // load, else shift-left
    assign so = q[7];                     // serial out = MSB (first pixel of the byte)
endmodule

// ---- ЛП5 (К531ЛП5, XOR "=1"): D34 video-output combine (pixel stream XOR sync/blanking) ----
module lp5_xor1 (input wire a, b, output wire y); assign y = a ^ b; endmodule  // sim video-out adjunct section

// ---- ИР16 (factory К555ИР16): 4-bit parallel-load shift register — the video PIXEL SERIALIZERS D42/D43 ----
// Traced (owner + sheet-2 top-right): D=pin5,C=pin4,B=pin3,A=pin2 parallel data in; LD=pin6 load;
// G=pin8 control; CK=pin9 clock; DS=pin1 serial in; QA/QB/QC/QD = pins13/12/11/10.
// The serializer uses QD/pin10 as its serial output -> node "A"
// (the analog video-mix summing node) -> D34. Two of these (D42 high nibble, D43 low nibble) form the
// 8-bit serializer. Connectivity for LVS (the runnable video demo uses the abstracted ir16_sr; the
// exact 2x4-bit + analog-sum byte->pixel scheme is the documented boundary — see dram-video-timing.md).
module ir16 (input wire a, b, c, d, ld, g, ck, ds, output wire qd, output wire qa, qb, qc);
    reg [3:0] r = 0;
    always @(posedge ck) if (~ld) r <= {d, c, b, a}; else r <= {r[2:0], ds};
    assign qd = r[3];
    assign qa = r[0];   // pin 13 (QA) -- D41 (sheet-2 LATCH chain) taps the parallel outputs
    assign qb = r[1];   // pin 12 (QB)
    assign qc = r[2];   // pin 11 (QC)
endmodule

// ---- video raster scanner (the ИЕ7 counter chain + timing, as one behavioral block) ----
// Scans the 40x241 framebuffer at 0xD800, emitting the byte address and the ИР16 load/shift
// control (LOAD at pixel 0 of each char byte, SHIFT for the other 7). Sim-functional; kept in a
// module so juku_top stays purely structural (no processes -> the LVS yosys JSON backend is happy).
module video_raster (input wire dotclk, output wire [15:0] vid_addr, output wire shl_n);
    reg [15:0] vraster = 16'hD800; reg [2:0] vpix = 0;
    always @(posedge dotclk) begin
        if (vpix == 3'd7) begin
            vpix    <= 0;
            vraster <= (vraster == 16'hD800 + 16'd9639) ? 16'hD800 : vraster + 1'b1;
        end else vpix <= vpix + 1'b1;
    end
    assign vid_addr = vraster;
    assign shl_n    = (vpix != 3'd0);
endmodule

// ---- К565РУ5 64Kx1 DRAM (one chip = one data bit); array from D60 ----
// К565РУ5 64Kx1 DRAM (one chip = one data bit). Multiplexed addressing: latch the ROW from MA on
// RAS, the COL from MA on CAS -> 16-bit cell address. Read is sample-held on CAS and driven onto DB
// for the duration of the access. For writes, the 4164-class contract strobes DIN on the latter
// falling edge of CAS or WE: CAS for an early write, WE for a delayed/read-modify-write cycle.
module dram_64kx1 (input wire [7:0] ma,
                   input wire ras_n, cas_n, we_n, di,
                   input wire nc_vbb_option, vcc_option, vss_gnd,
                   output wire do_,
                   input wire [15:0] va, output wire vq);   // SIM-ONLY 2nd read port for video readout
    reg [7:0] row; reg mem [0:65535]; reg held; integer i;
    initial begin held = 0; for (i = 0; i < 65536; i = i+1) mem[i] = 0; end
    // Video read port: the real РУ5 time-multiplexes ONE data pin between CPU and video (КП14
    // arbitration remains a physical boundary); in sim a read doesn't contend, so we expose the framebuffer
    // bit at `va` directly. `va`/`vq` are sim artifacts (not real pins) -> LVS allowlist drops them.
    assign vq = mem[va];
    // The drawn D48-D51 mux tables scramble BA[15:8] onto the row-phase MA lines (finding 24;
    // identical scramble on CPU + video pairs -> behaviorally neutral). Normalize here so mem[]
    // stays CPU-linear (tbs + the va video port index it directly): un-permute the raw row byte.
    wire [7:0] row_lin = {row[6], row[5], row[1], row[4], row[2], row[3], row[0], row[7]};
    always @(negedge ras_n) row <= ma;                       // latch row (ma = scrambled hi byte during Φ1)
    // The latter negative transition of CAS or WE is the physical DIN strobe. Watching both inputs
    // handles early and delayed writes without a synthetic master-clock pin or same-timestep race.
    // A CAS fall with WE high starts a read; a later WE fall converts it to read-modify-write.
    always @(negedge cas_n or negedge we_n) begin
        if (~ras_n && ~cas_n && ~we_n) mem[{row_lin, ma}] <= di;
        else if (~ras_n && ~cas_n)     held <= mem[{row_lin, ma}];
    end
    // Keep the sampled value available through the functional access window. Exact DOUT turn-off
    // awaits the still-untraced D36/R57 delays; the CPU must not see a scheduling-dependent Z when
    // the zero-delay CAS scaffold rises in the same timestep as its sample.
    assign do_ = (we_n & (~ras_n | ~cas_n)) ? held : 1'bz;
endmodule

// ---- peripheral shells ----
// Peripherals: behavioral IN = last-OUT (the model that boots ekta37 in juku_struct). Write latches
// the addressed register while the I/O write strobe is active (DB is held stable by the 8238 then);
// read drives the last value back. PPI0 Port C low = the banking mode.
// 8255 PPI: latched ports + Port C low -> banking mode (portc_lo), incl. the BSR (bit
// set/reset) control writes (A==3). PPI0 (D26) also carries the KEYBOARD: Port A write
// low-nibble = the column the BIOS scans; Port B read = the 74148-encoded held key
// {SHIFT b7-6 active-LOW, code b3-1, GS b0 active-LOW}. The key is presented as sim-only
// stimulus (kbd_*, opt-in via kbd_en so a kbd-off boot stays byte-identical); PPI1 ties it off.
module ppi_8255 (input wire [1:0] A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n, reset,
                 output wire [7:0] pc,      // physical Port C pins (D26: mem-mode+floppy ctl; D27: X2)
                 output wire [7:0] pa,      // physical Port A pins (kbd scan SC0-3, AUDC, PREN, STB)
                 input wire [7:0] pb,       // physical Port B pins (kbd data; unused by the sim path)
                 input wire kbd_en, kbd_pressed, kbd_shift,
                 input wire [3:0] kcol, input wire [2:0] kbit);
    reg [7:0] regs [0:3]; reg [7:0] portc; reg [2:0] bsr_bit; integer i;
    assign pc = portc;
    reg [3:0] kbd_col_sel = 0;                  // last column the BIOS wrote to Port A
    initial begin for (i=0;i<4;i=i+1) regs[i]=0; portc=0; end

    assign pa = regs[0];               // Port A latch drives the pins (mode-0 output)
    wire held    = kbd_en & kbd_pressed;
    wire kactive = held & (kbd_col_sel == kcol);
    wire [7:0] kbd_portb = {1'b1, ~(held & kbd_shift), 2'b00,
                            kactive ? {((~kbit) & 3'h7), 1'b0} : 4'hF};

    assign D = (~cs_n & ~rd_n) ? ((kbd_en & A == 2'd1) ? kbd_portb : regs[A]) : 8'bz;
    always @(posedge reset or negedge wr_n) begin
        if (reset) begin
            for (i=0;i<4;i=i+1) regs[i] <= 0;
            portc <= 0;
            kbd_col_sel <= 0;
        end else begin
            #1;
            if (~cs_n) begin
                regs[A] <= D;
                if (A == 2'd0) kbd_col_sel <= D[3:0];    // Port A write = keyboard column select
                if (A == 2'd2) portc <= D;
                else if (A == 2'd3) begin                // BSR: set/reset one Port C bit
                    if (D[7]) portc <= 0;
                    else begin bsr_bit = (D >> 1) & 3'd7; portc[bsr_bit] <= D[0]; end
                end
            end
        end
    end
endmodule

module pit_8253 (input wire [1:0] A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n, clk,
                 input wire clk0, gate0, clk1, gate1, clk2, gate2,
                 output wire out0, out1, out2);
    reg [7:0] regs [0:3]; integer i;
    reg [1:0] access [0:2], phase [0:2];
    reg [15:0] reload [0:2], count [0:2];
    reg [7:0] low_latch [0:2];
    reg [2:0] mode [0:2];
    reg [2:0] ch;
    reg [15:0] next_reload;
    reg [2:0] ctl_ch;
    initial begin
        for (i=0;i<4;i=i+1) regs[i]=0;
        for (i=0;i<3;i=i+1) begin
            access[i]=2'b11; phase[i]=0; reload[i]=0; count[i]=0; low_latch[i]=0; mode[i]=0;
        end
    end

    always @(negedge wr_n) if (~cs_n) begin
        regs[A] = D;
        if (A == 2'd3) begin
            ctl_ch = D[7:6];
            if (ctl_ch < 3) begin
                access[ctl_ch] = D[5:4];
                mode[ctl_ch] = D[3:1];
                phase[ctl_ch] = 0;
            end
        end else begin
            ch = A;
            if (access[ch] == 2'b01) begin
                next_reload = {8'h00, D};
                reload[ch] = (next_reload == 0) ? 16'hffff : next_reload;
                count[ch] = (next_reload == 0) ? 16'hffff : next_reload;
                phase[ch] = 0;
            end else if (access[ch] == 2'b10) begin
                next_reload = {D, 8'h00};
                reload[ch] = (next_reload == 0) ? 16'hffff : next_reload;
                count[ch] = (next_reload == 0) ? 16'hffff : next_reload;
                phase[ch] = 0;
            end else if (access[ch] == 2'b11) begin
                if (phase[ch] == 0) begin
                    low_latch[ch] = D;
                    phase[ch] = 1;
                end else begin
                    next_reload = {D, low_latch[ch]};
                    reload[ch] = (next_reload == 0) ? 16'hffff : next_reload;
                    count[ch] = (next_reload == 0) ? 16'hffff : next_reload;
                    phase[ch] = 0;
                end
            end
        end
    end
    assign D = (~cs_n & ~rd_n) ? regs[A] : 8'bz;
    // Minimal programmable divider behavior: enough for video/frame/sound source
    // guards. It is not a full 8253 mode-accurate waveform model; each loaded
    // channel divides its input clock by the programmed count and toggles OUT.
    reg [2:0] out_r = 3'b000;
    assign out0 = out_r[0]; assign out1 = out_r[1]; assign out2 = out_r[2];
    always @(posedge clk0) if (gate0 && reload[0] != 0) begin
        if (count[0] <= 1) begin count[0] <= reload[0]; out_r[0] <= ~out_r[0]; end
        else count[0] <= count[0] - 1'b1;
    end
    always @(posedge clk1) if (gate1 && reload[1] != 0) begin
        if (count[1] <= 1) begin count[1] <= reload[1]; out_r[1] <= ~out_r[1]; end
        else count[1] <= count[1] - 1'b1;
    end
    always @(posedge clk2) if (gate2 && reload[2] != 0) begin
        if (count[2] <= 1) begin count[2] <= reload[2]; out_r[2] <= ~out_r[2]; end
        else count[2] <= count[2] - 1'b1;
    end
endmodule

module usart_8251 (input wire A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n, clk, rxc, txc,
                   input wire vss_gnd, vcc_5v,
                   output wire txd, rts, dtr, rxrdy, txrdy, syndet, txempty,
                   input wire rxd, cts_n, reset, dsr_n);
    reg [7:0] mode = 8'h00, command = 8'h00, rx_data = 8'h00;
    reg mode_seen = 1'b0;

    reg txd_r = 1'b1, tx_busy = 1'b0;
    reg [8:0] tx_shift = 9'h1ff;
    integer tx_bits = 0;

    reg rx_busy = 1'b0, rx_ready = 1'b0;
    reg [7:0] rx_shift = 8'h00;
    integer rx_bits = 0;

    wire tx_enable = command[0];
    wire rx_enable = command[2];
    wire [7:0] status = {5'b00000, ~tx_busy, rx_ready, ~tx_busy};

    assign D = (~cs_n & ~rd_n) ? (A ? status : rx_data) : 8'bz;
    assign txd = txd_r;
    assign rts = ~command[5];
    assign dtr = ~command[1];
    assign rxrdy = rx_ready;
    assign txrdy = ~tx_busy;
    assign txempty = ~tx_busy;
    assign syndet = 1'b0;

    always @(negedge wr_n) if (~cs_n) begin
        if (A) begin
            if (!mode_seen) begin
                mode <= D;
                mode_seen <= 1'b1;
            end else if (D[6]) begin
                command <= 8'h00;
                mode_seen <= 1'b0;
                txd_r <= 1'b1;
                tx_busy <= 1'b0;
                rx_busy <= 1'b0;
                rx_ready <= 1'b0;
            end else begin
                command <= D;
                if (D[4]) rx_ready <= 1'b0;  // error reset also clears the minimal RX latch.
            end
        end else if (tx_enable && !tx_busy) begin
            tx_shift <= {1'b1, D};  // 8 data bits, then stop; start bit is driven immediately.
            tx_bits <= 9;
            txd_r <= 1'b0;
            tx_busy <= 1'b1;
        end
    end

    always @(negedge rd_n) if (~cs_n && !A) begin
        rx_ready <= 1'b0;
    end

    // Minimal async 8N1 shifter. It is enough for digital loopback/bring-up
    // guards; mode word parity/stop-bit variants and sync mode remain out of
    // scope until software needs them.
    always @(posedge txc) if (tx_busy) begin
        txd_r <= tx_shift[0];
        tx_shift <= {1'b1, tx_shift[8:1]};
        if (tx_bits <= 1) begin
            tx_busy <= 1'b0;
            tx_bits <= 0;
        end else begin
            tx_bits <= tx_bits - 1;
        end
    end

    always @(posedge rxc) begin
        if (!rx_busy) begin
            if (rx_enable && !rx_ready && rxd == 1'b0) begin
                rx_busy <= 1'b1;
                rx_bits <= 0;
                rx_shift <= 8'h00;
            end
        end else if (rx_bits < 8) begin
            rx_shift <= {rxd, rx_shift[7:1]};
            rx_bits <= rx_bits + 1;
        end else begin
            rx_data <= rx_shift;
            rx_ready <= 1'b1;
            rx_busy <= 1'b0;
            rx_bits <= 0;
        end
    end
endmodule

// К170АП2 serial line driver -- DIP-8 DUAL (board photo pin-count; power 8/5/4 per the power table
// fits 8-pin). Sections: 3->6, 2->7 (owner scan img). One-way (never drives the USART side).
// Used by D14 (SOUT) and D32 (RTS/DTP). [D3 turned out to be К561ЛН2, not АП2 -- see ln2_inv.]
module ap2_drv (input wire i2, i3, output wire o6, o7);
    assign o6 = i3; assign o7 = i2;
endmodule
// К561ЛН2 hex inverter (CMOS), D3: section 11->10 makes TTL SOUT = ~TxD (the schematic section I
// first misread as an АП2 -- АП2 is 8-pin, so pins 11/10 could only be the ЛН2).
module ln2_inv (input wire a, i13, i1, i3, i5, i9,
                output wire y, o12, o2, o4, o6, o8);   // D3 К561ЛН2 complete hex-inverter package
    assign o12 = ~i13;   // 13->12: -INT7 (X1.113B) -> IR7 (D10.25), via S4 [series switch, unmodeled]
    assign o2  = ~i1;    // 1->2:   -INT6 (X1.113C) -> S4 INT6 throw
    assign o4  = ~i3; // D26 PC1/pin15 -> pulled-up pin3 -> pin4 -> D6 A6/pin1
    assign o6  = ~i5; // D26 PC0/pin14 -> pulled-up pin5 -> pin6 -> D6 A5/pin2
    assign o8  = ~i9; // 9->8 is the serial OC pre-inverter
// original section:
    assign y = ~a;
endmodule
// К155ЛА55/ЛА18 open-collector NAND (D12): -> OC SOUT.
module la18_oc (input wire i1, i2, output wire o3);
    assign o3 = ~(i1 & i2);
endmodule
// К170УП2 triple serial line receiver (D104), as drawn on sheet 1:
// pins 4->13 SIN, 5->12 CTS, and 6->11 DSR. Electrical threshold/polarity
// remains an idealized one-way buffer, matching the former single-section model.
module up2_rcv (input wire sin_in, cts_in, dsr_in,
                output wire sin_out, cts_out, dsr_out);
    assign sin_out = sin_in;
    assign cts_out = cts_in;
    assign dsr_out = dsr_in;
endmodule
// Bracket-mounted serial connector X3. The .009 assembly cable maps PCB
// landings A21..A32 in order to these physical pins 1..12.
module serial_conn (inout wire pullup_io, aux2, ttl_sout, sin, cts, dsr,
                    aux7, aux8, sout, rts, dtp, oc_sout);
endmodule

module fdc_1793 (input wire [1:0] A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n, mr_n, clk, dden,
                 input wire nc_back_bias, vss_gnd, vcc_5v, vdd_12v,
                 output wire step, dirc, early, late, rg, hld, tg43, wg, wdata,
                 input wire test, hlt, rclk, raw_read, ready, tr00, index, wprt,
                 inout wire wf_vfoe,
                 input wire motor_on, side, output wire drq, intrq);
    localparam ST_BUSY = 8'h01;
    localparam ST_DRQ = 8'h02;
    localparam ST_RNF = 8'h10;
    localparam ST_WRITE_PROTECT = 8'h40;
    localparam ST_NOT_READY = 8'h80;

    reg [7:0] status = ST_NOT_READY;
    reg [7:0] track = 8'h00;
    reg [7:0] sector = 8'h01;
    reg [7:0] data = 8'h00;
    reg [7:0] command = 8'h00;
    reg step_dir_in = 1'b1;
    integer buffer_pos = 0;
    integer buffer_len = 0;
    reg [7:0] sector_buf [0:511];
    reg [1023:0] disk_path;
    integer disk_file = 0;
    integer disk_heads = 0;
    integer disk_requested = 0;
    integer disk_loaded = 0;
    integer disk_offset = 0;
    integer disk_read_count = 0;
    integer disk_seek_status = 0;
    integer disk_sector_ok = 0;
    reg intrq_r = 1'b0;

    wire disk_side_valid = !disk_requested || (disk_loaded && ({31'b0, side} < disk_heads));
    wire [7:0] effective_status =
        (motor_on && disk_side_valid) ? (status & ~ST_NOT_READY) : (status | ST_NOT_READY);

    assign drq = status[1];
    assign intrq = intrq_r;
    assign step = 1'bz; assign dirc = 1'bz;
    assign early = 1'bz; assign late = 1'bz; assign rg = 1'bz;
    assign hld = 1'bz; assign tg43 = 1'bz;
    assign wg = 1'bz; assign wdata = 1'bz; assign wf_vfoe = 1'bz;

`ifndef YOSYS
    initial begin
        if ($value$plusargs("disk=%s", disk_path)) begin
            disk_requested = 1;
            if (!$value$plusargs("disk_heads=%d", disk_heads)) disk_heads = 2;
            disk_file = $fopen(disk_path, "rb");
            if (disk_file) begin
                disk_loaded = 1;
                $display("FDC-1793: loaded raw disk %0s (%0d side%s)",
                         disk_path, disk_heads, disk_heads == 1 ? "" : "s");
            end else begin
                $display("FDC-1793: could not open raw disk %0s", disk_path);
            end
        end
    end
`endif

    function is_read_sector(input [7:0] cmd); begin
        is_read_sector = ((cmd & 8'hE0) == 8'h80);
    end endfunction

    function is_type_i(input [7:0] cmd); begin
        is_type_i = (cmd[7] == 1'b0);
    end endfunction

    function is_write_track(input [7:0] cmd); begin
        is_write_track = ((cmd & 8'hF0) == 8'hF0);
    end endfunction

    function [7:0] synthetic_sector_byte(input integer pos); begin
        if (pos == 0) synthetic_sector_byte = track;
        else if (pos == 1) synthetic_sector_byte = {7'b0, side};
        else if (pos == 2) synthetic_sector_byte = sector;
        else synthetic_sector_byte = track + ({7'b0, side} << 5) + sector + pos[7:0];
    end endfunction

`ifndef YOSYS
    task load_disk_sector; begin
        disk_sector_ok = 0;
        if (!disk_loaded) begin
            status = status | ST_NOT_READY;
        end else if (track > 8'd79 || sector == 0 || sector > 10 || ({31'b0, side} >= disk_heads)) begin
            status = status | ST_RNF;
        end else begin
            disk_offset = (((track * disk_heads) + {31'b0, side}) * 10 + (sector - 1)) * 512;
            disk_seek_status = $fseek(disk_file, disk_offset, 0);
            disk_read_count = $fread(sector_buf, disk_file);
            if (disk_seek_status == 0 && disk_read_count == 512) disk_sector_ok = 1;
            else status = status | ST_RNF;
        end
    end endtask
`else
    task load_disk_sector; begin
        disk_sector_ok = 0;
    end endtask
`endif

    task clear_transfer; begin
        buffer_pos = 0;
        buffer_len = 0;
        status = status & ~(ST_BUSY | ST_DRQ);
        intrq_r = 1'b1;
    end endtask

    task begin_read_sector; begin
        clear_transfer();
        status = status & ~(ST_RNF | ST_NOT_READY);
        if (!motor_on) begin
            status = status | ST_NOT_READY;
        end else if (sector == 0 || sector > 10) begin
            status = status | ST_RNF;
        end else if (disk_requested) begin
            load_disk_sector();
            if (disk_sector_ok) begin
                buffer_pos = 0;
                buffer_len = 512;
                status = status | ST_BUSY | ST_DRQ;
                intrq_r = 1'b0;
            end
        end else begin
            buffer_pos = 0;
            buffer_len = 512;
            status = status | ST_BUSY | ST_DRQ;
            intrq_r = 1'b0;
        end
    end endtask

    task finish_type_i(input [7:0] cmd); begin
        clear_transfer();
        status = status & ~(ST_RNF | ST_WRITE_PROTECT | ST_NOT_READY);
        if (!motor_on) begin
            status = status | ST_NOT_READY;
        end else if ((cmd & 8'hF0) == 8'h00) begin
            track = 8'h00;
        end else if ((cmd & 8'hF0) == 8'h10) begin
            step_dir_in = (data >= track);
            track = data;
        end else if ((cmd & 8'hE0) == 8'h20) begin
            if (cmd[4]) begin
                if (step_dir_in && track != 8'hff) track = track + 8'd1;
                else if (!step_dir_in && track != 8'h00) track = track - 8'd1;
            end
        end else if ((cmd & 8'hE0) == 8'h40) begin
            step_dir_in = 1'b1;
            if (cmd[4] && track != 8'hff) track = track + 8'd1;
        end else if ((cmd & 8'hE0) == 8'h60) begin
            step_dir_in = 1'b0;
            if (cmd[4] && track != 8'h00) track = track - 8'd1;
        end
    end endtask

    task reject_write_track; begin
        clear_transfer();
        status = status & ~(ST_RNF | ST_NOT_READY);
        if (!motor_on || (disk_requested && !disk_loaded)) begin
            status = status | ST_NOT_READY;
        end else begin
            status = status | ST_WRITE_PROTECT;
        end
    end endtask

    wire fdc_write_active = ~cs_n & ~wr_n;
    wire fdc_data_read_active = ~cs_n & ~rd_n & (A == 2'd3);

    always @(posedge fdc_write_active) begin
        case (A)
            2'd0: begin
                command = D;
                intrq_r = 1'b0;
                if (is_read_sector(D)) begin_read_sector();
                else if (is_type_i(D)) finish_type_i(D);
                else if ((D & 8'hF0) == 8'hD0) clear_transfer();
                else if (is_write_track(D)) reject_write_track();
                else begin
                    status = (status & ~(ST_RNF | ST_DRQ)) | ST_BUSY;
                end
            end
            2'd1: track = D;
            2'd2: sector = D;
            2'd3: data = D;
        endcase
    end

    always @(posedge fdc_data_read_active) begin
        if (buffer_pos < buffer_len) begin
            data = disk_requested ? sector_buf[buffer_pos] : synthetic_sector_byte(buffer_pos);
            buffer_pos = buffer_pos + 1;
            if (buffer_pos >= buffer_len) clear_transfer();
        end else begin
            status = status & ~ST_DRQ;
        end
    end

    wire [7:0] read_data =
        (A == 2'd0) ? effective_status :
        (A == 2'd1) ? track :
        (A == 2'd2) ? sector :
        data;
    assign D = (~cs_n & ~rd_n) ? read_data : 8'bz;
endmodule

module pic_8259 (input wire A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n,
                 input wire vss_gnd, vcc_5v,
                 input wire ir7, ir6, ir5, ir3, ir2, ir1, ir0,
                 output wire cas0, cas1, cas2, inout wire sp_en,
                 output wire intr, input wire inta_n);
    reg [7:0] regs [0:1]; initial begin regs[0]=0; regs[1]=0; end
    always @(*) if (~cs_n & ~wr_n) regs[A] = D;
    assign D = (~cs_n & ~rd_n) ? regs[A] : 8'bz;
    assign cas0 = 1'bz; assign cas1 = 1'bz; assign cas2 = 1'bz;
    assign sp_en = 1'bz;
    assign intr = 1'bz;     // INT pin driven by the intr_ctl sim adjunct (below); z so it can
endmodule                   // -- with frame ticks off, intr_ctl drives 0 => boot byte-identical

// Sim-only behavioral ADJUNCT to the 8259 (D10) -- NOT a separate chip (it carries no
// refdes, so the LVS skips it as an unmapped instance; see sync/lvs.py). vm80a is a real
// die: to interrupt it we must drive pin_int and feed the 8259's CALL-mode vector over the
// bus during the INTA machine cycles -- behavior the register-stub pic_8259 can't express.
// Snoops the 8259 ICW/OCW from the PIC port writes, raises INT on the external frame tick
// (8253 VER-RTR -> IR5, a boundary), and injects {0xCD, lo, hi} on the INTA reads.
// Opt-in: with frame_tick never pulsing, intr stays 0 and DB is never driven (byte-identical).
module intr_ctl (input wire osc, dbin, inta_n, iowr_n, cs_pic_n, a0, frame_tick,
                 inout wire [7:0] DB, output wire intr);
    reg [7:0] icw1=0, icw2=0, mask=8'hFF; reg expect_icw2=0;
    always @(posedge osc) if (~cs_pic_n & ~iowr_n) begin           // snoop 8259 programming
        if (~a0) begin if (DB[4]) begin icw1<=DB; expect_icw2<=1; end end          // ICW1
        else if (expect_icw2) begin icw2<=DB; expect_icw2<=0; end                  // ICW2 (vector hi)
        else mask<=DB;                                                             // OCW1 (mask)
    end
    wire [15:0] vaddr = {icw2, 8'h00} | {8'h00, (icw1 & 8'hE0)} | 16'h0014;         // IR5<<2 = 0x14

    reg pending=0, ft_q=0, inq=0; integer inta_idx=0;
    always @(posedge osc) begin
        ft_q <= frame_tick;
        if (frame_tick & ~ft_q & ~mask[5]) pending <= 1;            // rising frame tick, IR5 unmasked
        if (~inta_n & ~inq) inq <= 1;                                // entering an INTA read
        if ( inta_n &  inq) begin inq <= 0;                          // leaving an INTA read
            if (inta_idx >= 2) begin inta_idx <= 0; pending <= 0; end  // 3-byte CALL consumed
            else inta_idx <= inta_idx + 1;
        end
    end
    assign intr = pending;
    wire [7:0] ivec = (inta_idx == 0) ? 8'hCD : (inta_idx == 1) ? vaddr[7:0] : vaddr[15:8];
    assign DB = ~inta_n ? ivec : 8'bz;                              // inject vector during INTA reads
endmodule
`default_nettype wire

// D34 К555ЛП5 (XOR): sect (4,5->6) -> C5 560pF RC -> sect (1,2->8) = the video-counter LD
// pulse generator (sheet-2). Pin 1 = +5 (node A) -> y2 = ~b2; b2 <- the RC (boundary).
module lp5_xor (input wire a1, b1, a2, b2, a3, b3, a4, b4, output wire y1, y2, y3, y4);
    assign y1 = a1 ^ b1;
    assign y2 = a2 ^ b2;
    assign y3 = a3 ^ b3;
    assign y4 = a4 ^ b4;
endmodule

// ---- Physical КР1818ВГ93 (WD1793 clone) at D93. This module preserves its proved
// bus pins while the behavioral core and remaining quadrant wiring are incomplete. The temporary
// released outputs prevent unproved behavior from driving DAL/IRQ; they do not denote an omitted,
// abstract, or depopulated controller.
module vg93_fdc (input wire cs_n, re_n, we_n, a0, a1, mr_n, clk, dden,
                 inout wire [7:0] dal, output wire drq, intrq);
    assign dal = 8'hzz; assign drq = 1'bz; assign intrq = 1'bz;
endmodule

// КР580ВА87 (8287, inverting 8286) D100: FDC bus buffer. Non-driving stub (see vg93_fdc).
module buf_8287 (input wire [7:0] a, inout wire [7:0] b, input wire oe_n, t,
                 input wire vss_gnd, vcc_5v);
    assign b = 8'hzz;
endmodule

// D94 К155РЕ3 #2, programmed part ДГШ5.106.092. The exact physical table is
// adopted from three matching reads, including a power-cycled read.
module re3_prom_092 (input wire [4:0] a, input wire e_n, output wire [7:0] d);
    // Photo tracing connects D0/D1/D2 directly to D93 RE/CS/WE. The table closes
    // their programmed states, but the PROM enable and the remaining D93-side
    // continuity boundaries are still unresolved; see d94-reconstruction-constraints.md.
    // РЕ3 outputs are open collector: a programmed one releases the line and a
    // programmed zero sinks it. Board pull-ups therefore recover the raw byte.
    reg [7:0] raw;
    always @* begin
        case (a)
            5'h03: raw = 8'hFE;
            5'h04, 5'h05, 5'h06: raw = 8'hF5;
            5'h07: raw = 8'hFC;
            5'h08, 5'h09, 5'h0A: raw = 8'hF9;
            5'h0B: raw = 8'hFC;
            5'h0F: raw = 8'hFE;
            5'h14, 5'h15, 5'h16, 5'h17: raw = 8'hF5;
            5'h18, 5'h19, 5'h1A, 5'h1B: raw = 8'hF9;
            default: raw = 8'hFF;
        endcase
    end
    assign d[0] = (!e_n && !raw[0]) ? 1'b0 : 1'bz;
    assign d[1] = (!e_n && !raw[1]) ? 1'b0 : 1'bz;
    assign d[2] = (!e_n && !raw[2]) ? 1'b0 : 1'bz;
    assign d[3] = (!e_n && !raw[3]) ? 1'b0 : 1'bz;
    assign d[4] = (!e_n && !raw[4]) ? 1'b0 : 1'bz;
    assign d[5] = (!e_n && !raw[5]) ? 1'b0 : 1'bz;
    assign d[6] = (!e_n && !raw[6]) ? 1'b0 : 1'bz;
    assign d[7] = (!e_n && !raw[7]) ? 1'b0 : 1'bz;
endmodule

// КМ555ТМ2 dual D flip-flop. D30 enables the functional model now that direct
// owner continuity closes its READY section; other boundary-only packages keep
// the non-driving default until their timing is proved.
module tm2_dff #(parameter FUNCTIONAL = 0) (input wire clr1_n, d1, clk1, pre1_n,
                output wire q1, q1_n,
                input wire clr2_n, d2, clk2, pre2_n,
                output wire q2, q2_n);
    generate if (FUNCTIONAL) begin : g_functional
        reg q1_r = 1'b1;
        reg q2_r = 1'b1;
        always @(posedge clk1 or negedge clr1_n or negedge pre1_n)
            if (!clr1_n) q1_r <= 1'b0;
            else if (!pre1_n) q1_r <= 1'b1;
            else q1_r <= d1;
        always @(posedge clk2 or negedge clr2_n or negedge pre2_n)
            if (!clr2_n) q2_r <= 1'b0;
            else if (!pre2_n) q2_r <= 1'b1;
            else q2_r <= d2;
        assign q1 = q1_r; assign q1_n = ~q1_r;
        assign q2 = q2_r; assign q2_n = ~q2_r;
    end else begin : g_boundary
        assign q1 = 1'bz; assign q1_n = 1'bz;
        assign q2 = 1'bz; assign q2_n = 1'bz;
    end endgenerate
endmodule
