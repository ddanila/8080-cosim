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
// decodes high address byte A8..A15 -> ROM/RAM/REV/ROE selects (contents from the
// emulator-recovered map). Enabled by V (from the D7 gate = mode/strobe).
module decode_prom (input wire [15:8] a, input wire v_en_n,
                    output wire rom_n, ram_n, rev, roe_n);
    // Merge step (memory): recovered banking map realized for the ekta37 boot. ROM occupies
    // 0x0000-0x3FFF, split between the two populated 2764s by A13: D15 = low 8K (0x0000-0x1FFF),
    // D16 = high 8K (0x2000-0x3FFF). RAM is everything outside ROM. (`rev` is repurposed as the
    // high-EPROM chip-select. Full 4-mode banking needs the mode wired through -- a boundary; this
    // is the mode-0 reset overlay, which is what ekta37 boots in.)
    // Banking mode from v_en_n (D7 output, fed by 8255#0 Port C bit 0):
    //   mode 0 (v_en_n=1, reset overlay): ROM at 0x0000-0x3FFF.
    //   mode 1 (v_en_n=0): ROM folds up to 0xD800-0xFFFF (the EPROM's BA[12:0] wiring yields the
    //   0x1800+ offset automatically), RAM below. ekta37 toggles this to run high ROM routines
    //   while keeping video RAM (0xD800+) writable in mode 0 -- needed to draw the banner + beyond.
    wire rom_region = v_en_n ? (a <= 8'h3F) : (a >= 8'hD8);
    assign rom_n = ~(rom_region & ~a[13]);   // D15 CE (low 8K)
    assign rev   = ~(rom_region &  a[13]);   // D16 CE (high 8K)
    assign ram_n = ~(~rom_region);           // RAM select (outside ROM)
    assign roe_n = ~rom_region;              // ROM output enable (region); read strobe is MEMR at the EPROM
endmodule

// ---- ЛА3 NAND gate section (D7) gating the PROM enable ----
module la3_gate (input wire a, b, output wire y);
    assign y = ~(a & b);
endmodule

// ---- EPROM 8Kx8 (2764-class, D15/D16 populated) ----
// The 16KB ekta37 BIOS spans D15 (low 8K, HALF=0) + D16 (high 8K, HALF=1), each with its own CE
// from the decode PROM. oe_n is the read strobe (MEMR). Sample-and-hold: latch the byte at the
// read strobe and hold it through DBIN (8080 tOS1/tOS2 -- a combinational multi-hop drive corrupts
// vm80a's fixed-phase capture; see project-status gotchas).
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
module ln1_osc   (input wire xin, output wire osc);                  // D59 ЛН1 crystal oscillator
    assign osc = 1'bz; endmodule
// D35 ЛН5 phase generator. Merge step 3: the discrete clock mesh feeding `osc` is an un-traced
// boundary (D36/D33/D40 gate inputs deferred), so realize the КР580 2-phase clock to functional
// INTENT here -- a non-overlapping Φ1/Φ2. This is a sim clock: it only sets the simulated VALUE;
// the D35->CPU net wiring (what LVS compares) is unchanged, so LVS stays IN SYNC.
module clk_phase (input wire osc, output reg phi1, phi2, phi2ttl);
    initial begin phi1 = 0; phi2 = 0; phi2ttl = 0; end
    always begin
        phi1 = 1;               #20;  phi1 = 0;              #5;   // Φ1 high, dead time
        phi2 = 1; phi2ttl = 1;  #20;  phi2 = 0; phi2ttl = 0; #5;   // Φ2 high, dead time
    end
endmodule
module stb_gen   (input wire osc, output wire stb);                  // D38 (legacy stub, unused)
    assign stb = 1'bz; endmodule
// clock divider + gate mesh (scan: docs/transcription/clock-subsystem.md). Z1 -> D59 osc ->
// D40 divider -> D33/D39/D36 gates -> D38 (ЛА1) = STB and D35 (ЛН5) = Φ1/Φ2.
module ct16_ctr  (input wire clk, r_n, ep, et, pe_n, input wire [3:0] d,  // D40 СТ16 (74161-class)
                  output wire [3:0] q, output wire co);
    assign q = 4'bz; assign co = 1'bz; endmodule
