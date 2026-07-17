// VJUGA rev B — bus-conflict monitor (simulation assertion).
// The backplane data bus must have at most ONE driver at any instant. This
// checker watches the four card output-enables and raises `conflict` (and prints
// a distinctive REVB-BUS-CONFLICT line) if two or more assert together — the
// class of fault byte-identity cannot see (a decode overlap can still yield the
// right bytes in sim yet short two outputs together on the bench). It is a passive
// observer: it drives nothing on the bus.
`default_nettype none
module revb_bus_monitor (
    input  wire        cpu_oe, mem_oe, video_oe, io_oe,
    input  wire [15:0] A,
    output reg         conflict
);
    wire [2:0] drivers = cpu_oe + mem_oe + video_oe + io_oe;
    initial conflict = 1'b0;
    always @(*) begin
        if (drivers > 3'd1) begin
            conflict = 1'b1;
            $display("REVB-BUS-CONFLICT: %0d drivers (cpu=%b mem=%b video=%b io=%b) @A=%04h t=%0t",
                     drivers, cpu_oe, mem_oe, video_oe, io_oe, A, $time);
        end
    end
endmodule
`default_nettype wire
