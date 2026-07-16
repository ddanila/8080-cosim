// Phase C, step 2: boot the real Juku BIOS (ekta37) on the die-accurate vm80a
// (КР580ВМ80А) in Verilog. The "system" here is a behavioral memory/banking/I-O
// model that faithfully mirrors the working cosim emulator (cosim/trace.c) -- same
// 4-mode overlay, same Port-C banking, same IN=output-latch behavior. This proves
// the real CPU core executes the real BIOS through the Juku decode in our toolchain;
// it's the bridge to the full chip-by-chip structural sim. Cross-validated vs cosim.
//
// 8080 bus protocol: a STATUS byte is emitted on D during SYNC. Bits we use:
//   D7=MEMR (memory read), D6=INP (I/O read), D4=OUT (I/O write).
//
// ekta37.hex is ROM-derived (kept out of git). Generate it locally from the ROM:
//   python3 -c "open('hdl/sim/ekta37.hex','w').write('\n'.join('%02x'%b for b in \
//     open('/path/to/ekta37.bin','rb').read()))"
// Run (from repo root):
//   iverilog -g2012 -o /tmp/jsim hdl/vendor/vm80a.v hdl/sim/juku_sim_tb.v
//   vvp /tmp/jsim                 # stops after 6000 video writes (the 0x55 RAM test)
//   vvp /tmp/jsim +maxvram=43000  # runs to the full boot banner (slow: die-replica)
// Cross-validated: VRAM is byte-identical to cosim at the same video-write count.
`timescale 1ns/100ps

module juku_sim_tb();
  tri1 [7:0] d;
  wire [15:0] a;
  reg  clk=0, f1=0, f2=0, reset=1, ready=1, hold=0, intr=0;
  wire inte, hlda, waitr, sync, dbin, wr_n;

  reg  [7:0] rom [0:16383];           // ekta37
  reg  [7:0] ram [0:65535];
  reg  [7:0] out_last [0:255];
  reg  [1:0] mode = 0;                 // memory view (reset=0)
  reg  [7:0] portc = 0;
  reg  [7:0] status = 0;               // latched 8080 status byte
  integer i;
  integer mcyc = 0, banks = 0, vram_writes = 0;
  integer max_vram = 6000;             // stop after this many video writes (+maxvram=N)
  reg vram_seen = 0;

  // --- clock + 2-phase generator ---
  initial forever begin
    f1=1; clk=0; #10; clk=1; #10;
    f1=0; f2=1; clk=0; #10; clk=1; #10;
    f2=0;
  end

  // --- memory read with the 4-mode overlay (mirrors cosim overlay()/rd_byte()) ---
  function [7:0] mem_read(input [15:0] addr);
    begin
      case (mode)
        2'd0: mem_read = (addr <= 16'h3FFF) ? rom[addr[13:0]] : ram[addr];
        2'd1: mem_read = (addr >= 16'hD800) ? rom[(16'h1800 + (addr-16'hD800))] : ram[addr];
        2'd2: mem_read = (addr >= 16'hD800) ? rom[(16'h1800 + (addr-16'hD800))] : ram[addr];
        default: mem_read = ram[addr];   // mode 3: all RAM
      endcase
    end
  endfunction

  function write_blocked(input [15:0] addr);
    begin
      write_blocked = (mode == 2'd1 || mode == 2'd2) && addr >= 16'hD800;
    end
  endfunction

  // read data onto the bus during DBIN (memory or I/O per latched status)
  wire [7:0] rdata = status[6] ? out_last[a[7:0]] : mem_read(a);
  assign d = dbin ? rdata : 8'hzz;


  // Capture the 8080 status byte. It is driven on D *while sync is high* (T1); we
  // must NOT sample at posedge sync -- sync and D update on the same f2 edge, so a
  // posedge-sync read gets the stale (pre-drive) bus. Sample on a clk edge while
  // sync is high instead (D is stable there), latched once per machine cycle.
  reg sync_q = 0;
  always @(posedge clk) begin
    if (sync && !sync_q) begin        // first clk inside this sync window
      status <= d;
      mcyc   <= mcyc + 1;
    end
    sync_q <= sync;
  end

  task set_mode(input [1:0] m);
    begin
      if (m !== mode) begin
        banks = banks + 1;
        $display("[BANK] mode %0d -> %0d  (portC=0x%02h)  @mcyc=%0d", mode, m, portc, mcyc);
        mode = m;
      end
    end
  endtask

  // bus write: I/O (OUT) or memory, decoded from the status byte
  reg [2:0] pbit;
  always @(negedge wr_n) begin
    if (status[4]) begin                 // OUT -> I/O write
      out_last[a[7:0]] = d;
      if (a[7:0] == 8'h06) begin          // 8255#0 Port C direct
        portc = d; set_mode(d[1:0]);
      end else if (a[7:0] == 8'h07) begin // 8255 control port
        if (d[7]) begin portc = 0; set_mode(2'd0); end
        else begin                        // bit set/reset on Port C
          pbit = (d >> 1) & 3'd7;
          if (d[0]) portc[pbit] = 1'b1; else portc[pbit] = 1'b0;
          set_mode(portc[1:0]);
        end
      end
    end else if (!write_blocked(a)) begin    // low ROM permits page-zero write-behind
      ram[a] = d;
      if (a >= 16'hD800) begin
        vram_writes = vram_writes + 1;
        if (!vram_seen) begin
          vram_seen = 1;
          $display("[VRAM] first write to video RAM @0x%04h = 0x%02h  (mode=%0d, mcyc=%0d)", a, d, mode, mcyc);
        end
        if (vram_writes == max_vram) begin   // captured enough -> dump & stop
          $display("[VRAM] %0d video writes done (mcyc=%0d, banks=%0d) -- dumping", vram_writes, mcyc, banks);
          dump_vram; $finish;
        end
      end
    end
  end

  initial begin
    for (i=0;i<65536;i=i+1) ram[i]=8'h00;
    for (i=0;i<256;i=i+1)   out_last[i]=8'h00;
    $readmemh("hdl/sim/ekta37.hex", rom);
    if ($value$plusargs("maxvram=%d", max_vram)) ;
    reset=1; #2000 reset=0;
  end

  integer fd, k;
  task dump_vram;
    begin
      fd = $fopen("hdl/sim/vram_hdl.bin", "wb");
      for (k=0; k<40*241; k=k+1) $fwrite(fd, "%c", ram[16'hD800 + k]);
      $fclose(fd);
      $display("[SIM] dumped VRAM -> hdl/sim/vram_hdl.bin");
    end
  endtask

  // overall time cap (backstop if the video-write threshold is never reached)
  initial begin
    #1000000000;
    $display("[SIM] time cap: machine_cycles=%0d  bank_switches=%0d  mode=%0d  vram_writes=%0d", mcyc, banks, mode, vram_writes);
    dump_vram; $finish;
  end

  vm80a cpu (.pin_clk(clk), .pin_f1(f1), .pin_f2(f2), .pin_d(d), .pin_a(a),
             .pin_reset(reset), .pin_hold(hold), .pin_hlda(hlda), .pin_ready(ready),
             .pin_wait(waitr), .pin_int(intr), .pin_inte(inte), .pin_sync(sync),
             .pin_dbin(dbin), .pin_wr_n(wr_n));
endmodule
