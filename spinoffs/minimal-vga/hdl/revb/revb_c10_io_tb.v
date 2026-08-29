`timescale 1ns/1ps
`default_nettype none

// R5.I6 focused execution of C10's exact post-hardware I/O sequence against
// the revised card. This identifies the failing observable without waiting for
// the production ROM's multi-million-cycle memory tests.
module revb_c10_io_tb;
  parameter integer CLK_SOURCE = 1;
  reg clk=0, baud_master=0, reset_n=0;
  reg [15:0] A=0; reg [7:0] D_in=0;
  reg m1_n=1, iorq_n=1, rd_n=1, wr_n=1;
  wire [7:0] D_out; wire D_oe, pit0, pit1, pit2, baudclk, txd;
  wire [7:0] post; wire mode0,mode1;
  integer errors=0; reg [7:0] value;
  always #250 clk=~clk;
  always #101.725 baud_master=~baud_master;

  revb_io_card #(.USART_REAL(1),.PIT_REAL(1),.CLK_SOURCE(CLK_SOURCE)) dut(
    .clk(clk),.baud_master(baud_master),.reset_n(reset_n),.A(A),.D_in(D_in),
    .m1_n(m1_n),.iorq_n(iorq_n),.rd_n(rd_n),.wr_n(wr_n),.uart_rxd(1'b1),
    .uart_txd(txd),.D_out(D_out),.D_oe(D_oe),.MODE0(mode0),.MODE1(mode1),
    .PIT_OUT0(pit0),.PIT_OUT1(pit1),.PIT_OUT2(pit2),
    .BAUDCLK_OUT(baudclk),.POST_CODE(post));

  task idle; begin iorq_n=1;rd_n=1;wr_n=1;m1_n=1;A=0;D_in=0; end endtask
  task wr(input [7:0] p,input [7:0] d); begin
    @(negedge clk); A=p;D_in=d;iorq_n=0;wr_n=0;
    @(posedge clk);@(negedge clk);idle;#5;
  end endtask
  task rd(input [7:0] p,output [7:0] d); begin
    @(negedge clk);A=p;iorq_n=0;rd_n=0;#20;d=D_oe?D_out:8'hff;
    idle;@(negedge clk);
  end endtask
  task fail(input [255:0] why); begin errors=errors+1;$display("  FAIL %0s",why); end endtask

  initial begin
    idle;repeat(4)@(posedge clk);reset_n=1;repeat(4)@(posedge clk);
    // hardware_init PPI and initial D57 channel-0 setup relevant to C10.
    wr(8'h07,8'h82);wr(8'h07,8'h0F);
    wr(8'h1B,8'h1F);wr(8'h18,8'h32);

    // Exact quick-POST D57 latch/read.
    wr(8'h1B,8'h15);wr(8'h18,8'h04);wr(8'h1B,8'h00);rd(8'h18,value);
    $display("  C10 PIT read=%02h",value);
    if(value<1 || value>4) fail("C10 D57 count is not 1..4");

    // Exact canonical reset/mode/command and exact (not masked) status.
    wr(8'h09,0);wr(8'h09,0);wr(8'h09,0);wr(8'h09,8'h40);
    wr(8'h09,8'h4E);wr(8'h09,8'h35);rd(8'h09,value);
    $display("  C10 USART status=%02h",value);
    if(value!==8'h05) fail("C10 USART idle status is not 05h");

    // C10 POF release and full port-C readback.
    wr(8'h07,8'h0E);rd(8'h06,value);
    $display("  C10 PPI portC=%02h internal=%02h",value,dut.portc);
    if(value!==8'h00 || dut.portc!==8'h00) fail("C10 PC7/POF release failed");
    if(errors==0) $display("REVB-C10-IO: PASS source=%0d PIT/USART/POF exact sequence",CLK_SOURCE);
    else $display("REVB-C10-IO: FAIL errors=%0d",errors);
    $finish;
  end
endmodule

`default_nettype wire
