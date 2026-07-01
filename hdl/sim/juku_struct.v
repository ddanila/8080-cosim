// juku_struct: a behavioral REFERENCE ORACLE for cross-checking the real structural top
// (hdl/juku_top.v). It mirrors juku_top's verified datapath instance-for-instance with
// behavioral `_b` chip bodies (flat 64K RAM, osc-sampled writes, etc.), so it is a second,
// independently-written model of the same machine. sync/cosim_check.sh locksteps the two on
// one clock+ROM and flags the first divergent read -- a VALUE-level check stronger than LVS
// (connectivity only) or boot_check (samples just 0xD300 + 0xD800+). This is exactly how the
// DRAM CAS-timing write bug (0xD441) was found. NOT a boot level itself; juku_top is THE model.
//
// (Was hdl/sim/juku_struct_tb.v -- the parallel "runnable twin" -- until juku_top itself booted
// ekta37 bit-identically; its testbench + boot-guard role were retired, this oracle kept.)

// Phase C, step 4: boot through a behavioral realization of the STRUCTURAL TOP.
// This module mirrors hdl/juku_top.v's verified datapath instance-for-instance:
//   cpu_8080 -> buf_8286 (BA) -> io_dec138 (I/O CS) ; cpu <-> sysctl_8238 <-> DB ;
//   peripherals (PPI/PIT/USART/PIC/FDC) on DB + the 8238 strobes.
// Those nets (BA, DB, IORD/IOWR/MEMR/MEMW, the I/O chip-selects) are the scan-grounded
// part of the LVS model, and the boot is carried by them here.
//
// MEMORY (loop-B deepening): now REAL chip instances on the DB bus, not a monolith --
// decode_prom_b (D6 К556РТ4, recovered map), eprom_b (ekta37), dram_bank_b (К565РУ5 RAM).
// The boot flows CPU -> D6 decode -> EPROM/DRAM drives DB. The ONE remaining abstraction
// is the DRAM's multiplexed row/col addressing (RAS/CAS mux) -- genuinely un-traced
// (Phase A boundary), so it is NOT invented here ("scan = source of truth"); the DRAM
// is a flat 64K bank. A validated К565РУ5 row/col model is ready in dram_unit_tb.v for
// when that wiring is traced.
// A few `assumed` glue spots are realized to their known functional INTENT (noted):
//   - io_dec138 enables on (iord|iowr) (the literal 74138 ANDs both -> never enables;
//     the real board has a strobe-OR not yet traced);
//   - banking mode is the 8255#0 Port-C value (the 1-bit la3 gate can't carry 4 modes).
//
// STATUS: WORKS -- the boot runs through the verified structural datapath and the VRAM
// is byte-identical to cosim. Root cause of the earlier failure + the fix:
//   The 8080/КР580ВМ80А requires read data to be STABLE across the whole DBIN window
//   (datasheet tOS1 = setup during phi1, tOS2 = setup to phi2; both must hold). vm80a
//   captures the bus at a fixed phase instant (di<=pin_din while dbin_pin), so a
//   combinational drive that is still settling on this multi-hop bus (A->buf->mem->8238
//   ->D) violates the spec and corrupts the capture. The fix (mem_subsystem below) is
//   SAMPLE-AND-HOLD: latch the read byte when the read strobe asserts and hold it stable
//   through DBIN -- exactly what vm80a's own testbench (hdl/vendor/tb80a.v) does. This is
//   NOT a Soviet-vs-Intel difference: same vm80a core, same flat-bus behavior (step 3);
//   only the bus topology's settling timing differed.
//
// Run (from repo root):
//   iverilog -g2012 -o /tmp/jstruct hdl/vendor/vm80a.v hdl/sim/juku_struct_tb.v
//   vvp /tmp/jstruct  [+maxvram=43000]
`timescale 1ns/100ps
`default_nettype none

// ===== verified-datapath chips (behavioral bodies; ports = juku_top contract) =====

// CPU: vm80a die-replica. `osc` = the die-replica high-speed sampling clock (a sim
// necessity; the real КР580ВМ80А derives timing from Φ1/Φ2 internally).
module cpu_8080_b(input wire osc, phi1, phi2, ready, reset, hold, intr,
                  output wire [15:0] A, inout wire [7:0] D,
                  output wire dbin, wr_n, sync, hlda, inte, wait_o);
  vm80a u(.pin_clk(osc), .pin_f1(phi1), .pin_f2(phi2), .pin_reset(reset),
          .pin_a(A), .pin_d(D), .pin_hold(hold), .pin_hlda(hlda), .pin_ready(ready),
          .pin_wait(wait_o), .pin_int(intr), .pin_inte(inte), .pin_sync(sync),
          .pin_dbin(dbin), .pin_wr_n(wr_n));
