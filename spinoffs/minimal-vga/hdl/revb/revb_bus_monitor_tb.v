// Unit TB: bus-conflict monitor. Proves the assertion (a) stays quiet for legal
// one-hot(0) driver patterns and (b) fires when two cards drive at once.
`default_nettype none
`timescale 1ns/100ps
module revb_bus_monitor_tb;
    reg cpu_oe = 0, mem_oe = 0, video_oe = 0, io_oe = 0;
    reg rfsh_n = 1'b1;                        // 1 = not a refresh cycle
    reg [15:0] A = 16'h0000;
    wire conflict;
    integer errors = 0;

    revb_bus_monitor dut (.cpu_oe(cpu_oe), .mem_oe(mem_oe), .video_oe(video_oe),
                          .io_oe(io_oe), .rfsh_n(rfsh_n), .A(A), .conflict(conflict));

    initial begin
        // Legal patterns: no driver, and each single driver.
        #1; if (conflict) begin errors = errors + 1; $display("  FAIL none"); end
        cpu_oe = 1; #1; if (conflict) begin errors = errors + 1; $display("  FAIL cpu-only"); end
        cpu_oe = 0; mem_oe = 1; #1; if (conflict) begin errors = errors + 1; $display("  FAIL mem-only"); end
        mem_oe = 0; video_oe = 1; #1; if (conflict) begin errors = errors + 1; $display("  FAIL video-only"); end
        video_oe = 0; io_oe = 1; #1; if (conflict) begin errors = errors + 1; $display("  FAIL io-only"); end
        io_oe = 0; #1;

        // Injected conflict: mem + video drive together (a decode overlap).
        mem_oe = 1; video_oe = 1; A = 16'hD800; #1;
        if (!conflict) begin errors = errors + 1; $display("  FAIL monitor missed a 2-driver conflict"); end
        mem_oe = 0; video_oe = 0; #1;

        // Refresh-drive: any driver during a refresh cycle must be caught.
        rfsh_n = 1'b0; cpu_oe = 1; #1;
        if (!conflict) begin errors = errors + 1; $display("  FAIL monitor missed a refresh-drive"); end
        cpu_oe = 0; rfsh_n = 1'b1; #1;

        if (errors == 0) $display("REVB-BUS-MONITOR-TB: PASS");
        else             $display("REVB-BUS-MONITOR-TB: FAIL (%0d error(s))", errors);
        $finish;
    end
endmodule
`default_nettype wire