module ln1_inv   (input wire a, output wire y); assign y = ~a; endmodule      // D33 ЛН1 inverter gate
module la12_gate (input wire a, b, output wire y); assign y = ~(a & b); endmodule // D36 ЛА12 NAND gate
module la1_gate  (input wire i0, i1, i2, i3, output wire y);                  // D38 ЛА1 4-input NAND
    assign y = ~(i0 & i1 & i2 & i3); endmodule

// ===== I/O chip-select decoder: К555ИД7 (74138) =====
// Functional (merge step 1): standard 1-of-8 active-low decode, enabled by g1 & !(g2a_n|g2b_n).
// On the board g2a_n/g2b_n = iord_n/iowr_n (enable on either strobe = the documented strobe-OR intent).
module io_dec138 (input wire a, b, c, g1, g2a_n, g2b_n, output wire [7:0] y_n);
    wire en = g1 & ~(g2a_n & g2b_n);
    assign y_n = en ? ~(8'b1 << {c, b, a}) : 8'hFF;
endmodule

// ===== video address generation + address mux (closes РУ5 MA/RAS/CAS) =====
// D44-47 ИЕ7 (К155ИЕ7 = 74193-class): 4-bit binary up-counter. Cascades via CO (carry-out
// pulses at terminal count 0xF) to form the video raster address. Functional for the video
// readout (was a connectivity stub); LVS reads this -lib so the body doesn't matter to it.
module ie7_ctr   (input wire clk, load_n, input wire [3:0] d, output wire [3:0] q, output wire co);
    reg [3:0] cnt = 0;
    always @(posedge clk) if (~load_n) cnt <= d; else cnt <= cnt + 4'd1;
    assign q  = cnt;
    assign co = (cnt == 4'hF);           // terminal-count carry (feeds the next stage's clk)
endmodule
// D48/D49 КП14 quad 2:1 mux: y = sel ? b : a (en_n low = enabled). For DRAM addressing, sel picks
// the ROW half (b) vs COL half (a) of the CPU address onto the 8-bit muxed bus MA.
module kp14_mux  (input wire [3:0] a, b, input wire sel, en_n, output wire [3:0] y);
    assign y = en_n ? 4'bz : (sel ? b : a); endmodule
// D53 ИД7 -- realized as the DRAM RAS/CAS strobe generator (the РЕ3/АГ3 timing it really comes from
// is un-modeled -> boundary). Repurposed inputs: a = RAM-select (ram_n, active-low), b = Φ1, c = Φ2.
// RAS asserts on Φ1 of a RAM access (latches the row), CAS on Φ2 (latches the col). y_n[0]=ras_n, [1]=cas_n.
// ИД7 RAS/CAS decoder. g = decoder enable: only a real memory cycle pulses RAS/CAS, so an
// INTA / I/O cycle whose address happens to fall in the RAM region does NOT make the DRAM
// drive the bus (which would corrupt the 8259's injected interrupt vector). Normal read/write
// cycles keep g=1, so the boot timing is unchanged.
module rascas_dec (input wire a, b, c, input wire g, output wire [3:0] y_n);
    assign y_n[0] = ~(g & ~a & b);     // ras_n
    assign y_n[1] = ~(g & ~a & c);     // cas_n
    assign y_n[3:2] = 2'b11; endmodule
// ---- video dot-clock chain (scan: docs/transcription/dram-video-timing.md, sheet-2 BR) ----
module ag3_oneshot (input wire a_n, b, clr_n, output wire q, q_n);  // D56 АГ3 (74123) RC -> 16 MHz
    assign q = 1'bz; assign q_n = 1'bz; endmodule
module ie10_ctr (input wire clk, clr_n, load_n, input wire [3:0] d,  // D103 ИЕ10 (СТ16): /N -> 1.23 MHz
                 output wire [3:0] q, output wire co);
    assign q = 4'bz; assign co = 1'bz; endmodule

// ---- ИР16 (К155ИР16 = 74166-class): 8-bit parallel-in / serial-out shift register (PISO) ----
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
module lp5_xor (input wire a, b, output wire y); assign y = a ^ b; endmodule

// ---- К565РУ5 64Kx1 DRAM (one chip = one data bit); array from D60 ----
// К565РУ5 64Kx1 DRAM (one chip = one data bit). Multiplexed addressing: latch the ROW from MA on
// RAS, the COL from MA on CAS -> 16-bit cell address. Read is sample-held on CAS and driven onto DB
// for the duration of the access (we_n high = read); write commits on CAS when we_n low.
module dram_64kx1 (input wire sclk,                         // SIM-ONLY sampling clock (see write below)
                   input wire [7:0] ma,
                   input wire ras_n, cas_n, we_n, di,
                   output wire do_);
    reg [7:0] row; reg mem [0:65535]; reg held; integer i;
    initial begin held = 0; for (i = 0; i < 65536; i = i+1) mem[i] = 0; end
    always @(negedge ras_n) row <= ma;                       // latch row (ma = row byte during Φ1)
    // WRITE sampled on osc (the die-replica's master sampling clock) while CAS & WE are both low
    // (ma = col byte during Φ2). Latching on the CAS *edge* dropped writes whose data-valid window
    // didn't line up with Φ2 (the DB settled on a different phase), storing the stale bus -- a silent
    // corruption both guards missed (RAM test checks only 0xD300; VRAM guard only 0xD800+). Sampling
    // on osc catches the settled data on whatever phase it lands, exactly as juku_struct does. osc is
    // a SIM artifact (not a real РУ5 pin); the LVS drops it via the sim-only allowlist (sync/lvs.py).
    always @(posedge sclk) if (~cas_n & ~we_n) mem[{row, ma}] = di;
    always @(negedge cas_n) if (we_n) held <= mem[{row, ma}]; // read: sample-and-hold (ma = col at CAS-fall)
    assign do_ = (we_n & (~ras_n | ~cas_n)) ? held : 1'bz;   // drive on read, through the access
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
                 output reg [1:0] portc_lo,
                 input wire kbd_en, kbd_pressed, kbd_shift,
                 input wire [3:0] kcol, input wire [2:0] kbit);
    reg [7:0] regs [0:3]; reg [7:0] portc; reg [2:0] pb; integer i;
    reg [3:0] kbd_col_sel = 0;                  // last column the BIOS wrote to Port A
    initial begin for (i=0;i<4;i=i+1) regs[i]=0; portc=0; portc_lo=0; end

    wire held    = kbd_en & kbd_pressed;
    wire kactive = held & (kbd_col_sel == kcol);
    wire [7:0] kbd_portb = {1'b1, ~(held & kbd_shift), 2'b00,
                            kactive ? {((~kbit) & 3'h7), 1'b0} : 4'hF};

    assign D = (~cs_n & ~rd_n) ? ((kbd_en & A == 2'd1) ? kbd_portb : regs[A]) : 8'bz;
    always @(*) if (~cs_n & ~wr_n) begin
        regs[A] = D;
        if (A == 2'd0) kbd_col_sel = D[3:0];    // Port A write = keyboard column select
        if (A == 2'd2) begin portc = D; portc_lo = D[1:0]; end
        else if (A == 2'd3) begin               // BSR: set/reset one Port C bit
            if (D[7]) begin portc = 0; portc_lo = 0; end
            else begin pb=(D>>1)&3'd7; if (D[0]) portc[pb]=1; else portc[pb]=0; portc_lo=portc[1:0]; end
        end
    end
endmodule

module pit_8253 (input wire [1:0] A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n, clk);
    reg [7:0] regs [0:3]; integer i; initial for (i=0;i<4;i=i+1) regs[i]=0;
    always @(*) if (~cs_n & ~wr_n) regs[A] = D;
    assign D = (~cs_n & ~rd_n) ? regs[A] : 8'bz;
endmodule

module usart_8251 (input wire A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n, clk);
    reg [7:0] regs [0:1]; initial begin regs[0]=0; regs[1]=0; end
    always @(*) if (~cs_n & ~wr_n) regs[A] = D;
    assign D = (~cs_n & ~rd_n) ? regs[A] : 8'bz;
endmodule

module fdc_1793 (input wire [1:0] A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n, clk);
    reg [7:0] regs [0:3]; integer i; initial for (i=0;i<4;i=i+1) regs[i]=0;
    always @(*) if (~cs_n & ~wr_n) regs[A] = D;
    assign D = (~cs_n & ~rd_n) ? regs[A] : 8'bz;
endmodule

module pic_8259 (input wire A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n,
                 output wire intr, input wire inta_n);
    reg [7:0] regs [0:1]; initial begin regs[0]=0; regs[1]=0; end
    always @(*) if (~cs_n & ~wr_n) regs[A] = D;
    assign D = (~cs_n & ~rd_n) ? regs[A] : 8'bz;
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