endmodule

// 8286 octal buffer used as address buffer (CPU A -> buffered BA).
module buf_8286_b(inout wire [7:0] Ain, Aout, input wire oe_n, t);
  assign Aout = (~oe_n & t) ? Ain : 8'bz;     // small transport delay: settle before capture
endmodule

// 8238 system controller: latch the status byte, generate strobes, bridge D <-> DB.
module sysctl_8238_b(inout wire [7:0] D, DB, input wire osc, sync, dbin, wr_n, hlda,
                     output wire memr_n, memw_n, iord_n, iowr_n, inta_n);
  reg [7:0] status = 0; reg sq = 0;
  always @(posedge osc) begin                 // status valid while sync high; sample
    if (sync && !sq) status <= D;             // on a clk edge inside the sync window
    sq <= sync;
  end
  assign memr_n = ~(dbin  & ~status[6] & ~status[0]);   // status[7]MEMR (not INP/INTA)
  assign iord_n = ~(dbin  &  status[6]);                // status[6]=INP
  assign memw_n = ~(~wr_n & ~status[4]);                // memory write (not OUT)
  assign iowr_n = ~(~wr_n &  status[4]);                // status[4]=OUT
  assign inta_n = ~(dbin  &  status[0]);
  assign D  = dbin   ? DB : 8'bz;          // read:  system bus -> CPU (settle before capture)
  assign DB = (~wr_n) ? D  : 8'bz;            // write: CPU -> system bus
endmodule

