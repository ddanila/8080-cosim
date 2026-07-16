// Phase C, step 3: run the boot on DISCRETE CHIP INSTANCES wired on a shared bus,
// not a monolithic behavioral memory. This is the merge taking its real form -- the
// memory map is decoded by an actual decode-PROM module (D6 РТ4), ROM and RAM are
// separate modules that drive/latch the shared data bus, the banking mode comes from
// the 8255#0 (D26) Port-C register, and the I/O ports are routed by a second decode
// PROM (D2 РТ4) to eight separate peripheral chips (PIC/PPI×2/PIT×3/USART/FDC) on the
// shared bus. Peripherals use cosim's latch model (IN = last OUT) -> byte-identical.
//
// Decomposition vs juku_sim_tb.v (monolithic): same vm80a, same cross-validation
// target. Its PROM decode is a historical behavioral oracle, not physical D6 burn
// data. The validated `.038` table and joined pins 11/12 live in juku_top; see
// docs/d6-physical-decode.md.
//
// Run (from repo root, needs hdl/sim/ekta37.hex -- see juku_sim_tb.v header):
//   iverilog -g2012 -o /tmp/jchips hdl/vendor/vm80a.v hdl/sim/juku_chips_tb.v
//   vvp /tmp/jchips                 # -> 6000 video writes, byte-identical to cosim
//   vvp /tmp/jchips +maxvram=43000  # -> full boot banner
`timescale 1ns/100ps

// --- Historical boot-map oracle; not the physical D6 `.038` implementation. ---------
module mem_decode_prom(
  input  [15:0] a,
  input  [1:0]  mode,
  output reg    rom_sel,      // ROM overlay serves this address
  output reg    ram_sel,      // RAM serves this address
  output reg [13:0] rom_idx); // ROM offset when rom_sel (banking folds 0xD800->0x1800)
  always @(*) begin
    rom_sel = 1'b0; ram_sel = 1'b0; rom_idx = 14'd0;
    case (mode)
      2'd0: if (a <= 16'h3FFF) begin rom_sel=1; rom_idx=a[13:0]; end else ram_sel=1;
      2'd1: if (a >= 16'hD800) begin rom_sel=1; rom_idx=16'h1800+(a-16'hD800); end else ram_sel=1;
      2'd2: if (a >= 16'hD800) begin rom_sel=1; rom_idx=16'h1800+(a-16'hD800); end else ram_sel=1;
      default: ram_sel=1;     // mode 3: all RAM
    endcase
  end
endmodule

// --- EPROM (ekta37), abstracts the D15-D22 array. Drives the bus when read+selected. -
module eprom(input [13:0] idx, input oe, inout [7:0] d);
  reg [7:0] cells [0:16383];
  initial $readmemh("hdl/sim/ekta37.hex", cells);
  assign d = oe ? cells[idx] : 8'hzz;
endmodule

// --- DRAM 64Kx8 (abstracts the К565РУ5 array). Drives on read, latches on write. -----
module dram(input [15:0] a, input [7:0] din, input we, input oe, inout [7:0] d);
  reg [7:0] cells [0:65535];
  integer i; initial for (i=0;i<65536;i=i+1) cells[i]=8'h00;
  always @(posedge we) cells[a] = din;
  assign d = oe ? cells[a] : 8'hzz;
  // expose for VRAM dump
  task dump(input integer fd, input integer n);
    integer k; begin for (k=0;k<n;k=k+1) $fwrite(fd,"%c",cells[16'hD800+k]); end
  endtask
endmodule

// --- D2 К556РТ4 I/O-decode PROM: port -> one of 8 chip-selects (4-port blocks).
//     Contents = the recovered I/O map (0x00 PIC, 0x04 PPI0, 0x08 USART, 0x0C PPI1,
//     0x10/0x14/0x18 PIT0-2, 0x1C FDC) -- matches MAME io_map / hardware-map.md. ------
module io_decode_prom(input [7:0] port, output reg [7:0] cs);
  always @(*) begin
    cs = 8'b0;
    if (port[7:5] == 3'b000) cs[port[4:2]] = 1'b1;   // ports 0x00..0x1F -> block port[4:2]
  end
endmodule

// --- Generic peripheral: 4 register ports, IN returns last OUT (cosim's latch model).
//     Models 8259/8251/8255#1/8253x3/FDC behaviorally-equivalent for the boot. --------
module latched_periph(input [1:0] rs, input cs, input [7:0] din,
                      input iord, input iowr, inout [7:0] d);
  reg [7:0] regs [0:3];
  integer i; initial for (i=0;i<4;i=i+1) regs[i]=8'h00;
  assign d = (cs & iord) ? regs[rs] : 8'hzz;
  always @(posedge iowr) if (cs) regs[rs] = din;
endmodule

// --- 8255#0 (D26): like latched_periph + Port C (rs=2) / control (rs=3) drive banking.
module ppi8255_bank(input [1:0] rs, input cs, input [7:0] din,
                    input iord, input iowr, inout [7:0] d, output reg [1:0] mode);
  reg [7:0] regs [0:3]; reg [7:0] portc; reg [2:0] pb;
  integer i; initial begin for (i=0;i<4;i=i+1) regs[i]=8'h00; portc=0; mode=0; end
  assign d = (cs & iord) ? regs[rs] : 8'hzz;
  always @(posedge iowr) if (cs) begin
    regs[rs] = din;
    if (rs == 2'd2) begin portc = din; mode = din[1:0]; end              // Port C (0x06)
    else if (rs == 2'd3) begin                                            // control (0x07)
      if (din[7]) begin portc = 0; mode = 0; end                          // mode-set cmd
      else begin pb = (din>>1)&3'd7; if (din[0]) portc[pb]=1; else portc[pb]=0; mode=portc[1:0]; end
    end
  end
endmodule

// ============================ top / testbench ===============================
module juku_chips_tb();
  tri1 [7:0] d;
  wire [15:0] a;
  reg  clk=0, f1=0, f2=0, reset=1, ready=1, hold=0, intr=0;
  wire inte, hlda, waitr, sync, dbin, wr_n;
  reg  [7:0] status = 0;
  integer mcyc=0, vram_writes=0, max_vram=6000;
  reg vram_seen=0;

  // clock + 2-phase generator
  initial forever begin
    f1=1; clk=0; #10; clk=1; #10;
    f1=0; f2=1; clk=0; #10; clk=1; #10;
    f2=0;
  end

  // status-byte latch (on a clk edge inside the 8080 SYNC window)
  reg sync_q=0;
  always @(posedge clk) begin
    if (sync && !sync_q) begin status <= d; mcyc <= mcyc+1; end
    sync_q <= sync;
  end

  // bus-cycle strobes decoded from the latched 8080 status byte
  wire mem_rd = dbin  & ~status[6];        // memory read  (status[6]=INP)
  wire io_rd  = dbin  &  status[6];        // I/O read
  wire is_io_wr = status[4];               // status[4]=OUT -> I/O write vs memory write

  // memory decode + chips on the shared bus
  reg  ram_we=0, io_wr_pulse=0;             // write pulses driven from the /WR handler
  wire [1:0] mode; wire rom_sel, ram_sel; wire [13:0] rom_idx;
  mem_decode_prom D6(.a(a), .mode(mode), .rom_sel(rom_sel), .ram_sel(ram_sel), .rom_idx(rom_idx));

  wire rom_oe = mem_rd & rom_sel;
  wire ram_oe = mem_rd & ram_sel;
  eprom     EP (.idx(rom_idx), .oe(rom_oe), .d(d));
  dram      RU (.a(a), .din(d), .we(ram_we), .oe(ram_oe), .d(d));

  // I/O: D2 decode PROM -> per-chip selects; each peripheral on the shared bus.
  wire [7:0] iocs;
  io_decode_prom D2 (.port(a[7:0]), .cs(iocs));
  ppi8255_bank   D26(.rs(a[1:0]), .cs(iocs[1]), .din(d), .iord(io_rd), .iowr(io_wr_pulse), .d(d), .mode(mode)); // 0x04 +banking
  latched_periph D10(.rs(a[1:0]), .cs(iocs[0]), .din(d), .iord(io_rd), .iowr(io_wr_pulse), .d(d)); // 0x00 PIC 8259
  latched_periph D11(.rs(a[1:0]), .cs(iocs[2]), .din(d), .iord(io_rd), .iowr(io_wr_pulse), .d(d)); // 0x08 USART 8251
  latched_periph D27(.rs(a[1:0]), .cs(iocs[3]), .din(d), .iord(io_rd), .iowr(io_wr_pulse), .d(d)); // 0x0C PPI1 8255
  latched_periph D54(.rs(a[1:0]), .cs(iocs[4]), .din(d), .iord(io_rd), .iowr(io_wr_pulse), .d(d)); // 0x10 PIT0 8253
  latched_periph D55(.rs(a[1:0]), .cs(iocs[5]), .din(d), .iord(io_rd), .iowr(io_wr_pulse), .d(d)); // 0x14 PIT1 8253
  latched_periph D57(.rs(a[1:0]), .cs(iocs[6]), .din(d), .iord(io_rd), .iowr(io_wr_pulse), .d(d)); // 0x18 PIT2 8253
  latched_periph FDC(.rs(a[1:0]), .cs(iocs[7]), .din(d), .iord(io_rd), .iowr(io_wr_pulse), .d(d)); // 0x1C WD1793

  // Write pulses (data valid at /WR). Paging is a read-source selection;
  // /MEMW writes the underlying DRAM even while ROM is visible.
  always @(negedge wr_n) begin
    if (is_io_wr) begin
      io_wr_pulse = 1; #1 io_wr_pulse = 0;            // pulse the I/O latch/banking
    end else begin
      ram_we = 1; #1 ram_we = 0;
      if (a >= 16'hD800) begin
        vram_writes = vram_writes + 1;
        if (!vram_seen) begin vram_seen=1;
          $display("[VRAM] first video write @0x%04h=0x%02h mode=%0d mcyc=%0d", a, d, mode, mcyc); end
        if (vram_writes == max_vram) begin
          $display("[VRAM] %0d writes (mcyc=%0d) -- dump", vram_writes, mcyc); dump_vram; $finish;
        end
      end
    end
  end

  integer fd;
  task dump_vram; begin
    fd=$fopen("hdl/sim/vram_chips.bin","wb"); RU.dump(fd, 40*241); $fclose(fd);
    $display("[SIM] dumped VRAM -> hdl/sim/vram_chips.bin");
  end endtask

  initial begin
    if ($value$plusargs("maxvram=%d", max_vram)) ;
    reset=1; #2000 reset=0;
  end
  initial begin #1000000000;
    $display("[SIM] time cap mcyc=%0d vram_writes=%0d mode=%0d", mcyc, vram_writes, mode);
    dump_vram; $finish;
  end

  vm80a cpu (.pin_clk(clk), .pin_f1(f1), .pin_f2(f2), .pin_d(d), .pin_a(a),
             .pin_reset(reset), .pin_hold(hold), .pin_hlda(hlda), .pin_ready(ready),
             .pin_wait(waitr), .pin_int(intr), .pin_inte(inte), .pin_sync(sync),
             .pin_dbin(dbin), .pin_wr_n(wr_n));
endmodule
