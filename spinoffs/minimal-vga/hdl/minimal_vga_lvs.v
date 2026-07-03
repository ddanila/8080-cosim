`default_nettype none

module z80_cpu_lvs(
  output wire [15:0] A,
  inout  wire [7:0] D,
  output wire MREQ_N, IORQ_N, RD_N, WR_N, M1_N, RFSH_N,
  input  wire WAIT_N, INT_N, NMI_N, RESET_N, CLK
);
endmodule

module z80_native_adapter_lvs(
  input wire [15:0] ZA,
  inout wire [7:0] ZD,
  input wire MREQ_N, IORQ_N, RD_N, WR_N, M1_N, RFSH_N,
  output wire [15:0] MA,
  inout wire [7:0] MD,
  output wire MEM_RD_N, MEM_WR_N, IO_RD_N, IO_WR_N, RFSH_OBS_N
);
endmodule

module rom_lvs(
  input wire [14:0] A,
  inout wire [7:0] D,
  input wire CE_N, OE_N
);
endmodule

module dram4164_bank_lvs(
  input wire [7:0] MA,
  inout wire [7:0] D,
  input wire RAS_N, CAS_N, WE_N
);
endmodule

module refresh_ctl_lvs(
  input wire CLK, RESET_N, MEM_RD_N, MEM_WR_N, RFSH_OBS_N,
  output wire RAS_N, CAS_N, WE_N,
  output wire [7:0] REFRESH_ROW
);
endmodule

module keyboard_lvs(
  inout wire [7:0] D,
  input wire IO_RD_N, IO_WR_N,
  input wire [3:0] COL,
  output wire [2:0] ROW,
  output wire GS_N
);
endmodule

module vga_timing_lvs(
  output wire HSYNC_N, VSYNC_N, BLANK_N,
  input wire PIXEL
);
endmodule

module video_fetch_lvs(
  input wire [15:0] A,
  inout wire [7:0] D,
  input wire CAS_N, BLANK_N,
  output wire PIXEL
);
endmodule

module minimal_vga_lvs_top();
  wire [15:0] za, ma;
  wire [7:0] zd, md;
  wire mreq_n, iorq_n, rd_n, wr_n, m1_n, rfsh_n;
  wire mem_rd_n, mem_wr_n, io_rd_n, io_wr_n, rfsh_obs_n;
  wire wait_n, int_n, nmi_n, reset_n, clk;
  wire rom_ce_n, rom_oe_n;
  wire ras_n, cas_n, dram_we_n;
  wire [7:0] refresh_row;
  wire [3:0] kcol;
  wire [2:0] krow;
  wire kgs_n, hsync_n, vsync_n, blank_n, pixel;

  z80_cpu_lvs U_CPU(
    .A(za), .D(zd),
    .MREQ_N(mreq_n), .IORQ_N(iorq_n), .RD_N(rd_n), .WR_N(wr_n), .M1_N(m1_n), .RFSH_N(rfsh_n),
    .WAIT_N(wait_n), .INT_N(int_n), .NMI_N(nmi_n), .RESET_N(reset_n), .CLK(clk)
  );

  z80_native_adapter_lvs U_ADAPT(
    .ZA(za), .ZD(zd),
    .MREQ_N(mreq_n), .IORQ_N(iorq_n), .RD_N(rd_n), .WR_N(wr_n), .M1_N(m1_n), .RFSH_N(rfsh_n),
    .MA(ma), .MD(md),
    .MEM_RD_N(mem_rd_n), .MEM_WR_N(mem_wr_n), .IO_RD_N(io_rd_n), .IO_WR_N(io_wr_n), .RFSH_OBS_N(rfsh_obs_n)
  );

  rom_lvs U_ROM(
    .A(ma[14:0]), .D(md), .CE_N(rom_ce_n), .OE_N(mem_rd_n)
  );

  dram4164_bank_lvs U_DRAM(
    .MA(ma[7:0]), .D(md), .RAS_N(ras_n), .CAS_N(cas_n), .WE_N(dram_we_n)
  );

  refresh_ctl_lvs U_REFRESH(
    .CLK(clk), .RESET_N(reset_n), .MEM_RD_N(mem_rd_n), .MEM_WR_N(mem_wr_n), .RFSH_OBS_N(rfsh_obs_n),
    .RAS_N(ras_n), .CAS_N(cas_n), .WE_N(dram_we_n), .REFRESH_ROW(refresh_row)
  );

  keyboard_lvs U_KBD(
    .D(md), .IO_RD_N(io_rd_n), .IO_WR_N(io_wr_n), .COL(kcol), .ROW(krow), .GS_N(kgs_n)
  );

  vga_timing_lvs U_VGA(
    .HSYNC_N(hsync_n), .VSYNC_N(vsync_n), .BLANK_N(blank_n), .PIXEL(pixel)
  );

  video_fetch_lvs U_VIDEO(
    .A(ma), .D(md), .CAS_N(cas_n), .BLANK_N(blank_n), .PIXEL(pixel)
  );
endmodule

`default_nettype wire
