`timescale 1ns/100ps
`default_nettype none

// Execute a full Jukuravi ROM with clock-faithful 8253 Mode-0 loads.  Stop at
// the first local-USART setup write, immediately after the nonfatal peripheral
// diagnostics, and report whether any D55 count was latched before its real
// counting element received a source clock.
module jukuravi_d55_clock_audit_tb;
  reg osc = 0;
  reg active = 0;
  integer failures = 0;
  integer d55_reads = 0;
  integer d55_latches = 0;
  integer unclocked_latches = 0;
  integer expect_unclocked = 0;
  integer expected_predicates = 0;
  integer fault = 0;
  reg [7:0] expected_e = 0;
  reg finishing = 0;

  juku_top #(.PIT_CLOCKED_MODE0_LOAD(1)) dut
           (.clk(1'b0), .reset_n(1'b1), .osc(osc),
            .kbd_en(1'b0), .kbd_pressed(1'b0), .kbd_shift(1'b0),
            .kbd_kcol(4'b0), .kbd_kbit(3'b0), .frame_tick(1'b0));

  wire [15:0] pc = dut.U_CPU.u.core.r16_pc;
  wire [7:0] architectural_e = dut.U_CPU.u.core.xchg_dh
      ? dut.U_CPU.u.core.r16_de[7:0] : dut.U_CPU.u.core.r16_hl[7:0];

  task fail(input [1023:0] message); begin
    $display("JUKURAVI-D55-CLOCK-AUDIT: FAIL %0s", message);
    failures = failures + 1;
  end endtask

  initial begin
    if (!$value$plusargs("expected_e=%h", expected_e))
      fail("missing +expected_e");
    if (!$value$plusargs("expect_unclocked=%d", expect_unclocked))
      fail("missing +expect_unclocked");
    if (!$value$plusargs("expected_predicates=%d", expected_predicates))
      fail("missing +expected_predicates");
    if (!$value$plusargs("fault=%d", fault)) fault = 0;
    case (fault)
      2: force dut.pit_hchain = 1'b0;  // good D55, bad upstream D54 OUT0 path
      3: force dut.d56_q2_n = 1'b0;    // good D55, bad D56 channel-1/2 clock path
      4: force dut.cs_pit1_n = 1'b1;   // good D55, bad D9/local chip-select path
    endcase
    force dut.ready = 1'b1;
    force dut.reset_sys = 1'b1;
    #25000;
    force dut.reset_sys = 1'b0;
    active = 1;
  end

  initial forever begin
    force dut.phi1 = 1'b1; force dut.phi2 = 1'b0; osc = 0; #125; osc = 1; #125;
    force dut.phi1 = 1'b0; force dut.phi2 = 1'b1; osc = 0; #125; osc = 1; #125;
    force dut.phi2 = 1'b0;
  end

  initial forever begin
    force dut.osc_clk = 1'b0; force dut.xtal16m_w = 1'b0; #31.25;
    force dut.osc_clk = 1'b1; force dut.xtal16m_w = 1'b1; #31.25;
  end

  always @(negedge dut.iowr_n) if (active && !finishing) begin
    #2;
    if (dut.BA[7:0] == 8'h17
        && (dut.DB == 8'h00 || dut.DB == 8'h40 || dut.DB == 8'h80)) begin
      d55_latches = d55_latches + 1;
      case (dut.DB[7:6])
        2'd0: if (dut.U_PIT1.load_pending[0]) unclocked_latches = unclocked_latches + 1;
        2'd1: if (dut.U_PIT1.load_pending[1]) unclocked_latches = unclocked_latches + 1;
        2'd2: if (dut.U_PIT1.load_pending[2]) unclocked_latches = unclocked_latches + 1;
      endcase
      // A direct D55 channel-2 DB7 fault proves the corrected predicate still
      // detects a package/data-output failure after its clock requirement is met.
      if (fault == 1 && dut.DB == 8'h80)
        dut.U_PIT1.output_latch[2][15] = 1'b0;
    end

    // Port 09h is the USART control port.  Its first write follows the complete
    // PIC/PPI/PIT block in T31 and T34.
    if (dut.BA[7:0] == 8'h09) begin
      finishing = 1;
      $display("JUKURAVI-D55-CLOCK-AUDIT: STATE pc=%04h e=%02h expected=%02h reads=%0d latches=%0d unclocked=%0d",
               pc, architectural_e, expected_e, d55_reads, d55_latches,
               unclocked_latches);
      if (architectural_e !== expected_e) fail("unexpected peripheral bitmap");
      if (d55_reads != expected_predicates || d55_latches != expected_predicates)
        fail("D55 predicate coverage");
      if (expect_unclocked && unclocked_latches == 0)
        fail("legacy sequence unexpectedly clocked every D55 load");
      if (!expect_unclocked && unclocked_latches != 0)
        fail("corrected sequence latched an unclocked D55 load");
      if (failures == 0)
        $display("JUKURAVI-D55-CLOCK-AUDIT: PASS pc=%04h e=%02h reads=%0d latches=%0d unclocked=%0d",
                 pc, architectural_e, d55_reads, d55_latches, unclocked_latches);
      #20 $finish;
    end
  end

  always @(negedge dut.iord_n) if (active && !finishing) begin
    #1;
    if (dut.BA[7:0] >= 8'h14 && dut.BA[7:0] <= 8'h16)
      d55_reads = d55_reads + 1;
  end

  initial begin
    #700000000;
    fail("time cap before post-PIT USART setup");
    $finish;
  end
endmodule

`default_nettype wire