// К555ИД7 (74138) I/O decode. NOTE: enables on (iord|iowr) -- functional intent (see header).
module io_dec138_b(input wire a, b, c, g1, g2a_n, g2b_n, output wire [7:0] y_n);
  wire en = g1 & ~(g2a_n & g2b_n);
  wire [2:0] sel = {c, b, a};
  assign y_n = en ? ~(8'b1 << sel) : 8'hFF;
endmodule

// 8255#0 (D26): latched ports + Port C -> banking mode (portc_lo) + the KEYBOARD.
// Writes are sampled on `osc` while wr_n is low (data settled on DB) -- NOT on the
// wr_n edge: the 8238 gates DB onto the bus with wr_n, so an edge-latch reads stale DB.
//
// Keyboard (opt-in via kbd_en, so the boot guard stays byte-identical):
//   Port A (A==0) WRITE low-nibble = the column the BIOS selects to scan;
//   Port B (A==1) READ = {SHIFT b7-6 active-LOW, 74148 code b3-1, GS b0 active-LOW}.
// The "typed" key is presented externally as (kcol,kbit,shift,pressed) from the TB.
module ppi0_b(input wire osc, input wire [1:0] A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n, reset,
              output reg [1:0] portc_lo,
              input wire kbd_en, kbd_pressed, kbd_shift, input wire [3:0] kcol, input wire [2:0] kbit);
  reg [7:0] regs [0:3]; reg [7:0] portc; reg [2:0] pb; integer i;
  reg [3:0] kbd_col_sel = 0;                 // last column the BIOS wrote to Port A
  initial begin for (i=0;i<4;i=i+1) regs[i]=0; portc=0; portc_lo=0; end

  // 74148 encode of the held key in the BIOS-selected column (mirrors cosim kbd_portb):
  wire held    = kbd_en & kbd_pressed;
  wire kactive = held & (kbd_col_sel == kcol);
  wire [7:0] kbd_portb = {1'b1, ~(held & kbd_shift), 2'b00,        // b7=1, b6=SHIFT(active-low), b5-4=0
                          kactive ? {((~kbit) & 3'h7), 1'b0}        // key: code b3-1, GS b0=0
                                  : 4'hF};                          // no key here: code=7, GS=1

  assign D = (~cs_n & ~rd_n) ? ((kbd_en & A == 2'd1) ? kbd_portb : regs[A]) : 8'bz;
  always @(posedge osc) if (~cs_n & ~wr_n) begin
    regs[A] = D;
    if (A == 2'd0) kbd_col_sel <= D[3:0];    // Port A write = keyboard column select
    if (A == 2'd2) begin portc = D; portc_lo = D[1:0]; end
    else if (A == 2'd3) begin
      if (D[7]) begin portc = 0; portc_lo = 0; end
      else begin pb=(D>>1)&3'd7; if (D[0]) portc[pb]=1; else portc[pb]=0; portc_lo=portc[1:0]; end
    end
  end
endmodule

// 8259 (D-?) interrupt generation for the twin: snoop the 8259 ICW/OCW from the PIC port
// writes, drive pin_int on the external frame tick (the 8253 VER-RTR -> IR5, a boundary
// here), and inject the MCS-80 3-byte CALL vector {0xCD, lo, hi} onto DB during the INTA
// reads. Opt-in: with frame_tick never pulsing, intr stays 0 and DB is never driven (boot
// byte-identical). Vector = ICW2<<8 | (ICW1 & 0xE0) | (IR5<<2), validated in intr_unit_tb.v.
module intr_ctl_b(input wire osc, dbin, inta_n, iowr_n, cs_pic_n, a0, frame_tick,
                  inout wire [7:0] DB, output wire intr);
  reg [7:0] icw1=0, icw2=0, mask=8'hFF; reg expect_icw2=0;
  always @(posedge osc) if (~cs_pic_n & ~iowr_n) begin           // snoop 8259 programming
    if (~a0) begin if (DB[4]) begin icw1<=DB; expect_icw2<=1; end end          // ICW1
    else if (expect_icw2) begin icw2<=DB; expect_icw2<=0; end                  // ICW2 (vector hi)
    else mask<=DB;                                                             // OCW1 (mask)
  end
  wire [15:0] vaddr = {icw2, 8'h00} | {8'h00, (icw1 & 8'hE0)} | 16'h0014;       // IR5<<2 = 0x14

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
  assign DB = ~inta_n ? ivec : 8'bz;                             // inject vector during INTA reads
endmodule

// Generic latched peripheral (PPI1/PIT/USART/PIC/FDC): IN = last OUT (cosim model).
module periph_b(input wire osc, input wire [1:0] A, inout wire [7:0] D, input wire cs_n, rd_n, wr_n);
  reg [7:0] regs [0:3]; integer i; initial for (i=0;i<4;i=i+1) regs[i]=0;
  assign D = (~cs_n & ~rd_n) ? regs[A] : 8'bz;
  always @(posedge osc) if (~cs_n & ~wr_n) regs[A] = D;
endmodule

// ===== memory subsystem as REAL chip instances (loop-B deepening) =====
// D6 (К556РТ4) memory-decode PROM: high address + banking mode -> ROM/RAM select +
// the ROM offset (banking folds 0xD800->0x1800). Contents = emulator-recovered map
// (`prom` provenance). Mode is the 8255#0 Port-C value.
module decode_prom_b(input wire [15:0] a, input wire [1:0] mode,
                     output reg rom_sel, ram_sel, output reg [13:0] rom_idx);
  always @(*) begin
    rom_sel=0; ram_sel=0; rom_idx=14'd0;
    case (mode)
      2'd0:      if (a<=16'h3FFF) begin rom_sel=1; rom_idx=a[13:0]; end else ram_sel=1;
      2'd1,2'd2: if (a>=16'hD800) begin rom_sel=1; rom_idx=16'h1800+(a-16'hD800); end else ram_sel=1;
      default:   ram_sel=1;
    endcase
  end
endmodule

// EPROM array (ekta37): real ROM chip on the DB bus; sample-and-hold read (8080 tOS1/2).
module eprom_b(input wire [13:0] idx, input wire sel, rd_n, inout wire [7:0] db);
  reg [7:0] rom [0:16383]; reg [1023:0] romfile;
  initial begin
    if (!$value$plusargs("rom=%s", romfile)) romfile = "hdl/sim/ekta37.hex";
    $readmemh(romfile, rom);
  end
  reg [7:0] held;
  always @(negedge rd_n) if (sel) held <= rom[idx];      // latch when read strobe asserts
  assign db = (sel & ~rd_n) ? held : 8'bz;
endmodule

// DRAM bank (К565РУ5 array): real RAM on the DB bus. Behavioral 64K -- the multiplexed
// row/col addressing (RAS/CAS mux) is the un-traced boundary, so it is NOT invented here
// (a validated К565РУ5 row/col model lives in hdl/sim/dram_unit_tb.v for when it is traced).
module dram_bank_b(input wire osc, input wire [15:0] a, input wire sel, rd_n, we_n, inout wire [7:0] db);
  reg [7:0] mem [0:65535]; integer i; initial for (i=0;i<65536;i=i+1) mem[i]=0;
  reg [7:0] held;
  always @(negedge rd_n) if (sel) held <= mem[a];
  assign db = (sel & ~rd_n) ? held : 8'bz;
  always @(posedge osc) if (sel & ~we_n) mem[a] = db;   // sample write while strobe low
endmodule

// =============================== structural top =================================
// Wiring mirrors hdl/juku_top.v (verified datapath); memory replaced by the black box.
module juku_struct(input wire osc, phi1, phi2, reset, input wire ready,
                   input wire frame_tick, kbd_en, kbd_pressed, kbd_shift,   // external stimulus
                   input wire [3:0] kbd_kcol, input wire [2:0] kbd_kbit);
  wire [15:0] A, BA; tri1 [7:0] D, DB;     // tri1: pull-up like the real open bus (avoids z/x poisoning vm80a's capture)
  wire dbin, wr_n, sync, hlda, inte, wait_o, intr;
  wire memr_n, memw_n, iord_n, iowr_n, inta_n;
  wire cs_pic_n, cs_ppi0_n, cs_sio0_n, cs_ppi1_n, cs_pit0_n, cs_pit1_n, cs_pit2_n, cs_fdc_n;
  wire [1:0] mem_mode;

  cpu_8080_b  U_CPU (.osc(osc), .phi1(phi1), .phi2(phi2), .ready(ready), .reset(reset),
                     .hold(1'b0), .intr(intr), .A(A), .D(D),
                     .dbin(dbin), .wr_n(wr_n), .sync(sync), .hlda(hlda), .inte(inte), .wait_o(wait_o));
  sysctl_8238_b U_SYS (.D(D), .DB(DB), .osc(osc), .sync(sync), .dbin(dbin), .wr_n(wr_n), .hlda(hlda),
                       .memr_n(memr_n), .memw_n(memw_n), .iord_n(iord_n), .iowr_n(iowr_n), .inta_n(inta_n));
  buf_8286_b  U_BUFL (.Ain(A[7:0]),  .Aout(BA[7:0]),  .oe_n(1'b0), .t(1'b1));
  buf_8286_b  U_BUFH (.Ain(A[15:8]), .Aout(BA[15:8]), .oe_n(1'b0), .t(1'b1));

  io_dec138_b U_DID7 (.a(BA[2]), .b(BA[3]), .c(BA[4]), .g1(1'b1), .g2a_n(iord_n), .g2b_n(iowr_n),
      .y_n({cs_fdc_n, cs_pit2_n, cs_pit1_n, cs_pit0_n, cs_ppi1_n, cs_sio0_n, cs_ppi0_n, cs_pic_n}));

  wire dec_rom, dec_ram; wire [13:0] dec_idx;
  decode_prom_b U_D6   (.a(BA), .mode(mem_mode), .rom_sel(dec_rom), .ram_sel(dec_ram), .rom_idx(dec_idx));
  eprom_b       U_EPROM(.idx(dec_idx), .sel(dec_rom), .rd_n(memr_n), .db(DB));
  dram_bank_b   U_DRAM (.osc(osc), .a(BA), .sel(dec_ram), .rd_n(memr_n), .we_n(memw_n), .db(DB));

  ppi0_b    U_PPI0 (.osc(osc), .A(BA[1:0]), .D(DB), .cs_n(cs_ppi0_n), .rd_n(iord_n), .wr_n(iowr_n), .reset(reset), .portc_lo(mem_mode),
                    .kbd_en(kbd_en), .kbd_pressed(kbd_pressed), .kbd_shift(kbd_shift), .kcol(kbd_kcol), .kbit(kbd_kbit));
  periph_b  U_PPI1 (.osc(osc), .A(BA[1:0]), .D(DB), .cs_n(cs_ppi1_n), .rd_n(iord_n), .wr_n(iowr_n));
  periph_b  U_PIT0 (.osc(osc), .A(BA[1:0]), .D(DB), .cs_n(cs_pit0_n), .rd_n(iord_n), .wr_n(iowr_n));
  periph_b  U_PIT1 (.osc(osc), .A(BA[1:0]), .D(DB), .cs_n(cs_pit1_n), .rd_n(iord_n), .wr_n(iowr_n));
  periph_b  U_PIT2 (.osc(osc), .A(BA[1:0]), .D(DB), .cs_n(cs_pit2_n), .rd_n(iord_n), .wr_n(iowr_n));
  periph_b  U_SIO0 (.osc(osc), .A({1'b0,BA[0]}), .D(DB), .cs_n(cs_sio0_n), .rd_n(iord_n), .wr_n(iowr_n));
  periph_b  U_FDC  (.osc(osc), .A(BA[1:0]), .D(DB), .cs_n(cs_fdc_n),  .rd_n(iord_n), .wr_n(iowr_n));
  periph_b  U_PIC  (.osc(osc), .A({1'b0,BA[0]}), .D(DB), .cs_n(cs_pic_n),  .rd_n(iord_n), .wr_n(iowr_n));
  intr_ctl_b U_INTR (.osc(osc), .dbin(dbin), .inta_n(inta_n), .iowr_n(iowr_n), .cs_pic_n(cs_pic_n),
                     .a0(BA[0]), .frame_tick(frame_tick), .DB(DB), .intr(intr));
endmodule

`default_nettype wire
