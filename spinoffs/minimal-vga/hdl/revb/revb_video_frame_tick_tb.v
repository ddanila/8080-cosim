// Exact U6 frame-divider simulation: one FRAME_TICK for every six VGA frames.
`default_nettype none
module revb_video_frame_tick_tb;
    localparam integer HT=16, HA=8, VT=7;
    reg dot_clk=0, clk=0, reset_n=0;
    wire hsync_n,vsync_n,active,pixel,wait_od_n,frame_tick,d_oe;
    wire [7:0] d_out;
    integer frames=0, ticks=0, last_tick_frame=-1, errors=0;

    revb_video_card_ttl #(
        .H_ACTIVE(HA),.H_FP(2),.H_SYNC(2),.H_BP(4),.H_TOTAL(HT),
        .V_ACTIVE(4),.V_FP(1),.V_SYNC(1),.V_BP(1),.V_TOTAL(VT),.vw_limit(0)) uut (
        .dot_clk(dot_clk),.clk(clk),.reset_n(reset_n),.A(16'h0000),.D_in(8'h00),
        .mreq_n(1'b1),.rd_n(1'b1),.wr_n(1'b1),.MODE0(1'b0),.MODE1(1'b0),
        .D_out(d_out),.D_oe(d_oe),.wait_od_n(wait_od_n),.hsync_n(hsync_n),
        .vsync_n(vsync_n),.active(active),.pixel(pixel),.frame_tick(frame_tick));
    always #1 dot_clk=~dot_clk;
    always #3 clk=~clk;

    reg prior_tick=0;
    always @(negedge dot_clk) if (reset_n) begin
        if (uut.hcount==0 && uut.vcount==0) frames=frames+1;
        if (frame_tick && !prior_tick) begin
            ticks=ticks+1;
            if (last_tick_frame>=0 && frames-last_tick_frame != 6) errors=errors+1;
            last_tick_frame=frames;
        end
        prior_tick=frame_tick;
    end

    initial begin
        #3 reset_n=1;
        wait(frames==19); #2;
        if (ticks != 3 || errors != 0) begin
            $display("REVB-VIDEO-FRAME-TICK: FAIL frames=%0d ticks=%0d errors=%0d",frames,ticks,errors);
        end else begin
            $display("REVB-VIDEO-FRAME-TICK: PASS 3 ticks / 18 frames, spacing=6");
        end
        $finish;
    end
endmodule
`default_nettype wire
