// VJUGA rev B — CPU card.
// Z80 (tv80) + bus-buffer behavior. Sole bus driver during writes. See
// spinoffs/minimal-vga/docs/rev-b-bus-contract.md. Memory technology lives on
// other cards (SRAM), so no DRAM/wait sequencer here.
`default_nettype none
module revb_cpu_card (
    input  wire        clk,
    input  wire        reset_n,
    input  wire        wait_n,       // extension E1 (backplane pulls high; video may assert in B2)
    input  wire        int_n,        // base pin 22 (open-drain, pulled high)
    input  wire        nmi_n,        // extension E2
    input  wire        busrq_n,      // extension E3
    input  wire [7:0]  D_in,         // resolved backplane data bus
    output wire [7:0]  D_out,        // data this card drives
    output wire        D_oe,         // this card is driving the bus
    output wire [15:0] A,
    output wire        m1_n, mreq_n, iorq_n, rd_n, wr_n, rfsh_n, halt_n, busak_n
);
    tv80s #(.Mode(0), .T2Write(0), .IOWait(1)) U_CPU (
        .reset_n(reset_n), .clk(clk), .wait_n(wait_n),
        .int_n(int_n), .nmi_n(nmi_n), .busrq_n(busrq_n),
        .m1_n(m1_n), .mreq_n(mreq_n), .iorq_n(iorq_n), .rd_n(rd_n), .wr_n(wr_n),
        .rfsh_n(rfsh_n), .halt_n(halt_n), .busak_n(busak_n),
        .A(A), .di(D_in), .dout(D_out));

    // CPU sources the data bus only on a memory or I/O write cycle.
    assign D_oe = (~wr_n) & ((~mreq_n) | (~iorq_n));
endmodule
`default_nettype wire
