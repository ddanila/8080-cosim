// Minimum-tier bring-up twin: CPU + Memory + I/O(real 8251), NO Video card.
// Boots the T1.1 bring-up ROM and logs every CPU write to UART data port 0x08,
// so sim/revb_bringup_check.sh can diff that TX byte stream against cosim's.
// The real usart_8251 drives genuine TxRDY, so the ROM's per-byte TxRDY poll is
// exercised for real here (not just cosim's latch coincidence).
`default_nettype none
`timescale 1ns/100ps
module revb_bringup_tb;
    parameter rom_file     = "revb_bringup.hex";
    parameter tx_log       = "revb_tx.bin";
    parameter expect_bytes = 47;
    reg clk = 0, reset_n = 0;
    always #10 clk = ~clk;

    revb_backplane_top #(.rom_file(rom_file), .DECODE_MODE(1),
                         .VIDEO_PRESENT(0), .USART_REAL(1), .vw_limit(0))
        dut (.clk(clk), .reset_n(reset_n));

    integer fo, n = 0;
    reg prev = 1'b0;
    wire wr08 = (dut.iorq_n == 1'b0) && (dut.wr_n == 1'b0) && (dut.A[7:0] == 8'h08);
    initial fo = $fopen(tx_log, "wb");

    always @(posedge clk) if (reset_n) begin
        if (wr08 && !prev) begin
            $fwrite(fo, "%c", dut.D);
            n <= n + 1;
            if (n + 1 >= expect_bytes) begin
                $fclose(fo);
                $display("REVB-BRINGUP-TB: logged %0d TX bytes", n + 1);
                $finish;
            end
        end
        prev <= wr08;
    end

    initial begin
        #100 reset_n = 1;
        #200_000_000;                    // watchdog (~10M clks)
        $fclose(fo);
        $display("REVB-BRINGUP-TB: WATCHDOG at %0d bytes", n);
        $finish;
    end
endmodule
`default_nettype wire
